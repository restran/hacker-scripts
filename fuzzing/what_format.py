# coding=utf-8


import os
import sys
import binascii

# dict = r'C:\MyTools\whatFormat.dic'
dict_data = 'what_format.dic'


def usage():
    data = '''
[+] This script help you to find outthe real format of the file or hide data from the file!
[+] the result file save at 'output' dir, go and search it!
[+] http://hi.baidu.com/l34rn
[+] cnh4ckff [at] gmail.com

[+] usage: %s <target file>
    ''' % sys.argv[0].split('\\')[-1]
    print(data)


def load_dict(d):
    dict_list = []
    with open(d, 'r') as lines:
        for line in lines:
            if line.strip() != '':
                if not line.startswith('#'):
                    ext, des, hex_dump = line.split('::')
                    dict_list.append([ext, des, hex_dump])
    return dict_list


def load_file(file_name):
    size = os.path.getsize(file_name)
    print('''
[+] File:               %s
[+] Size:               %s [Kb]
    ''' % (file_name, str(size / 1024)))
    with open(file_name, 'rb') as f:
        data = f.read()
        hex_data = binascii.hexlify(data)
    return hex_data


def check_format(hex_data, dict_list):
    res_list = []
    for d in dict_list:
        star = 0
        hex_dump = ''
        for hex_dump_tmp in d[2].strip():
            hex_dump_tmp = hex_dump_tmp.strip()
            if hex_dump_tmp != '':
                hex_dump += hex_dump_tmp.lower()
        while True:
            code = hex_data.find(hex_dump, star)
            if code != -1:
                star = code + 1
                res_list.append([d[0].strip(), d[1].strip(), code])
            else:
                break
    return res_list


def output(res_list, hex_data):
    i = 0
    for res in res_list:
        i += 1
        num = str(i)
        ext = res[0]
        des = res[1]
        startup = int(res[2])
        file_name = num + '.' + ext
        data = binascii.unhexlify(hex_data[startup:])
        save_file(file_name, data)
        print('''
[+] Number:             %s
[+] Extension:          %s
[+] Description:        %s
[+] Startup:            %s
[+] Saveas:             %s
        ''' % (num, ext, des, startup, file_name))


def save_file(file_name, data):
    if not os.path.exists('output'):
        os.mkdir('output')
    with open('output/' + file_name, 'wb') as f:
        f.write(data)


def main():
    # if len(sys.argv) < 2:
    #     usage()
    #     exit()

    file_name = 'convert_file'
    hex_data = load_file(file_name)
    dict_list = load_dict(dict_data)
    res_list = check_format(hex_data, dict_list)
    output(res_list, hex_data)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('[+] %s' % e)
