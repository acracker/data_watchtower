#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re


def to_snake(name):
    """
    转下划线命名
    :param name:
    :return:
    """
    pattern = r'(?<=[a-z])[A-Z]|(?<!^)[A-Z](?=[a-z])'
    name = re.sub(pattern, r'_\g<0>', name).lower()
    return name
