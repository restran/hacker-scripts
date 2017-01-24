# -*- coding: utf-8 -*-
# Created by restran on 2016/10/10
from __future__ import unicode_literals, absolute_import
# noinspection PyCompatibility
from concurrent import futures
from future.moves.queue import Queue, PriorityQueue
from collections import deque
import time
import logging
from colorlog import ColoredFormatter
import logging.config
import os
import sys
import grequests

# 当前项目所在路径
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 日志所在目录
LOG_PATH = BASE_PATH
# 可以给日志对象设置日志级别，低于该级别的日志消息将会被忽略
# CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
LOGGING_LEVEL = 'INFO'
LOGGING_HANDLERS = ['console_color', 'file']

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': "%(log_color)s[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s %(reset)s",
            'datefmt': "%H:%M:%S",
            'log_colors': {
                'DEBUG': 'white',
                'INFO': 'white',
                'WARNING': 'green',
                'ERROR': 'yellow',
                'CRITICAL': 'red',
                # 'CRITICAL': 'red, bg_white',
            }
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'console_color': {
            'level': 'DEBUG',
            'class': 'colorlog.StreamHandler',
            'formatter': 'colored'
        },
        'file': {
            'level': 'DEBUG',
            # 'class': 'logging.FileHandler',
            'class': 'logging.handlers.RotatingFileHandler',
            # 如果没有使用并发的日志处理类，在多实例的情况下日志会出现缺失
            # 当达到10MB时分割日志
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 1,
            # If delay is true,
            # then file opening is deferred until the first call to emit().
            'delay': True,
            'filename': os.path.join(LOG_PATH, 'script.log'),
            'formatter': 'verbose'
        }
    },
    'loggers': {
        '': {
            'handlers': LOGGING_HANDLERS,
            'level': LOGGING_LEVEL,
        }
    }
})

logger = logging.getLogger(__name__)
# Useful for very coarse version differentiation.
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
PYPY = True if getattr(sys, 'pypy_version_info', None) else False

if PY3:
    from io import BytesIO
    text_type = str
    binary_type = bytes
else:
    from cStringIO import StringIO as BytesIO

    text_type = unicode
    binary_type = str


def group(lst, n):
    """
    http://code.activestate.com/recipes/303060-group-a-list-into-sequential-n-tuples/
    Group a list into sequential n-tuples
    :param lst:
    :param n:
    :return:
    """
    for i in range(0, len(lst), n):
        val = lst[i:i + n]
        if len(val) == n:
            yield tuple(val)


_UTF8_TYPES = (bytes, type(None))


def utf8(value):
    """Converts a string argument to a byte string.
    """
    if isinstance(value, _UTF8_TYPES):
        return value
    if not isinstance(value, text_type):
        raise TypeError(
            "Expected bytes, unicode, or None; got %r" % type(value)
        )
    return value.encode("utf-8")


_TO_UNICODE_TYPES = (text_type, type(None))


def to_unicode(value):
    """Converts a string argument to a unicode string.
    """
    if isinstance(value, _TO_UNICODE_TYPES):
        return value
    if not isinstance(value, bytes):
        raise TypeError(
            "Expected bytes, unicode, or None; got %r" % type(value)
        )
    try:
        value = value.decode('utf-8')
    except:
        try:
            value = value.decode('gbk')
        except:
            pass

    return value


def read_dict(file_name, clear_none=False):
    """
    读取字典文件
    :param clear_none:
    :param file_name:
    :return:
    """
    with open(file_name, 'r') as f:
        data = [line.strip() for line in f]
        new_data = []
        for t in data:
            new_data.append(to_unicode(t))
        if clear_none:
            data = [t for t in new_data if t != '']
        data = deque(data)
    return data


def ip_range(start_ip, end_ip):
    ip_list = []
    start = list(map(int, start_ip.split(".")))
    end = list(map(int, end_ip.split(".")))
    tmp = start
    ip_list.append(start_ip)
    while tmp != end:
        start[3] += 1
        for i in (3, 2, 1):
            if tmp[i] == 256:
                tmp[i] = 0
                tmp[i - 1] += 1
        ip_list.append(".".join(map(str, tmp)))

    return ip_list


class TaskExecutor(object):
    """
    使用线程的执行器，可以并发执行任务
    """

    def __init__(self, task_list, max_workers=5):
        self.max_workers = max_workers
        self.task_list = task_list
        self.task_queue = Queue()
        for t in task_list:
            self.task_queue.put(t)

    def get_next_task(self, max_num):
        output = []
        count = 0
        while not self.task_queue.empty() and count < max_num:
            t = self.task_queue.get()
            output.append(t)
            count += 1

        return output

    def run(self, fn_task, *args, **kwargs):
        logger.info('executor start')
        start_time = time.time()
        with futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            next_tasks = self.get_next_task(self.max_workers)
            future_to_task = {
                executor.submit(fn_task, task, *args, **kwargs): task
                for task in next_tasks
                }
            should_shut_down = False
            while not should_shut_down and len(future_to_task.items()) > 0:
                tmp_future_to_task = {}

                for future in futures.as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        should_shut_down = future.result()
                    except Exception as exc:
                        logger.info('%s generated an exception: %s' % (task, exc))
                    else:
                        if should_shut_down:
                            break

                        new_task = self.get_next_task(1)
                        if len(new_task) > 0:
                            task = new_task[0]
                            tmp_future_to_task[executor.submit(fn_task, task, *args, **kwargs)] = task

                future_to_task = tmp_future_to_task
        end_time = time.time()
        logger.info('executor done, %.3fs' % (end_time - start_time))


class AsyncHTTPExecutor(object):
    """
    异步HTTP请求，可以并发访问
    """

    def __init__(self, fn_on_queue_empty, max_workers=20, timeout=3):
        self.fn_on_queue_empty = fn_on_queue_empty
        self.task_queue = deque()
        self.timeout = timeout
        self.max_workers = max_workers
        # data = func_add_2_queue()
        # for t in data:
        #     self.task_queue.append(t)

    def get_next_task(self, max_num):
        output = []
        count = 0
        no_more_task = False
        while count < max_num:
            try:
                item = self.task_queue.popleft()
                output.append(item)
                count += 1
            except IndexError:
                no_more_task = self.fn_on_queue_empty(self.task_queue, max_num)
                if no_more_task:
                    break

        return no_more_task, output

    def run(self, fn_on_response, *args, **kwargs):
        logger.info('executor start')
        start_time = time.time()
        no_more_task, urls = self.get_next_task(self.max_workers)
        while True:
            if len(urls):
                break

            tmp_urls = []
            urls = (grequests.head(u, timeout=self.timeout) for u in urls)
            for r in grequests.imap(urls):
                fn_on_response(r)
                no_more_task, urls = self.get_next_task(self.max_workers)
                if len(urls):
                    break

        end_time = time.time()
        logger.info('executor done, %.3fs' % (end_time - start_time))


class ColorConsole(object):
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"

    @classmethod
    def green(cls, message):
        return '%s%s%s' % (cls.GREEN, message, cls.END)

    @classmethod
    def blue(cls, message):
        return '%s%s%s' % (cls.BLUE, message, cls.END)

    @classmethod
    def red(cls, message):
        return '%s%s%s' % (cls.RED, message, cls.END)

    @classmethod
    def yellow(cls, message):
        return '%s%s%s' % (cls.YELLOW, message, cls.END)

    @classmethod
    def bold(cls, message):
        return '%s%s%s' % (cls.BOLD, message, cls.END)
