# -*- coding: utf-8 -*-
# Created by restran on 2016/10/20

import os
import pyinotify
from optparse import OptionParser
from datetime import datetime

parser = OptionParser()
parser.add_option("-b", "--backup_dir", dest="backup_dir", type="string",
                  help="backup dir, e.g. /home/bak")
parser.add_option("-w", "--watch_dir", dest="watch_dir", type="string",
                  help="watch dir")
parser.add_option("-d", dest="disable_backup", action="store_true",
                  default=False, help="disable backup")

watch_dir_name = ''
back_dir_name = ''
protected_file_ext_list = [
    '.py', '.php', '.phps', '.ini', '.php1', '.php2', '.htaccess',
    '.php3', '.php4', '.php5', '.phtml', '.asp', '.jsp'
]

"""
使用方法

# 自动做文件备份
python monitor.py -w /home/monitor_dir -b /home/backup_dir
# 不做文件备份
python monitor.py -w /home/monitor_dir -b /home/backup_dir -d

# 如果修改备份文件夹中的文件，会自动同步到监控文件夹中
"""


class Logger(object):
    DATE_FMT = "%H:%M:%S"

    @classmethod
    def get_date_str(cls):
        now = datetime.now()
        return now.strftime(cls.DATE_FMT)

    @classmethod
    def info(cls, message):
        print('[%s] INFO %s' % (cls.get_date_str(), message))

    @classmethod
    def warning(cls, message):
        print('[%s] WARNING %s' % (cls.get_date_str(), message))


logger = Logger()


class FileEventHandler(pyinotify.ProcessEvent):
    @classmethod
    def do_delete_file(cls, file_path):
        shell_code = "rm -rf '%s'" % file_path
        os.system(shell_code)
        logger.warning(shell_code)

    @classmethod
    def delete_file(cls, file_path):
        # 创建的文件中不属于特殊的保护文件，允许创建，例如正常上传图片
        # 但是不允许创建文件夹，因为新建文件夹中的文件没有办法被监控
        if not any(map(file_path.lower().endswith, protected_file_ext_list)) \
                and not os.path.isdir(file_path):
            logger.info('skip file %s' % file_path)
            return

        cls.do_delete_file(file_path)

    def restore_file(self, pathname, event_filename):
        # 属于被修改文件，执行恢复
        logger.warning('restore file %s' % pathname)
        shell_code = "cp -a '%s%s' '%s'" % (back_dir_name, event_filename, pathname)
        os.system(shell_code)
        logger.warning(shell_code)

    def on_create_event(self, event):
        monitor_dir, event_filename, is_bak = get_file_name(event.pathname)
        logger.info('-----------------------------------------')
        logger.warning('on_create_event: %s' % event.pathname)
        if is_bak:
            logger.info('work in back dir, create')
            # 在备份目录中创建文件，直接复制过去
            pathname = '%s%s' % (watch_dir_name, event_filename)
            self.restore_file(pathname, event_filename)
            return

        file_exist = os.system("test -f '%s%s'" % (back_dir_name, event_filename))
        if file_exist == 0:
            # 文件存在，先判断md5，md5相同表示恢复文件
            temp1 = os.popen("md5sum '%s'| awk '{print $1}'" % event.pathname).readlines()
            temp2 = os.popen("md5sum '%s%s'| awk '{print $1}'" % (back_dir_name, event_filename)).readlines()
            if temp1 == temp2:
                # 属于恢复文件，不需要处理
                pass
            else:
                self.restore_file(event.pathname, event_filename)
        else:
            self.delete_file(event.pathname)

    def on_modify_event(self, event):
        monitor_dir, event_filename, is_bak = get_file_name(event.pathname)
        logger.info('-----------------------------------------')
        logger.warning('on_modify_event: %s' % event.pathname)
        if is_bak:
            # 在备份目录中修改文件，直接复制过去
            logger.info('work in back dir, modify')
            pathname = '%s%s' % (watch_dir_name, event_filename)
            self.restore_file(pathname, event_filename)
            return

        file_exist = os.system("test -f '%s%s'" % (back_dir_name, event_filename))
        if file_exist == 0:
            # 文件存在，先判断md5，md5相同表示恢复文件
            temp1 = os.popen("md5sum '%s'| awk '{print $1}'" % event.pathname).readlines()
            temp2 = os.popen("md5sum '%s%s'| awk '{print $1}'" % (back_dir_name, event_filename)).readlines()
            if temp1 == temp2:
                # 属于恢复文件，不需要处理
                pass
            else:
                self.restore_file(event.pathname, event_filename)
        else:
            self.delete_file(event.pathname)

    def on_delete_event(self, event):
        monitor_dir, event_filename, is_bak = get_file_name(event.pathname)
        logger.info("-----------------------------------------")
        logger.warning('on_delete_event: %s' % event.pathname)
        if is_bak:
            logger.info('work in back dir, delete')
            # 在备份目录中删除文件，直接删除
            pathname = '%s%s' % (watch_dir_name, event_filename)
            self.do_delete_file(pathname)
            return

        file_exist = os.system("test -f '%s%s'" % (back_dir_name, event_filename))
        # 0 表示存在
        if file_exist == 0:
            # 恢复文件
            self.restore_file(event.pathname, event_filename)
        else:
            pass

    def process_IN_MOVE_SELF(self, event):
        # logger.info('MOVE_SELF event: %s' % event.pathname)
        pass

    # 等价于执行删除
    def process_IN_MOVED_FROM(self, event):
        # logger.info('-----------------------------------------')
        logger.info('MOVED_FROM event: %s' % event.pathname)
        self.on_delete_event(event)

    # 文件重命名，或者复制，等价于执行复制
    def process_IN_MOVED_TO(self, event):
        # logger.info('-----------------------------------------')
        logger.warning('MOVED_TO event: %s' % event.pathname)
        self.on_create_event(event)

    def process_IN_ACCESS(self, event):
        # print "-----------------------------------------"
        # print "ACCESS event:", event.pathname
        # logger.info('ACCESS event: %s' % event.pathname)
        pass

    def process_IN_ATTRIB(self, event):
        # print "-----------------------------------------"
        # print "ATTRIB event:", event.pathname
        # logger.info('ATTRIB event: %s' % event.pathname)
        pass

    def process_IN_CLOSE_NOWRITE(self, event):
        # print "-----------------------------------------"
        # print "CLOSE_NOWRITE event:", event.pathname
        # logger.info('CLOSE_NOWRITE event: %s' % event.pathname)
        pass

    # 文件写完成
    def process_IN_CLOSE_WRITE(self, event):
        # logger.info('-----------------------------------------')
        # logger.info('CLOSE_WRITE event: %s' % event.pathname)
        pass

    def process_IN_CREATE(self, event):
        # logger.info('-----------------------------------------')
        # logger.warning('CREATE event: %s' % event.pathname)
        self.on_create_event(event)

    def process_IN_DELETE(self, event):
        # logger.info("-----------------------------------------")
        # logger.warning('DELETE event: %s' % event.pathname)
        self.on_delete_event(event)

    def process_IN_MODIFY(self, event):
        # logger.info('-----------------------------------------')
        # logger.warning('MODIFY event: %s' % event.pathname)
        self.on_modify_event(event)

    def process_IN_OPEN(self, event):
        # print "-----------------------------------------"
        # print "OPEN event:", event.pathname
        pass


def get_file_name(path_name):
    """
    目录，最后的文件名，是否备份目录
    :param path_name:
    :return:
    """
    # 因为备份目录不能是 watch 的子目录，因此可以这样判断
    if back_dir_name in path_name:
        return back_dir_name, path_name[len(back_dir_name):], True
    else:
        return watch_dir_name, path_name[len(watch_dir_name):], False


def backup_monitor_dir(watch_dir, backup_dir):
    logger.info('backup files')
    if os.system('test -d %s' % backup_dir) != 0:
        os.system('mkdir -p %s' % backup_dir)

    os.system('rm -rf %s/*' % backup_dir)
    logger.info('cp -a %s/* %s/' % (watch_dir, backup_dir))
    os.system('cp -a %s/* %s/' % (watch_dir, backup_dir))


def main():
    (options, args) = parser.parse_args()
    if None in [options.watch_dir, options.backup_dir]:
        parser.print_help()
        return

    # 删除最后的 /
    options.watch_dir = options.watch_dir.rstrip('/')
    options.backup_dir = options.backup_dir.rstrip('/')

    global watch_dir_name
    global back_dir_name
    watch_dir_name = options.watch_dir
    back_dir_name = options.backup_dir

    logger.info('watch dir %s' % options.watch_dir)
    logger.info('back  dir %s' % options.backup_dir)

    if not options.disable_backup:
        backup_monitor_dir(options.watch_dir, options.backup_dir)

    # watch manager
    wm = pyinotify.WatchManager()
    wm.add_watch(options.watch_dir, pyinotify.ALL_EVENTS, rec=True)
    wm.add_watch(options.backup_dir, pyinotify.ALL_EVENTS, rec=True)

    # event handler
    eh = FileEventHandler()

    # notifier
    notifier = pyinotify.Notifier(wm, eh)
    notifier.loop()


if __name__ == '__main__':
    main()
