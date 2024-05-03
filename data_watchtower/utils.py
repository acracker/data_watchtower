#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json
import copy
import importlib
from string import Template

from attrs import asdict


def load_object(path):
    if not isinstance(path, str):
        if callable(path):
            return path
        else:
            raise TypeError("Unexpected argument type, expected string "
                            "or object, got: %s" % type(path))

    if ':' in path:
        module, obj_name = path.split(':', maxsplit=1)
    else:
        module, obj_name = path, None
    mod = importlib.import_module(module)
    if obj_name:
        try:
            obj = getattr(mod, obj_name)
            return obj
        except AttributeError:
            raise NameError(f"Module '{module}' doesn't define any object named '{obj_name}'")
    else:
        return mod


def to_snake(name):
    """
    转下划线命名
    :param name:
    :return:
    """
    pattern = r'(?<=[a-z])[A-Z]|(?<!^)[A-Z](?=[a-z])'
    name = re.sub(pattern, r'_\g<0>', name).lower()
    return name


def from_dict(cls, items):
    return cls(**items)


def to_dict(self):
    result = {}
    for k, v in asdict(self).items():
        if str(k).startswith('_'):
            continue
        result[k] = v
    return result


def spawn_validator_from_dict(item):
    cls_path = item.get('__class__')
    cls = load_object(cls_path)
    return cls.from_dict(item)


def spawn_data_loader_from_dict(item):
    item = item.copy()
    cls_path = item.pop('__class__')
    cls = load_object(cls_path)
    return cls.from_dict(item)


def get_string_values(data):
    result = []
    if isinstance(data, str):
        return [data]
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                result.extend(get_string_values(item))
            elif isinstance(item, list):
                result.extend(get_string_values(item))
    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                result.append(value)
            elif isinstance(value, list):
                result.extend(get_string_values(value))
            elif isinstance(value, dict):
                result.extend(get_string_values(value))
    return result


class StringTemplate(Template):
    idpattern = r'(?a:[_a-zA-Z][_:a-zA-Z0-9]*)'


class MacroTemplate(object):
    template = StringTemplate

    def __init__(self, macro_config):
        self.macro_config = copy.deepcopy(macro_config)
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

    def apply(self, value):
        """
        把字符串里面的模板替换掉。
        如果 value是字典， 会复制一个字段出来， 不会修改原字典数据
        :param value:
        :return:
        """
        if isinstance(value, str):
            return self.apply_string(value)
        elif isinstance(value, dict):
            result = {}
            for k, v in value.items():
                if isinstance(v, dict):
                    result[k] = self.apply(v)
                elif isinstance(v, str):
                    result[k] = self.apply_string(v)
                else:
                    result[k] = v
            return result
        else:
            return value


def json_dumps(obj):
    def _default_encoder(_obj):
        return str(_obj)

    if isinstance(obj, str):
        return obj
    return json.dumps(obj, default=_default_encoder, ensure_ascii=True)


def json_loads(data):
    if isinstance(data, str):
        return json.loads(data)
    else:
        return data


def dump_macro_map(macro_map):
    """
    把模板转换成字符串
    :param macro_map:
    :return:
    """

    pass


def f2():
    return 1


def main():
    def add():
        return 1

    import inspect
    return


if __name__ == '__main__':
    main()
