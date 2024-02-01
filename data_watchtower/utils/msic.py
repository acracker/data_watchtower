#!/usr/bin/env python
# -*- coding: utf-8 -*-
import inspect
import re
from importlib import import_module
from pkgutil import iter_modules


def to_snake(name):
    """
    转下划线命名
    :param name:
    :return:
    """
    pattern = r'(?<=[a-z])[A-Z]|(?<!^)[A-Z](?=[a-z])'
    name = re.sub(pattern, r'_\g<0>', name).lower()
    return name


def load_object(path):
    if not isinstance(path, str):
        if callable(path):
            return path
        else:
            raise TypeError("Unexpected argument type, expected string "
                            "or object, got: %s" % type(path))

    try:
        dot = path.rindex('.')
    except ValueError:
        raise ValueError(f"Error loading object '{path}': not a full path")

    module, name = path[:dot], path[dot + 1:]
    mod = import_module(module)

    try:
        obj = getattr(mod, name)
    except AttributeError:
        raise NameError(f"Module '{module}' doesn't define any object named '{name}'")

    return obj


def walk_modules(path):
    mods = []
    mod = import_module(path)
    mods.append(mod)
    if hasattr(mod, '__path__'):
        for _, sub_path, is_pkg in iter_modules(mod.__path__):
            full_path = path + '.' + sub_path
            if is_pkg:
                mods += walk_modules(full_path)
            else:
                sub_mod = import_module(full_path)
                mods.append(sub_mod)
    return mods


def load_sub_class(root_modules, base_class):
    result = []
    for root_module in root_modules:
        for m in walk_modules(root_module):
            for obj in vars(m).values():
                if inspect.isclass(obj) and issubclass(obj, base_class) and obj.__module__ == m.__name__:
                    result.append(obj)
    return result
