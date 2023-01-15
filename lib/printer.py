#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect
import threading

from termcolor import *

from lib.common import current_time

_print_mutex = threading.Lock()
_debug = False


# _print = print
def _printer(info, *args, **kwargs):
    with _print_mutex:
        format_time = current_time()
        content = f'{format_time} {info} {" ".join(f"{str(arg)}" for arg in args)}'
        print(content, **kwargs)


# 样式一 信息、函数名、行数、内容
def printer(content, title, color):
    """
    Available text colors:
    grey, red, green, yellow, blue, magenta, cyan, white.

    Available text highlights:
        on_grey, on_red, on_green, on_yellow, on_blue, on_magenta, on_cyan, on_white.

    Available attributes:
        bold, dark, underline, blink, reverse, concealed.
    """
    with _print_mutex:
        ctm = current_time()
        tmp = f'[{title}]'
        if _debug:
            row = f'[{str(inspect.stack()[1][3])}:{str(inspect.stack()[1][2])}]'
            msg = f'{ctm} {tmp} {row} {content}'
        else:
            msg = f'{ctm}{tmp} {content}'
        print(colored(msg, color), flush=True)
