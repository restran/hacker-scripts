# -*- coding: utf-8 -*-
# Created by restran on 2016/10/10
from __future__ import unicode_literals, absolute_import
import sys
import os

# 当前目录所在路径
BASE_PATH = os.path.dirname(os.path.dirname(__file__))

SOURCE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def update_syspath():
    """
    将项目的目录，加入到系统的环境变量中
    :return:
    """
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
