# -*- coding: utf-8 -*-
# Created by restran on 2017/1/21
from __future__ import unicode_literals, absolute_import

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
from datetime import datetime
from bs4 import BeautifulSoup
import ipaddr

# 把项目的目录加入的环境变量中，这样才可以导入 common.base
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.base import read_dict, text_type

logger = logging.getLogger(__name__)
# 最大并发数量
ASYNC_HTTP_MAX_CLIENTS = 200

parser = OptionParser()
parser.add_option("-f", "--file_ip", dest="ip_list_file", type="string",
                  help="e.g. ip_list.txt")
parser.add_option("-w", "--worker", dest="worker_num", type="int",
                  default=10, help="max worker num")
parser.add_option("-t", "--timeout", dest="timeout", type="int",
                  default=3, help="timeout in seconds")
parser.add_option("-v", dest="verbose", action="store_true",
                  default=False, help="verbose log")

try:
    # curl_httpclient is faster than simple_httpclient
    AsyncHTTPClient.configure(
        'tornado.curl_httpclient.CurlAsyncHTTPClient',
        max_clients=ASYNC_HTTP_MAX_CLIENTS)
except ImportError:
    AsyncHTTPClient.configure(
        'tornado.simple_httpclient.AsyncHTTPClient',
        max_clients=ASYNC_HTTP_MAX_CLIENTS)


class AsyncHTTPExecutor(object):
    """
    异步HTTP请求，可以并发访问
    """

    def __init__(self, fn_on_queue_empty, max_workers=10,
                 timeout=2, verbose=False):
        self.fn_on_queue_empty = fn_on_queue_empty
        self.task_queue = deque()
        self.timeout = timeout
        self.max_workers = max_workers
        self.verbose = verbose
        self.count = 0
        self.port_list = [80, 8080, 8000]
        self.start_time = None
        self.last_time = None

    def get_next_task(self):
        try:
            item = self.task_queue.popleft()
        except IndexError:
            item = self.fn_on_queue_empty(self.task_queue)
        return item

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

        url = item.decode('utf-8')
        try:
            body = '' if method == 'POST' else None
            response = yield AsyncHTTPClient().fetch(
                HTTPRequest(url=url,
                            method=method,
                            body=body,
                            decompress_response=True,
                            validate_cert=False,
                            connect_timeout=self.timeout,
                            request_timeout=self.timeout,
                            follow_redirects=True))
            fn_on_response(url, item, method, response, self.task_queue)
        except HTTPError as e:
            if hasattr(e, 'response') and e.response:
                fn_on_response(url, item, method, e.response, self.task_queue)
            else:
                pass
                # logger.error('Exception: %s %s %s' % (e, method, item))
        except Exception as e:
            pass
            # logger.error('Exception: %s %s %s' % (e, method, item))

    @gen.coroutine
    def fetch_url(self, i, fn_on_response):
        item = self.get_next_task()
        while item is not None:
            try:
                if '/' in item:
                    mask = ipaddr.IPv4Network(item)
                    ip_list = [text_type(t) for t in mask.iterhosts()]
                else:
                    ip_list = [item]
            except Exception as e:
                ip_list = []

            for t in ip_list:
                if t == '':
                    continue

                url_list = ['http://%s:%s' % (t, p) for p in self.port_list]
                url_list.extend(['https://%s:%s' % (t, p) for p in [443, 8443]])
                for u in url_list:
                    yield self.do_request(u, 'GET', fn_on_response)
            item = self.get_next_task()

    @gen.coroutine
    def run(self, fn_on_response, *args, **kwargs):
        logger.info('executor start')
        self.start_time = time.time()
        self.last_time = self.start_time
        # Start workers, then wait for the work queue to be empty.
        # 会卡在这里，等待所有的 worker 都结束
        yield [self.fetch_url(t, fn_on_response) for t in range(self.max_workers)]
        end_time = time.time()
        logger.info('total count: %s' % self.count)
        cost_time = end_time - self.start_time
        if cost_time > 0:
            speed = self.count / cost_time
        else:
            speed = 1

        logger.info('executor done, %.3f, %.1f/s' % (cost_time, speed))


class WebScanner(object):
    def __init__(self, ip_file_name, max_worker=10, timeout=3):
        self.max_worker = max_worker
        self.timeout = timeout
        self.list_data = deque()
        self.ip_file_name = ip_file_name
        self.found_items = {}
        self.status = [200, 301, 302, 304, 401, 403]

    def on_queue_empty(self, queue, max_num=100):
        for _ in range(max_num):
            try:
                item = self.list_data.popleft()
                if '/' in item:
                    mask = ipaddr.IPv4Network(item)
                    ip_list = [text_type(t) for t in mask.iterhosts()]
                else:
                    ip_list = [item]
                queue.extend(ip_list)
            except IndexError:
                break

        try:
            item = queue.popleft()
        except IndexError:
            item = None
        return item

    def on_response(self, url, item, method, response, queue):
        if url in self.found_items:
            return
        try:
            soup = BeautifulSoup(response.body, 'html.parser')
            title = soup.title.text.replace('\n', ' ')
            if title is None:
                title = response.body[:30].encode('utf-8').replace('\n', ' ')
        except Exception as e:
            title = ''

        if response.code in self.status:
            self.found_items[url] = title
            logger.warning('[Y] %s %s %s' % (response.code, url, title))
        else:
            logger.info('%s %s %s' % (response.code, url, title))

    def init_dict(self):
        self.list_data = read_dict(self.ip_file_name)

    def save_found(self):
        if len(self.found_items.keys()) <= 0:
            return
        now = datetime.now()
        f_name = now.strftime('site_%Y%m%d_%H%M%S.txt')
        with open(f_name, 'w') as f:
            data = ['%s : %s' % (key, value) for (key, value) in self.found_items.iteritems()]
            data = '\n'.join(data)
            try:
                f.write(data.encode('utf-8'))
            except Exception as e:
                logger.error(e)

    @gen.coroutine
    def run(self):
        self.init_dict()
        executor = AsyncHTTPExecutor(
            self.on_queue_empty,
            self.max_worker, self.timeout
        )
        yield executor.run(self.on_response)
        self.save_found()


@gen.coroutine
def main():
    (options, args) = parser.parse_args()
    if options.ip_list_file is None:
        parser.print_help()
        return

    w = WebScanner(ip_file_name=options.ip_list_file,
                   max_worker=options.worker_num,
                   timeout=options.timeout)
    yield w.run()


if __name__ == '__main__':
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(main)
