#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import datetime
import logging
from string import Template
from typing import Mapping

logger = logging.getLogger(__name__)

default_macro_config = {
    'today': {'impl': lambda: datetime.datetime.now().strftime("%Y%m%d"), 'description': "今天的日期.格式:yyyymmdd"},
    'today:1': {'impl': lambda: datetime.datetime.now().strftime("%Y%m%d"), 'description': "今天的日期.格式:yyyymmdd"},
    'today:2': {'impl': lambda: datetime.datetime.now().strftime("%Y-%m-%d"),
                'description': "今天的日期.格式:yyyy-mm-dd"},
    'test': {'impl': 'test abc'},
    'n': {'impl': lambda: 50},
    'year:1': {'impl': lambda: datetime.datetime.now().strftime("%Y")},
}


class StringTemplate(Template):
    idpattern = r'(?a:[_a-zA-Z][_:a-zA-Z0-9]*)'


class MacroTemplate(object):
    template = StringTemplate

    def __init__(self, macro_config):
        self.macro_config = macro_config
        self._strings = []
        self._using_macro_names = set()
        self.used_macro_maps = None

    def get_macro_map(self, names):
        """
        获取输入的名称对应的值的map
        :param names:
        :return:
        """
        result = {}
        for name in names:
            if name not in self.macro_config:
                continue
            item = self.macro_config[name]
            if isinstance(item, dict):
                impl = item['impl']
                if impl and callable(impl):
                    result[name] = impl()
                else:
                    result[name] = impl
            else:
                result[name] = item
        return result

    def get_used_macro_maps(self, strings):
        used_names = set()
        for string in strings:
            names = self.get_using_macro_names(string)
            used_names.update(set(names))
        return self.get_macro_map(used_names)

    def get_using_macro_names(self, string):
        """
        获取字符串中包含的宏名称
        :return:
        """
        names = []
        for item in re.findall(self.template.pattern, string):
            name = item[1] or item[2]
            names.append(name)
        return names

    def apply_string(self, string):
        return self.template(string).safe_substitute(**self.macro_config)


def main():
    macro_template = MacroTemplate(default_macro_config)
    s1 = "today is ${today}. $today:2  $xx"
    s2 = "now is ${today}."
    maps = macro_template.get_used_macro_maps([s1, s2])

    print(macro_template.used_macro_maps)
    return


if __name__ == '__main__':
    main()
