# -*- coding: utf-8 -*-
# Created by restran on 2016/10/20

import os
from threading import Thread
from optparse import OptionParser
from datetime import datetime
from md5py import md5
import shutil
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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
    '.php3', '.php4', '.php5', '.phtml', '.asp', '.jsp', '.asa', '.cer', '.cdx'
]

"""
使用方法

# 自动做文件备份
python monitor.py -w D:/monitor_dir -b D:/backup_dir
# 不做文件备份
python monitor.py -w D:/monitor_dir -b D:/backup_dir -d

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

    @classmethod
    def error(cls, message):
        print('[%s] ERROR %s' % (cls.get_date_str(), message))


logger = Logger()


class FileEventHandler(FileSystemEventHandler):
    @classmethod
    def recursive_make_parent_dir(cls, path, is_directory):
        try:
            if is_directory:
                # 递归创建父文件夹，否则后面执行 copyfile 的时候
                # 可能会因为没有文件夹而创建失败
                os.makedirs(os.path.abspath(os.path.join(path, os.path.pardir)))
            else:
                os.makedirs(os.path.dirname(path))
        except:
            pass

    @classmethod
    def do_delete_file(cls, file_path, is_directory):
        logger.info('delete %s' % file_path)
        try:
            if is_directory:
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
        except Exception as e:
            logger.error(e)

    @classmethod
    def delete_file(cls, event_path, is_directory):
        # 创建的文件中不属于特殊的保护文件，允许创建，例如正常上传图片
        # 允许创建文件夹，因为新建的文件夹也可以监控到
        # iis6解析漏洞，文件夹也不允许包含.php, .asp
        if not any(map(event_path.lower().endswith, protected_file_ext_list)):
            logger.info('skip file %s' % event_path)
            return

        cls.do_delete_file(event_path, is_directory)

    @classmethod
    def restore_file(cls, event_path, event_filename, is_directory):
        # 属于被修改文件，执行恢复
        logger.warning('restore file %s' % event_path)
        backup_file_path = '%s%s' % (back_dir_name, event_filename)

        try:
            # 递归创建父文件夹，否则后面执行 copyfile 的时候
            # 可能会因为没有文件夹而创建失败
            cls.recursive_make_parent_dir(event_path, is_directory)
            if is_directory:
                shutil.copytree(backup_file_path, event_path)
            else:
                shutil.copyfile(backup_file_path, event_path)
        except Exception as e:
            logger.error(e)

    def on_create_event(self, event_path, is_directory):
        monitor_dir, event_filename, is_bak = get_file_name(event_path)
        logger.info('-----------------------------------------')
        logger.warning('on_create_event: %s' % event_path)

        if is_bak:
            logger.info('work in back dir, create')
            # 在备份目录中创建文件，直接复制过去
            pathname = '%s%s' % (watch_dir_name, event_filename)
            self.restore_file(pathname, event_filename, is_directory)
            return

        pathname = '%s%s' % (back_dir_name, event_filename)
        file_exist = os.path.exists(pathname)
        if file_exist:
            if not is_directory:
                # 文件存在，先判断md5，md5相同表示恢复文件
                temp1 = file_md5(event_path)
                temp2 = file_md5(pathname)
                if temp1 == temp2:
                    # 属于恢复文件，不需要处理
                    pass
                else:
                    self.restore_file(event_path, event_filename, is_directory)
        else:
            self.delete_file(event_path, is_directory)

    def on_modify_event(self, event_path, is_directory):
        monitor_dir, event_filename, is_bak = get_file_name(event_path)
        logger.info('-----------------------------------------')
        logger.warning('on_modify_event: %s' % event_path)
        if is_directory:
            logger.info('skip dir modify event')
            return

        if is_bak:
            # 在备份目录中修改文件，直接复制过去
            logger.info('work in back dir, modify')
            pathname = '%s%s' % (watch_dir_name, event_filename)
            self.restore_file(pathname, event_filename, is_directory)
            return

        pathname = '%s%s' % (back_dir_name, event_filename)
        file_exist = os.path.exists(pathname)
        if file_exist:
            # 文件存在，先判断md5，md5相同表示恢复文件
            temp1 = file_md5(event_path)
            temp2 = file_md5(pathname)
            if temp1 == temp2:
                # 属于恢复文件，不需要处理
                pass
            else:
                self.restore_file(event_path, event_filename, is_directory)
        else:
            self.delete_file(event_path, is_directory)

    def on_delete_event(self, event_path, is_directory):
        monitor_dir, event_filename, is_bak = get_file_name(event_path)
        logger.info("-----------------------------------------")
        logger.warning('on_delete_event: %s' % event_path)
        if is_bak:
            logger.info('work in back dir, delete')
            # 在备份目录中删除文件，直接删除
            pathname = '%s%s' % (watch_dir_name, event_filename)
            self.do_delete_file(pathname, is_directory)
            return

        pathname = '%s%s' % (back_dir_name, event_filename)
        file_exist = os.path.exists(pathname)
        if file_exist:
            # 恢复文件
            self.restore_file(event_path, event_filename, is_directory)
        else:
            pass

    def on_moved(self, event):
        super(FileEventHandler, self).on_moved(event)
        self.on_delete_event(event.src_path, event.is_directory)
        self.on_create_event(event.dest_path, event.is_directory)

    def on_created(self, event):
        super(FileEventHandler, self).on_created(event)
        self.on_create_event(event.src_path, event.is_directory)

    def on_deleted(self, event):
        super(FileEventHandler, self).on_deleted(event)

        self.on_delete_event(event.src_path, event.is_directory)

    def on_modified(self, event):
        super(FileEventHandler, self).on_modified(event)
        self.on_modify_event(event.src_path, event.is_directory)


def watch_path(path):
    event_handler = FileEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(.5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def watch_backup(path):
    event_handler = FileEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(.5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def file_md5(path):
    if os.path.exists(path):
        with open(path, 'rb') as f:
            try:
                return md5(f.read()).hexdigest()
            except Exception as e:
                logger.warning(e)
                return None
    else:
        return None


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
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)

    # os.system('rd /s/q "%s/"' % backup_dir)
    shutil.copytree(watch_dir, backup_dir)
    # os.system('xcopy "%s/" "%s/" /O /X /E /H /K' % (watch_dir, backup_dir))


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

    Thread(target=watch_path, args=(watch_dir_name,)).start()
    Thread(target=watch_backup, args=(back_dir_name,)).start()

    logger.info('monitor is running now')


if __name__ == '__main__':
    main()
