#!/usr/bin/env python
# -*- coding: utf_8 -*-
# Author: 蔚蓝行
from __future__ import unicode_literals

"""
破解栅栏密码python脚本
"""


def parse(e):
    # e = 'tn c0afsiwal kes,hwit1r  g,npt  ttessfu}ua u  hmqik e {m,  n huiouosarwCniibecesnren.'
    elen = len(e)
    field = []
    for i in range(2, elen):
        if elen % i == 0:
            field.append(i)

    for f in field:
        b = elen / f
        result = {x: '' for x in range(b)}
        for i in range(elen):
            a = i % b
            result.update({a: result[a] + e[i]})
        d = ''
        for i in range(b):
            d = d + result[i]
        print('分为\t' + str(f) + '\t' + '栏时，解密结果为：' + d)


def main():
    e = 'T_ysK9_5rhk__uFMt}3El{nu@E'
    parse(e)


if __name__ == '__main__':
    main()
