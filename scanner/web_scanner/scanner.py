# -*- coding: utf-8 -*-
# Created by restran on 2016/10/13

"""
使用方法

默认是自动识别，如果没有识别出，则使用全部字典
python scanner.py -u http://www.github.com

指定使用什么字典去扫描
python scanner.py -u http://www.github.com -w 10 -t 3 -d php -d dir
"""

# TODO 添加对 Cookie 的支持

from __future__ import unicode_literals, absolute_import
from tornado.escape import to_unicode
import os
import sys
import time
from collections import deque
import logging
import traceback
from tornado.httpclient import HTTPRequest, HTTPError
from future.moves.urllib.parse import urlunparse, urlparse
from tornado import gen, ioloop
from tornado.httpclient import AsyncHTTPClient
from optparse import OptionParser
import validators

# 把项目的目录加入的环境变量中，这样才可以导入 common.base
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common.base import read_dict

logger = logging.getLogger(__name__)

# 最大并发数量
ASYNC_HTTP_MAX_CLIENTS = 200

try:
    # curl_httpclient is faster than simple_httpclient
    AsyncHTTPClient.configure(
        'tornado.curl_httpclient.CurlAsyncHTTPClient',
        max_clients=ASYNC_HTTP_MAX_CLIENTS)
except ImportError:
    AsyncHTTPClient.configure(
        'tornado.simple_httpclient.AsyncHTTPClient',
        max_clients=ASYNC_HTTP_MAX_CLIENTS)

parser = OptionParser()
parser.add_option("-u", "--url", dest="target_url", type="string",
                  help="target url, e.g. http://127.0.0.1:8080/index.php")
parser.add_option("-w", "--worker", dest="worker_num", type="int",
                  default=10, help="max worker num")
parser.add_option("-t", "--timeout", dest="timeout", type="int",
                  default=3, help="timeout in seconds")
parser.add_option("-v", dest="verbose", action="store_true",
                  default=False, help="verbose log")
parser.add_option("-d", "--dict", dest="scan_dict", default=None,
                  action="append",
                  choices=['dir', 'php', 'jsp', 'asp', 'aspx', 'mdb'],
                  help="which dict to scan, only allow dir, php, jsp, asp, aspx, mdb")

parser.add_option("-s", "--status", dest="status", default=None,
                  action="append", choices=["200", "301", "302", "304", "401", "403"],
                  help="which status to catch, only allow 200, 301, 302, 304, 401, 403")

# 字典列表
DICT_LIST = ['dir', 'php', 'jsp', 'asp', 'aspx', 'mdb']


class AsyncHTTPExecutor(object):
    """
    异步HTTP请求，可以并发访问
    """

    def __init__(self, base_url, fn_on_queue_empty, first_queue,
                 max_workers=10, timeout=3, verbose=False):
        self.base_url = base_url.rstrip('/')
        self.fn_on_queue_empty = fn_on_queue_empty
        self.task_queue = deque()
        self.task_queue.extend(first_queue)
        self.timeout = timeout
        self.max_workers = max_workers
        self.verbose = verbose
        self.count = 0
        self.start_time = None
        self.last_time = None

    def get_next_task(self):
        try:
            item, method = self.task_queue.popleft()
        except IndexError:
            item, method = self.fn_on_queue_empty(self.task_queue)
        return item, method

    def make_url(self, item):
        if item.startswith('/'):
            url = '%s%s' % (self.base_url, item)
        else:
            url = '%s/%s' % (self.base_url, item)
        return url

    @gen.coroutine
    def do_request(self, item, method, fn_on_response):
        self.count += 1
        current_time = time.time()
        # 每隔10秒输出一次
        if current_time - self.last_time > 10:
            self.last_time = current_time
            speed = self.count / (current_time - self.start_time)
            past_time = current_time - self.start_time
            logger.info('items, speed, time: %s, %.1f/s, %.1fs' % (self.count, speed, past_time))
        url = ''

        item = item.decode('utf-8')
        try:
            url = self.make_url(item)
            body = '' if method == 'POST' else None
            response = yield AsyncHTTPClient().fetch(
                HTTPRequest(url=url,
                            method=method,
                            body=body,
                            decompress_response=True,
                            connect_timeout=self.timeout,
                            request_timeout=self.timeout,
                            follow_redirects=False))
            fn_on_response(url, item, method, response, self.task_queue)
        except HTTPError as e:
            if hasattr(e, 'response') and e.response:
                fn_on_response(url, item, method, e.response, self.task_queue)
            else:
                logger.error('Exception: %s %s %s' % (e, method, item))
        except Exception as e:
            logger.error('Exception: %s %s %s' % (e, method, item))

    @gen.coroutine
    def fetch_url(self, fn_on_response):
        item, method = self.get_next_task()
        while item is not None:
            yield self.do_request(item, method, fn_on_response)
            item, method = self.get_next_task()

    @gen.coroutine
    def run(self, fn_on_response, *args, **kwargs):
        logger.info('executor start')
        self.start_time = time.time()
        self.last_time = self.start_time
        # Start workers, then wait for the work queue to be empty.
        # 会卡在这里，等待所有的 worker 都结束
        yield [self.fetch_url(fn_on_response) for _ in range(self.max_workers)]
        end_time = time.time()
        logger.info('total count: %s' % self.count)
        logger.info('executor done, %.3fs' % (end_time - self.start_time))


class WebScanner(object):
    def __init__(self, url, max_worker=10, timeout=3,
                 scan_dict=None, verbose=False, status=None):
        self.site_lang = ''
        self.raw_base_url = url
        self.base_url = url
        self.max_worker = max_worker
        self.timeout = timeout
        self.scan_dict = scan_dict
        self.verbose = verbose
        self.first_item = ''
        self.dict_data = {}
        self.first_queue = []
        self.found_items = {}
        if status is None or len(status) == 0:
            self.status = [200, 301, 302, 304, 401, 403]
        else:
            self.status = [int(t) for t in status]

    def on_queue_empty(self, queue, max_num=100):
        for t in range(max_num):
            for d in self.dict_data.keys():
                dict_d = self.dict_data[d]
                try:
                    item = dict_d.popleft()
                except IndexError:
                    del self.dict_data[d]
                    break

                queue.append((item, 'HEAD'))
        try:
            item, method = queue.popleft()
        except IndexError:
            item, method = None, None
        return item, method

    def on_response(self, url, item, method, response, queue):
        if response.code in self.status:
            if item in self.found_items:
                return
            self.found_items[item] = None
            logger.warning('[Y] %s %s %s' % (response.code, method, url))
            # 自动对找到的代码文件扫描编辑器生成的备份文件
            if any(map(item.endswith, ['.php', '.asp', '.jsp'])):
                bak_list = self.make_bak_file_list(item)
                bak_list = [(t, 'HEAD') for t in bak_list]
                queue.extendleft(bak_list)
        else:
            if response.code == 405 and method != 'POST':
                queue.appendleft((item, 'POST'))

            if self.verbose:
                logger.info('[N] %s %s %s' % (response.code, method, url))

    def init_dict(self):
        if self.first_item != '':
            first_queue = [self.first_item]
            first_queue.extend(self.make_bak_file_list(self.first_item))
            first_queue = [(t, 'HEAD') for t in first_queue]
            self.first_queue.extend(first_queue)

        if self.scan_dict is None:
            self.dict_data['dir'] = read_dict('dictionary/dir.txt')
            if self.site_lang != '':
                self.dict_data[self.site_lang] = read_dict('dictionary/%s.txt' % self.site_lang)
            else:
                tmp_dict_list = [t for t in DICT_LIST if t != 'dir']
                for t in tmp_dict_list:
                    self.dict_data[t] = read_dict('dictionary/%s.txt' % t)
        else:
            for t in self.scan_dict:
                self.dict_data[t] = read_dict('dictionary/%s.txt' % t)

    @classmethod
    def make_bak_file_list(cls, file_name):
        """
        根据文件名称生成备份文件名称
        使用 vim 打开
        - index.php.swp # 强制关闭产生的
        - index.php~ # 备份文件

        使用vi编辑器，可能会产生一个临时文件
        - .index.php.swp
        - .index.php.swo
        - .index.php.swn

        使用UE等编辑器，会自动产生备份
        - index.php.bak
        :param file_name:
        :return:
        """
        data = [
            '~%s.swap' % file_name,
            '%s.swap' % file_name,
            '.%s.swap' % file_name,
            '.%s.swp' % file_name,
            '.%s.swo' % file_name,
            '.%s.swn' % file_name,
            '%s~' % file_name,
            '%s.swp' % file_name,
            '%s.bak' % file_name,
        ]

        return data

    def prepare_url(self):
        url_parsed = urlparse(self.raw_base_url)
        items = url_parsed.path.split('/')
        if len(items) > 0:
            item = items[-1]
            items = items[:-1]
            new_path = '/'.join(items)
        else:
            item = ''
            new_path = url_parsed.path
        url = urlunparse((url_parsed.scheme, url_parsed.netloc, new_path, '', '', ''))

        if item.endswith('.php'):
            self.site_lang = 'php'
        elif item.endswith('.asp'):
            self.site_lang = 'asp'
        elif item.endswith('.aspx'):
            self.site_lang = 'aspx'

        if self.site_lang != '':
            logger.info('site_lang: %s' % self.site_lang)
        self.base_url = url
        self.first_item = item
        logger.info('base_url: %s' % url)
        logger.info('first_item: %s' % item)

    @gen.coroutine
    def run(self):
        self.prepare_url()
        self.init_dict()
        executor = AsyncHTTPExecutor(
            self.base_url, self.on_queue_empty, self.first_queue,
            self.max_worker, self.timeout
        )
        yield executor.run(self.on_response)


@gen.coroutine
def main():
    (options, args) = parser.parse_args()
    if options.target_url is None or not validators.url(options.target_url):
        parser.print_help()
        return

    logger.info('target_url: %s' % options.target_url)
    logger.info('worker_num: %s' % options.worker_num)
    logger.info('timeout: %s' % options.timeout)
    if options.scan_dict is None:
        logger.info('scan_dict: auto')
    else:
        logger.info('scan_dict: %s' % options.scan_dict)

    ws = WebScanner(
        options.target_url, options.worker_num,
        options.timeout, options.scan_dict,
        options.verbose,
        options.status
    )
    yield ws.run()


if __name__ == '__main__':
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(main)
