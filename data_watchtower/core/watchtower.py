#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import copy
import logging
import polars as pl
import datetime

from data_watchtower.data_loaders.base import DatabaseLoader
from data_watchtower.validators.base import ExpectColumnValuesToNotBeNull, ExpectRowCountToBeBetween
from data_watchtower.utils.macro import MacroTemplate, default_macro_config

logger = logging.getLogger(__name__)


class Watchtower(object):

    def __init__(self, name, custom_macro_map=None):
        self._validators = []
        self._loader = None
        self.custom_macro_map = custom_macro_map or {}
        self.used_macro_map = {}
        self.name = name
        self.meta = {}

    def mount_data_loader(self, loder_cls, params: dict):
        self.meta['loder'] = {'loder_cls': loder_cls, 'params': params}

    def add_validator(self, validator_cls, params: dict, **extra):
        self.meta.setdefault('validators', []).append(
            {'validator_cls': validator_cls, 'params': params, 'extra': extra}
        )

    def macro_config(self):
        macro_config = copy.deepcopy(default_macro_config)
        macro_config.update(self.custom_macro_map)
        return macro_config

    def get_macro_maps(self):
        strings = [self.name]
        loader_params = self.meta['loder']['params'] or {}
        for k, v in loader_params.items():
            if isinstance(v, str):
                strings.append(v)
        for item in self.meta['validators']:
            params = item['params'] or {}
            for k, v in params.items():
                if isinstance(v, str):
                    strings.append(v)

        macro_template = MacroTemplate(self.macro_config())
        return macro_template.get_used_macro_maps(strings)

    def run(self):
        macro_maps = self.get_macro_maps()
        macro_template = MacroTemplate(macro_maps)

        loader_params = self.meta['loder']['params'] or {}
        loader_params = copy.deepcopy(loader_params)
        for k, v in loader_params.items():
            if isinstance(v, str):
                loader_params[k] = macro_template.apply_string(v)

        self._loader = self.meta['loder']['loder_cls'](**loader_params)

        data = self._loader.load()
        validators_result = []
        for item in self.meta['validators']:
            validator_cls = item['validator_cls']
            validator_params = item['params']
            validator_extra = item['extra']
            validator_params = copy.deepcopy(validator_params)
            for k, v in validator_params.items():
                if isinstance(v, str):
                    validator_params[k] = macro_template.apply_string(v)
            validator = validator_cls(**validator_params)
            validator.data = data
            validator_result = validator.validation()
            item = dict(
                validator=validator.get_validator_name(),
                datetime=datetime.datetime.now(),
                params=validator_params,
            )
            validator_result.update(item)
            validator_result.update(validator_extra)
            validators_result.append(validator_result)
        result = dict(
            macro_maps=macro_maps,
            validators_result=validators_result,
        )
        return result


def main():
    import pprint
    host = '39.108.123.230'
    user = 'uadmin'
    pwd = 'uxmc*123'
    db_name = "test"
    connection_string = f"mysql://{user}:{pwd}@{host}:3306/{db_name}"
    sql = ("SELECT `code`, `trading_day`,  `open`, `high`, `low`, `settle`, `close` FROM `t_eodprices` "
           "WHERE trading_day='${today}'   LIMIT ${n}")
    data_handler = Watchtower("日行情-${today}")
    data_handler.mount_data_loader(DatabaseLoader, dict(query=sql, connection=connection_string))
    data_handler.add_validator(ExpectColumnValuesToNotBeNull, dict(column='high'), vid=1)
    data_handler.add_validator(ExpectRowCountToBeBetween, dict(min_rows=50), vid=2)
    pprint.pprint(data_handler.run())


if __name__ == '__main__':
    """
    1. 实时获取数据加载器套件
    2. 添加数据处理器, 设置数据名称, 调用时机, 加载器, 以及加载器参数. 
    3. 为数据集添加 校验器
    """
    main()
