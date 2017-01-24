# -*- coding: utf-8 -*-
# Created by restran on 2017/1/21
from __future__ import unicode_literals, absolute_import

import logging
import os
import sys
from collections import deque
from datetime import datetime
from threading import Thread, Lock
from optparse import OptionParser
from libnmap.parser import NmapParser, NmapParserException
from libnmap.process import NmapProcess

# 把项目的目录加入的环境变量中，这样才可以导入 common.base
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.base import read_dict

logger = logging.getLogger(__name__)

parser = OptionParser()
parser.add_option("-f", "--file_ip", dest="ip_list_file", type="string",
                  help="e.g. ip_list.txt")
parser.add_option("-w", "--worker", dest="worker_num", type="int",
                  default=10, help="max worker num")
parser.add_option("-v", dest="verbose", action="store_true",
                  default=False, help="verbose log")
parser.add_option("-p", "--file_options", dest="nmap_options_file", type="string",
                  help="e.g. nmap_options.txt")


class NMAPScanner(object):
    def __init__(self, ip_file_name, max_worker=10,
                 options='-v -sT -sV -Pn'):
        self.max_worker = max_worker
        self.ip_file_name = ip_file_name
        self.task_queue = deque()
        self.done_data = {}
        self.options = options
        self.total_count = 0
        self.lock = Lock()

    @classmethod
    def clear_file(cls):
        with open("nmap_up_ip.txt", "w") as f:
            f.write(''.encode('utf-8'))

        with open("nmap_ip_port.txt", "w") as f:
            f.write(''.encode('utf-8'))

    def init_dict(self):
        self.task_queue = read_dict(self.ip_file_name)
        self.total_count = len(self.task_queue)

    def get_next_task(self):
        try:
            item = self.task_queue.popleft()
        except IndexError:
            item = None
        return item

    def run(self):
        logger.info('run worker')
        self.clear_file()
        self.init_dict()
        for i in range(self.max_worker):
            Thread(target=self.worker_run, args=(i,)).start()

    def append_data(self, nmap_report):
        self.lock.acquire()
        with open("nmap_up_ip.txt", "a") as f:
            for host in nmap_report.hosts:
                if 'up' in host.status.lower():
                    f.write('%s\n'.encode('utf-8') % host.address)

        with open("nmap_ip_port.txt", "a") as f:
            for host in nmap_report.hosts:
                if 'up' not in host.status.lower():
                    continue

                port_list = []
                for serv in host.services:
                    if serv.state == 'open'.lower():
                        pserv = "%s/%s %s" % (
                            str(serv.port),
                            serv.protocol,
                            serv.service)
                        port_list.append(pserv)
                if len(port_list) > 0:
                    f.write('%s\t%s\n'.encode('utf-8') % (host.address, '\t'.join(port_list)))
        self.lock.release()

    def save_data(self):
        logger.info('save_data')
        now = datetime.now()
        f_name = now.strftime('nmap_%Y%m%d_%H%M%S.txt')
        # with open(f_name, 'w') as f:
        #     data = ['%s : %s' % (key, value) for (key, value) in self.done_data.iteritems()]
        #     data = '\n'.join(data)
        #     try:
        #         f.write(data.encode('utf-8'))
        #     except Exception as e:
        #         logger.error(e)

    def worker_run(self, worker_id):
        logger.info('worker %s start' % worker_id)
        item = self.get_next_task()
        while item is not None:
            report = self.do_scan(targets=item, options=self.options)
            if report:
                self.print_scan(report)
                self.append_data(report)
            item = self.get_next_task()

        if len(self.done_data.keys()) == self.total_count:
            logger.info('------scan has finished-------')
            self.save_data()

        logger.info('worker %s stop' % worker_id)

    def do_scan(self, targets, options):
        """
        start a new nmap scan on localhost with some specific options
        :param targets:
        :param options:
        :return:
        """
        logger.info('do scan %s %s' % (targets, options))
        parsed = None
        if isinstance(options, basestring):
            options = options.encode('utf-8')
        if isinstance(targets, basestring):
            targets = targets.encode('utf-8')
        nmproc = NmapProcess(targets, options)
        rc = nmproc.run()
        if rc != 0:
            logger.error("nmap scan failed: {0}".format(nmproc.stderr))
        # print(type(nmproc.stdout))

        try:
            parsed = NmapParser.parse(nmproc.stdout)
        except NmapParserException as e:
            logger.error("Exception raised while parsing scan: {0}".format(e.msg))

        self.done_data[targets] = parsed
        return parsed

    # print scan results from a nmap report
    @classmethod
    def print_scan(cls, nmap_report):
        # print("Starting Nmap {0} ( http://nmap.org ) at {1}".format(
        #     nmap_report.version,
        #     nmap_report.started))

        for host in nmap_report.hosts:
            if len(host.hostnames):
                tmp_host = host.hostnames.pop()
            else:
                tmp_host = host.address

            logger.info("Nmap scan report for {0} ({1})".format(
                tmp_host,
                host.address))
            logger.info("Host is {0}.".format(host.status))
            logger.info("  PORT     STATE         SERVICE")

            for serv in host.services:
                pserv = "{0:>5s}/{1:3s}  {2:12s}  {3}".format(
                    str(serv.port),
                    serv.protocol,
                    serv.state,
                    serv.service)
                if len(serv.banner):
                    pserv += " ({0})".format(serv.banner)
                logger.info(pserv)
        logger.info(nmap_report.summary)


def main():
    (options, args) = parser.parse_args()
    if options.ip_list_file is None:
        parser.print_help()
        return

    logger.info('ip_list_file: %s' % options.ip_list_file)
    logger.info('worker_num: %s' % options.worker_num)
    # pg数据库 5432
    nmap_options = '-v -sT -sV -Pn -p21,22,23,80,81,88,443,445,873,1433,1521,3306,3389,5432,6379,8000-8100,8443,11211,27017'
    if options.nmap_options_file is not None:
        with open(options.nmap_options_file) as f:
            nmap_options = f.read().strip().replace('\n', '')

    s = NMAPScanner(ip_file_name=options.ip_list_file,
                    max_worker=options.worker_num, options=nmap_options)
    s.run()


if __name__ == "__main__":
    main()
