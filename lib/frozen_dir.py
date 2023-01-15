#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


def resource_path(relative_path: str):
    """Returns the base application path."""
    # os.path.join(os.path.dirname(os.path.realpath(sys.executable)), 'test.xlsx')

    # if hasattr(sys, 'frozen'):
    #     # Handles PyInstaller
    #     return os.path.dirname(sys.executable)
    # return os.path.dirname(__file__)

    # if getattr(sys, 'frozen', False):
    #     return os.path.dirname(os.path.abspath(sys.executable)).replace('lib', '')
    # elif __file__:
    #     return os.path.dirname(os.path.abspath(__file__)).replace('lib', '')

    # PyInstaller creates a temp folder and stores path in _MEIPASS
    if getattr(sys, 'frozen', False):  # 是否Bundle Resource
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
