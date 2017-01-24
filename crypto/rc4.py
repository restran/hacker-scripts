# -*- coding: utf-8 -*-
# Created by restran on 2016/12/4
from __future__ import unicode_literals, absolute_import
import random
import base64
from hashlib import sha1

"""
rc4 算法
"""


def crypt(data, key):
    """RC4 algorithm"""
    x = 0
    box = range(256)
    for i in range(256):
        x = (x + box[i] + ord(key[i % len(key)])) % 256
        box[i], box[x] = box[x], box[i]
    x = y = 0
    out = []
    for char in data:
        x = (x + 1) % 256
        y = (y + box[x]) % 256
        box[x], box[y] = box[y], box[x]
        out.append(chr(ord(char) ^ box[(box[x] + box[y]) % 256]))

    return ''.join(out)


def rc4_encode(data, key, encode=base64.b64encode, salt_length=16):
    """RC4 encryption with random salt and final encoding"""
    salt = ''
    for n in range(salt_length):
        salt += chr(random.randrange(256))
    data = salt + crypt(data, sha1(key + salt).digest())
    if encode:
        data = encode(data)
    return data


def rc4_decode(data, key, decode=base64.b64decode, salt_length=16):
    """RC4 decryption of encoded data"""
    if decode:
        data = decode(data)
    salt = data[:salt_length]
    return crypt(data[salt_length:], sha1(key + salt).digest())


def main():
    # 需要加密的数据
    data = 'UUyFTj8PCzF6geFn6xgBOYSvVTrbpNU4OF9db9wMcPD1yDbaJw== '
    # 密钥
    key = 'welcometoicqedu'

    # 加码
    encoded_data = rc4_encode(data=data, key=key)
    print(encoded_data)
    # 解码
    decoded_data = rc4_decode(data=encoded_data, key=key)
    print(decoded_data)


if __name__ == '__main__':
    main()
