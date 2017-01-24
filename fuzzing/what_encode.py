# -*- coding: utf-8 -*-
# created by restran on 2016/09/30

"""
自动解析字符串数据是采用了怎样的编码
"""

import logging
from optparse import OptionParser
from copy import deepcopy
from base64 import b32decode, b16decode

FORMAT = "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(format=FORMAT, datefmt=DATE_FMT, level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 自动尝试这些编码
encode_methods = [
    'hex',
    'base64',
    'zlib',
    'base32',
    'binary',  # 01010101
    'base16'
]

parser = OptionParser()
parser.add_option("-d", "--data str", dest="data_str", type="string",
                  help="data str")
parser.add_option("-f", "--file name", dest="file_name", type="string",
                  help="read from file")
parser.add_option("-s", "--save file name", dest="save_file_name", type="string",
                  help="save decoded data to file")
parser.add_option("-m", "--decode method list", dest="method_list", type="string",
                  help="decode method list, base64->hex")


# TODO
# urlencode, binary

def parse_str(encode_str, decode_method, *args, **kwargs):
    if len(encode_str) == 0:
        return False, encode_str

    try:
        if decode_method == 'base16':
            decode_str = b16decode(encode_str)
        elif decode_method == 'base32':
            decode_str = b32decode(encode_str)
        elif decode_method == 'binary':
            tmp = encode_str.replace('0', '').replace('1', '').strip()
            if tmp == '':
                # 解码后是 0xab1234，需要去掉前面的 0x
                decode_str = hex(int(encode_str, 2))[2:].rstrip('L')
            else:
                return False, encode_str
        else:
            decode_str = encode_str.decode(decode_method)
        # logger.info('%s: %s' % (decode_method, decode_str))
        if len(decode_str) == 0:
            return False, encode_str
        else:
            return True, decode_str
    except Exception as e:
        # print(e)
        return False, encode_str


def try_method(encode_str, method, m_list):
    if method is not None:
        tmp_methods = [t for t in encode_methods if t != method]
        tmp_methods.insert(0, method)
    else:
        tmp_methods = deepcopy(encode_methods)

    for m in tmp_methods:
        success, decode_str = parse_str(encode_str, m)
        if success:
            encode_str = decode_str
            m_list.append(m)
            return try_method(encode_str, None, m_list)
    else:
        return encode_str, m_list


def parse(encode_str):
    encode_str = encode_str.strip()
    recognized_methods = []
    output_list = []
    for m in encode_methods:
        m_list = []
        decode_str, m_list = try_method(encode_str, m, m_list)
        if m_list in recognized_methods or len(decode_str) == 0:
            continue
        else:
            recognized_methods.append(m_list)
            tmp_list = deepcopy(m_list)
            length = len(tmp_list)
            for i in range(length):
                l = tmp_list[:length - i]
                if l in output_list:
                    continue
                else:
                    # 把所有找到的方法，按方法链，全部输出每个步骤的结果
                    output_list.append(l)
                    decode_str = decode_with_methods(encode_str, l)
                    logger.info('')
                    logger.info('methods: %s' % '->'.join(l))
                    logger.info('plain  : %s' % decode_str)
                    logger.info('size   : %s' % len(decode_str))

    if len(recognized_methods) <= 0:
        logger.info('not encode method recognized')


def decode_with_methods(data_str, method_list):
    success, decode_str = False, ''
    for m in method_list:
        success, decode_str = parse_str(data_str, m)
        if not success:
            logger.error('decode method list error, save file error')
    else:
        return decode_str


def decode_2_file(options, data_str):
    if options.save_file_name is not None and options.method_list:
        method_list = options.method_list.split('->')

        decode_str = decode_with_methods(data_str, method_list)
        with open(options.save_file_name, 'wb') as f:
            f.write(decode_str)

        return True
    else:
        return False


def main():
    (options, args) = parser.parse_args()

    if options.data_str is not None:
        if not decode_2_file(options, options.data_str):
            parse(options.data_str)
    elif options.file_name is not None:
        with open(options.file_name, 'rb') as f:
            data_str = f.read()
            if not decode_2_file(options, data_str):
                parse(data_str)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
