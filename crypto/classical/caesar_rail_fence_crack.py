# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
凯撒困在栅栏里了,需要你的帮助。
sfxjkxtfhwz9xsmijk6j6sthhj

flag格式：NSFOCUS{xxx}，以及之前的格式
"""


def rail_fence(e):
    # e = 'tn c0afsiwal kes,hwit1r  g,npt  ttessfu}ua u  hmqik e {m,  n huiouosarwCniibecesnren.'
    elen = len(e)
    field = []
    for i in range(2, elen):
        if elen % i == 0:
            field.append(i)

    output = []
    for f in field:
        b = elen / f
        result = {x: '' for x in range(b)}
        for i in range(elen):
            a = i % b;
            result.update({a: result[a] + e[i]})
        d = ''
        for i in range(b):
            d = d + result[i]
        output.append(d)
        print('分为\t' + str(f) + '栏时，解密结果为：' + d)

    return output


class Caesar(object):
    """docstring for caesar"""

    @classmethod
    def convert(cls, c, key, start='a', n=26):
        a = ord(start)
        offset = ((ord(c) - a + key) % n)
        return chr(a + offset)

    @classmethod
    def encode(cls, s, key):
        o = ""
        for c in s:
            if c.islower():
                o += cls.convert(c, key, 'a')
            elif c.isupper():
                o += cls.convert(c, key, 'A')
            else:
                o += c
        return o

    @classmethod
    def decode(cls, s, key):
        return cls.encode(s, -key)


def main():
    key_prefix = ['flag', 'key', 'Key', 'Flag', 'nscf']

    data = 'T_ysK9_5rhk__uFMt}3El{nu@E '
    output = rail_fence(data)
    for t in output:
        for key in range(26):
            d = Caesar.decode(t, key)
            tmp = d.lower()
            print(d)
            for x in key_prefix:
                if tmp.startswith(x):
                    print(d)


if __name__ == '__main__':
    main()
