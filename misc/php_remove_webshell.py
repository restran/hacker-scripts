# -*- coding: utf-8 -*-
# Created by restran on 2016/10/23
from __future__ import absolute_import

"""
批量注释代码中的一句话木马
用于快速替换指定目录中的文件当中的eval($_POST['XXX'])
python php_remove_webshell.py 文件夹名称
"""

from os import walk
import re
import sys
import traceback

pattern = re.compile(
    r'(@?\s*(assert|eval)\s*\(\s*\$_(POST|GET|REQUEST|COOKIE)\s*\[[^\]]+\]\s*\)\s*;)', re.I)


def find_all(p, content, pos=0):
    ret = ''
    match = p.search(content, pos)
    if match is not None:
        ret = find_all(p, content, match.span()[1])
        return ret + match.group(0)
    else:
        return ret


def replace(content):
    match = pattern.search(content)
    flag = match is not None
    item = ''
    if flag:
        item = find_all(pattern, content, pos=0)
        content = pattern.sub(lambda m: '/*' + m.group(0) + '*/', content)
    if flag:
        return flag, item, content
    else:
        return flag, None, content


def run(path):
    for root, dirs, files in walk(path):
        for f in files:
            if not f.endswith('.php'):
                continue
            else:
                # print(f)
                pass

            if not root.endswith('/'):
                f = root + '/' + f
            else:
                f = root + f
            try:
                with open(f, 'r') as fp:
                    content = fp.read()

                found, item, content = replace(content)
                if found:
                    print('[%s] : (%s) is changed!' % (f, item))
                    with open(f, 'w') as fp:
                        fp.write(content)
            except Exception as ex:
                print(ex)
                print(traceback.format_exc())
    print('done')


if __name__ == '__main__':
    run(sys.argv[1])
