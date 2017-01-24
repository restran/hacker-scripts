# -*- coding: utf-8 -*-
# Created by restran on 2016/10/10
from __future__ import unicode_literals, absolute_import

import logging
import os
import sys
import psycopg2

# 把项目的目录加入的环境变量中，这样才可以导入 common.base
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.base import TaskExecutor, read_dict

logger = logging.getLogger(__name__)

"""
PostgreSQL 弱口令爆破
"""

found_password = []

ip_list = read_dict('ip.txt', clear_none=True)
username_list = ['postgres', 'root']
database_name = None


def weak_pass(password, ip, db, port_list=None):
    for name in username_list:
        if port_list is None:
            port_list = [5432, 1521]

        for port in port_list:
            try:
                psycopg2.connect(host=ip,
                                 port=port,
                                 database=database_name,
                                 user=name,
                                 password=password, )

                logger.info('[True ] %s %s:%s' % (ip, name, password))
                found_password.append((ip, '%s:%s' % (name, password)))
                return True
            except Exception as e:
                logger.info(e)
                logger.info('[False] %s %s:%s' % (ip, name, password))

    return False


def main():
    password_list = read_dict('password.dic')
    for ip in ip_list:
        executor = TaskExecutor(password_list)
        executor.run(weak_pass, ip, database_name)

    for t in found_password:
        logger.info('%s password is %s' % t)


if __name__ == "__main__":
    main()
