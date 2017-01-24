# -*- coding: utf-8 -*-
# Created by restran on 2016/11/22
from __future__ import absolute_import
from os import walk
from os.path import join, getsize
import sys

"""
比较两个文件夹内有哪些不同的文件
"""


def traverse_dir(path):
    file_dict = {}
    dir_dict = {}
    count = 1
    for root, dirs, files in walk(path):
        for d in dirs:
            abs_p = join(root, d)
            dir_dict[abs_p] = 0
            print(abs_p)
            count += 1
            if count % 200 == 0:
                print('%s files scanned' % count)

        for f in files:
            abs_p = join(root, f)
            file_dict[abs_p] = getsize(abs_p)
            print(abs_p)
            count += 1
            if count % 200 == 0:
                print('%s files scanned' % count)

    return file_dict, dir_dict


def check_ignored_path(ignored_path, f):
    for t in ignored_path:
        if f.startswith(t):
            return True

    return False


def compare(file_dict, dir_dict, path2, path1):
    print('\n-------begin to compare-------\n')
    count = 1
    m_result = []
    c_result = []
    d_result = []
    ignored_path = []
    # 去掉根路径前缀，因为是不同的根路径在比较
    # prefix_path1_len = len(path1)
    prefix_path2_len = len(path2)
    for root, dirs, files in walk(path2):
        for d in dirs:
            abs_p = join(root, d)
            key = '%s%s' % (path1, abs_p[prefix_path2_len:])

            # 文件夹不存在，那么path1中该文件夹下的所有文件都不存在
            if key in dir_dict:
                del dir_dict[key]
            else:
                # 如果是上级目录，就不需要再重复添加
                if check_ignored_path(ignored_path, abs_p):
                    continue
                r = '[+] %s' % abs_p
                c_result.append(r)
                print(r)
                # 不用在继续判断该文件夹下的文件，因为都是[+]
                ignored_path.append(abs_p)

            count += 1
            if count % 200 == 0:
                print('%s files scanned' % count)

        for f in files:
            abs_p = join(root, f)
            if check_ignored_path(ignored_path, abs_p):
                continue

            size = getsize(abs_p)
            key = '%s%s' % (path1, abs_p[prefix_path2_len:])
            if key in file_dict:
                path1_size = file_dict[key]
                if path1_size != size:
                    r = '[*] %s %s %s' % (abs_p, path1_size, size)
                    m_result.append(r)
                    print(r)
                del file_dict[key]
            else:
                r = '[+] %s' % abs_p
                c_result.append(r)
                print(r)

            count += 1
            if count % 200 == 0:
                print('%s files scanned' % count)

    d_path_list = dir_dict.keys()
    for p in file_dict.keys():
        # 相同的路径，就只需要输出跟路径
        if check_ignored_path(d_path_list, p):
            continue

        r = '[-] %s' % p
        print(r)
        d_result.append(r)

    d_result.sort()
    return m_result, c_result, d_result


def main():
    if len(sys.argv) <= 3:
        print('Usage: python dir_compare.py path1 path2')
    path1 = sys.argv[1]
    path2 = sys.argv[2]
    print('\n-------scan path1-------\n')
    file_dict, dir_dict = traverse_dir(path1)
    m_result, c_result, d_result = compare(file_dict, dir_dict, path2, path1)

    with open('dir_compare_result.txt', 'w') as f:
        f.write(('path1: %s\n' % path1))
        f.write(('path2: %s\n' % path2))
        f.write('[*] modify path1_size path2_size\n')
        f.write('[+] create\n')
        f.write('[-] delete\n\n')
        f.write(('path2 has %s files modified\n\n' % len(m_result)).encode('utf-8'))
        f.write('\n'.join(m_result))
        f.write('\n\n')
        f.write(('path2 has %s files created\n\n' % len(c_result)).encode('utf-8'))
        f.write('\n'.join(c_result))
        f.write('\n\n')
        f.write(('path2 has %s files deleted\n\n' % len(d_result)).encode('utf-8'))
        f.write('\n'.join(d_result))
    print('\n------done------\n')


if __name__ == '__main__':
    main()
