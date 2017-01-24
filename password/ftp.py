# -*- coding: utf-8 -*-
# Created by restran on 2016/10/10
from __future__ import unicode_literals, absolute_import

import logging
from ftplib import FTP
import os
import sys
# 把项目的目录加入的环境变量中，这样才可以导入 common.base
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.base import read_dict, TaskExecutor

logger = logging.getLogger(__name__)

ip_list = read_dict('ip.txt')
username_list = ['admin', 'root', 'test', 'cmcc', 'ftp']
found_password = []


def weak_pass(password, ip):
    for name in username_list:
        try:
            f = FTP(host=ip)
            f.login(user=name, passwd=password)
            found_password.append((ip, password))
            logger.info('[True ] %s %s:%s' % (ip, name, password))
            return True
        except Exception as e:
            logger.info(e)
            logger.info('[False] %s %s:%s' % (ip, name, password))

    return False


def anonymous(ip):
    try:
        f = FTP(host=ip)
        f.login()
        found_password.append((ip, '匿名登录'))
        logger.info('[True ] %s %s' % (ip, '匿名登录'))
        return True
    except Exception as e:
        logger.info(e)
        logger.info('[False] %s %s' % (ip, '匿名登录'))


def main():
    password_list = read_dict('password.dic')
    for ip in ip_list:
        # 测试匿名登录
        if anonymous(ip):
            continue

        executor = TaskExecutor(password_list, max_workers=20)
        executor.run(weak_pass, ip)

    for t in found_password:
        logger.info('%s password is %s' % t)


if __name__ == "__main__":
    main()
