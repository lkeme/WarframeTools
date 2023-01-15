#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ctypes
import time


# 当前时间
def current_time():
    # return f"[{str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))}]"
    return f"[{str(time.strftime('%H:%M:%S', time.localtime(time.time())))}]"


# 清理字典
def clear_dict(d):
    if d is None:
        return None
    elif isinstance(d, list):
        return list(filter(lambda x: x is not None, map(clear_dict, d)))
    elif not isinstance(d, dict):
        return d
    else:
        r = dict(
            filter(lambda x: x[1] is not None,
                   map(lambda x: (x[0], clear_dict(x[1])),
                       d.items())))
        if not bool(r):
            return None
        return r


# 判断管理员权限 1是管理员 0不是管理员
def is_admin():
    """
    Check whether the user is an administrator.
    :return:
    """
    # noinspection PyBroadException
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as _:
        return False
