# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
破解凯撒密码python脚本
"""


def convert(c, key, start='a', n=26):
    a = ord(start)
    offset = ((ord(c) - a + key) % n)
    return chr(a + offset)


def caesar_encode(s, key):
    o = ""
    for c in s:
        if c.islower():
            o += convert(c, key, 'a')
        elif c.isupper():
            o += convert(c, key, 'A')
        else:
            o += c
    return o


def caesar_decode(s, key):
    return caesar_encode(s, -key)


def main():
    for key in range(26):
        s = 'the tragedy of julius caesar.'
        # e = caesar_encode(s, key)
        d = caesar_decode(s, key)
        print(d)


if __name__ == '__main__':
    main()
