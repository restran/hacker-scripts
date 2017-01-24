# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import hashlib
import uuid
import sys


def main():
    if len(sys.argv) >= 2:
        length = int(sys.argv[1])
    else:
        length = 10

    for i in range(length):
        random_str = '%s' % uuid.uuid1()
        p = hashlib.md5(random_str).hexdigest()
        print(p[10:-10])


if __name__ == '__main__':
    main()
