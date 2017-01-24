# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import hashlib
import sys


def main():
    file_name = sys.argv[1]

    with open(file_name, 'rb') as f:
        data = f.read()
        sha256 = hashlib.sha256(data).hexdigest()
        print(sha256)


if __name__ == '__main__':
    main()
