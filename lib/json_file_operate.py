#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
将字典类型数据写入json文件或读取json文件并转为字典格式输出
"""

import json
import os


class JsonFileOperate:
    """
    需要传入文件所在目录，完整文件名。
    默认为只读，并将json文件转换为字典类型输出
    若为写入，需向resources传入字典类型数据
    默认为utf-8格式
    """

    def __init__(self, filepath, filename, way='r', resources=None, encoding='utf-8'):
        self.filepath = filepath
        self.filename = filename
        self.way = way
        self.resources = resources
        self.encoding = encoding

    def operation_file(self):
        if self.resources:
            self.way = 'w'
        with open(os.path.join(self.filepath, self.filename), self.way, encoding=self.encoding) as f:
            if self.resources:
                print(self.resources)
                f.write(json.dumps(self.resources, ensure_ascii=False))
            else:
                if '.json' in self.filename:
                    data = json.loads(f.read())
                else:
                    data = f.read()
                return data


if __name__ == '__main__':
    # writer
    dict_data = {"a": "1"}
    JsonFileOperate(
        resources=dict_data, filepath='./data/', filename='test.json'
    ).operation_file()
    # reader
    dict_data1 = JsonFileOperate(
        filepath='./data/', filename='test.json'
    ).operation_file()
