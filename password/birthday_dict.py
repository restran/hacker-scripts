# -*- coding: utf-8 -*-
# Created by restran on 2016/9/25
from __future__ import unicode_literals, absolute_import
from datetime import datetime
from datetime import timedelta


def main():
    begin_date = datetime(year=1950, month=1, day=1)
    end_date = datetime(year=2017, month=1, day=1)

    data = []
    tmp = begin_date
    while tmp < end_date:
        d = tmp.strftime('%Y%m%d')
        data.append(d)
        tmp += timedelta(days=1)

    with open('birthday_dict.txt', 'w') as f:
        output = '\n'.join(data)
        f.write(output.encode('utf-8'))

    print('done')


if __name__ == '__main__':
    main()
