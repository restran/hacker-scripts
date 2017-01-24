# -*- coding: utf-8 -*-
# Created by restran on 2016/8/3
from __future__ import unicode_literals, absolute_import
from Crypto.PublicKey import RSA


class RSAHelper(object):
    @classmethod
    def decrypt(cls, encrypted_file, key_file,
                out_file='output_dec', passphrase=''):
        """
        解密
        :param out_file:
        :param encrypted_file:
        :param key_file:
        :param passphrase:
        :return:
        """
        print('decrypt')
        with open(key_file, "r") as kf:
            rsa = RSA.importKey(kf.read(), passphrase=passphrase)
            with open(encrypted_file, 'rb') as df:
                data = rsa.decrypt(df.read())
                print('data:\n')
                print(data)
                print('hex:')
                print(data.encode('hex'))
                with open(out_file, "wb") as of:
                    of.write(data)

    @classmethod
    def encrypt(cls, raw_file, key_file, out_file='output_enc', passphrase=''):
        """
        加密
        :param out_file:
        :param raw_file:
        :param key_file:
        :param passphrase:
        :return:
        """
        print('encrypt')
        with open(key_file, "r") as kf:
            rsa = RSA.importKey(kf.read(), passphrase=passphrase)
            with open(raw_file, 'rb') as df:
                data = rsa.encrypt(df.read(), 0)
                print('data:')
                print(data)
                print('hex:')
                print(data.encode('hex'))
                with open(out_file, "wb") as of:
                    of.write(data[0])


if __name__ == '__main__':
    RSAHelper.decrypt('flag.enc', 'pub.key')
    # RSAHelper.encrypt('raw_data.txt', 'private_key.txt')
    # RSAHelper.decrypt('output.txt', 'private_key.txt')
    # RSAHelper.decrypt('key.enc', 'publickey.pub')
