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

    def __init__(self, name, custom_macro_map=None, **extra):
        self._validators = []
        self.extra = extra
        self.metrics = {}
        self._loader = None
        self.custom_macro_map = custom_macro_map or {}
        self.used_macro_map = {}
        self.name = name
        self.meta = {}

    def mount_data_loader(self, loader_cls, params: dict):
        self.meta['loader'] = {'loader_cls': loader_cls, 'params': params}

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
        loader_params = self.meta['loader']['params'] or {}
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

    def gen_metrics(self, data, validators_result):
        # self.metrics = data
        pass

    def run_validators(self, data, macro_template):
        result = []
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
                run_time=datetime.datetime.now(),
                params=validator_params,
            )
            validator_result.update(item)
            validator_result.update(validator_extra)
            result.append(validator_result)
        return result

    def run(self):
        run_time = datetime.datetime.now()
        macro_maps = self.get_macro_maps()
        macro_template = MacroTemplate(macro_maps)
        wt_name = macro_template.apply_string(self.name)
        loader_params = self.meta['loader']['params'] or {}
        loader_params = copy.deepcopy(loader_params)
        for k, v in loader_params.items():
            if isinstance(v, str):
                loader_params[k] = macro_template.apply_string(v)
        self._loader = self.meta['loader']['loader_cls'](**loader_params)
        data = self._loader.load()
        validators_result = self.run_validators(data, macro_template)
        self.gen_metrics(data, validators_result)
        result = dict(
            name=wt_name,
            success=True,
            run_time=run_time,
            macro_maps=macro_maps,
            metrics=self.metrics,
            validators_result=validators_result,
        )
        result.update(self.extra)
        return result


def main():
    import pprint
    from data_watchtower.services import save_run_log
    from data_watchtower.database import SessionLocal
    host = '39.108.123.230'
    user = 'uadmin'
    pwd = 'uxmc*123'
    db_name = "test"
    connection_string = f"mysql://{user}:{pwd}@{host}:3306/{db_name}"
    sql = ("SELECT `code`, `trading_day`,  `open`, `high`, `low`, `settle`, `close` FROM `t_eodprices` "
           "WHERE trading_day='${today}'   LIMIT ${n}")
    wt = Watchtower("日行情-${today}")
    wt.mount_data_loader(DatabaseLoader, dict(query=sql, connection=connection_string))
    wt.add_validator(ExpectColumnValuesToNotBeNull, dict(column='high'), vid=1)
    wt.add_validator(ExpectRowCountToBeBetween, dict(min_rows=50), vid=2)
    run_log = wt.run()
    pprint.pprint(run_log)
    with SessionLocal() as db:
        save_run_log(db, wt_id=1, run_log=run_log)


if __name__ == '__main__':
    """
    1. 实时获取数据加载器套件
    2. 添加数据处理器, 设置数据名称, 调用时机, 加载器, 以及加载器参数. 
    3. 为数据集添加 校验器
    """
    main()
