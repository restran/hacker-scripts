# -*- coding: utf-8 -*-
# Created by restran on 2016/10/23
from __future__ import unicode_literals, absolute_import
import re


def waf_sql_inject_filter(input_data):
    """
    sql inject filter
    """
    re_list = [
        r'(\/\*.*?\*\/)',  # 替换注释1
        r'[#\s]',  # 替换mysql注释及空格换行
        r'\-\-.*$',  # 替换注释2
        r'\s+(and|or|union|select)\s+',  # 替换SQL关建字
        r'([\.]+\/|\/[^\s\\]+)',  # 替换所有路径
        r'[^\s]+\s*\([^\)]*\)', # 替换函数
        r'(push|pop|viewbox|fill)\s+.*',     # IM
        r'(php|phar):\/\/\s*[^\s]+',          # php stream        
        r'\<\?php\s+.*\?\>'  # PHP
    ]

    for t in re_list:
        pattern = re.compile(t, re.I)
        input_data, number = pattern.subn('', input_data)
        print('%s, %s' % (input_data, number))

    return input_data
