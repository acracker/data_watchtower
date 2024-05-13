#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
import datetime

from data_watchtower.utils import (spawn_data_loader_from_dict, spawn_validator_from_dict,
                                   get_string_values, MacroTemplate, json_loads, json_dumps)
from data_watchtower.core.macro import DEFAULT_MACRO_CONFIG


class Watchtower(object):
    def __init__(self, name, data_loader, custom_macro_map=None, **params):
        """

        :param name:
        :param data_loader:
        :param params: schedule, validator_success_method, success_method
        """
        custom_macro_map = custom_macro_map or {}  # 只是运行的时候使用,不会保存
        self.params = params
        self._data_loader = data_loader  # 原本的loader,参数可能包含宏
        self._data_loader_meta = data_loader.to_dict()  # 原本的loader,参数可能包含宏
        self._validators = []
        self._validators_meta = []
        self.name = name
        self.metrics = {}
        self.macro_map = copy.deepcopy(DEFAULT_MACRO_CONFIG)
        self.macro_map.update(custom_macro_map)
        self.macro_template = MacroTemplate(self.macro_map)
        # 回填默认值
        self.params['schedule'] = self.schedule
        self.params['validator_success_method'] = self.validator_success_method
        self.params['success_method'] = self.success_method

    @property
    def schedule(self):
        return self.params.get('schedule')

    @property
    def validator_success_method(self):
        return self.params.get('validator_success_method', 'all')

    @property
    def success_method(self):
        success_method = self.params.get('success_method')
        if success_method is None:
            if len(self.macro_template.get_used_macro_maps([self.name])) > 0:
                return 'all'
            else:
                return 'last'
        else:
            return success_method

    def set_custom_macro(self, **custom_macro_map):
        self.macro_map.update(custom_macro_map)
        self.macro_template.macro_config.update(custom_macro_map)

    @classmethod
    def from_dict(cls, data):
        data_loader = spawn_data_loader_from_dict(data.get('data_loader', {}))
        params = data.get('params', {})
        inst = cls(name=data['name'], data_loader=data_loader, **params)
        for validator in data.get('validators', []):
            inst.add_validator(spawn_validator_from_dict(validator))
        return inst

    def to_dict(self):
        params = {

        }
        result = dict(
            name=self.name,
            data_loader=json_dumps(self.get_loader_meta()),
            validators=json_dumps(self.get_validator_meta()),
            params=json_dumps(self.params),
        )
        return result

    def add_validator(self, validator):
        item = validator.to_dict()
        self._validators_meta.append(item)

    def get_validator_meta(self):
        return self._validators_meta

    def get_loader_meta(self):
        return self._data_loader_meta

    @staticmethod
    def get_params_strings(params):
        return params

    def get_macro_maps(self):
        strings = [self.name]
        strings.extend(get_string_values(self._data_loader_meta))
        strings.extend(get_string_values(self._validators_meta))
        return self.macro_template.get_used_macro_maps(strings)

    def gen_metrics(self, data, validators_result):
        # self.metrics = data
        pass

    def compute_success(self, validators_result):
        success_list = [item.success for item in validators_result]
        if self.validator_success_method == 'all':
            success_method = all
        elif self.validator_success_method == 'any':
            success_method = any
        else:
            raise ValueError('validator_success_method must be any or all.')
        return success_method(success_list)

    def run_validators(self, data, macro_template):
        result = []
        for item in self._validators_meta:
            validator_item = {}
            for k, v in item.items():
                if k == 'params':
                    validator_item['params'] = macro_template.apply(v)
                else:
                    validator_item[k] = v

            validator = spawn_validator_from_dict(validator_item)
            validator.set_data(data)
            validator_result = validator.validation()
            validator_result.params = validator_item['params']
            validator_result.name = validator.get_validator_name()
            result.append(validator_result)
        return result

    def run(self):
        run_time = datetime.datetime.now()
        macro_maps = self.get_macro_maps()
        macro_template = MacroTemplate(macro_maps)
        wt_name = macro_template.apply_string(self.name)
        # self.metrics['raw_name'] = self.name
        # self.metrics['name'] = wt_name
        data_loader_meta = {}
        for k, v in self._data_loader_meta.items():
            if isinstance(v, str):
                data_loader_meta[k] = macro_template.apply_string(v)
            else:
                data_loader_meta[k] = v
        self._data_loader = spawn_data_loader_from_dict(data_loader_meta)
        data = self._data_loader.load()
        validators_result = self.run_validators(data, macro_template)
        self.gen_metrics(data, validators_result)
        success = self.compute_success(validators_result)
        result = dict(
            name=wt_name,
            success=success,
            run_time=run_time,
            macro_maps=macro_maps,
            metrics=self.metrics,
            validators_result=validators_result,
        )
        return result

    @classmethod
    def module_path(cls):
        return "%s:%s" % (cls.__module__, cls.__name__)


def main():
    pass


if __name__ == '__main__':
    main()
