#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import copy
import logging
import polars as pl
import datetime
from data_watchtower.utils.macro import MacroTemplate, default_macro_config
from data_watchtower.validators.base import *


class DataLoader(object):
    _validator_directory = []

    def __init__(self):
        self._validators = []
        self._validator_cls_maps = {}

    def _load(self, **kwargs):
        raise NotImplementedError

    def load(self):
        data = self._load()
        return data

    def add_validator(self, validator):
        self._validators.append(validator)

    def dump(self) -> dict:
        """
        用于序列化加载器
        :return:
        """
        obj = dict(
            cls="%s:%s" % (self.__class__.__module__, self.__class__.__name__),
        )
        return obj

    def get_validator_directory(self):
        _validator_directory = []
        _validator_directory.extend(self._validator_directory)
        path = os.getenv("_validator_directory")
        if path and os.path.isdir(path):
            _validator_directory.append(path)
        return _validator_directory

    def _load_validator_map(self):

        for fp in self.get_validator_directory():
            pass
        validators = [ExpectColumnValuesToNotBeNull, ExpectRowCountToBeBetween]
        result = {}
        for v in validators:
            result[v.get_validator_name()] = v
        return result

    def mount_validator_to_inst(self):
        for k, v in self._load_validator_map().items():
            setattr(self, k, v)

    # def __getattr__(self, item):
    #     validator_map = self._load_validator_map()
    #
    #     if item not in validator_map:
    #         raise ValueError
    #     validator = validator_map[item]
    #     return validator


class DatabaseLoader(DataLoader):
    def __init__(self, query: str, connection: str):
        super().__init__()
        self.query = query
        self.connection = connection

    def _load(self):
        return pl.read_database_uri(self.query, self.connection)

    def dump(self) -> dict:
        result = super().dump()
        result['connection'] = self.connection
        result['query'] = self.query
        return result
