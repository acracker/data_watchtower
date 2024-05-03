#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
from attrs import define, field
from ..utils import to_dict, from_dict, to_snake


class BaseBean:
    def to_dict(self):
        result = to_dict(self)
        result['__class__'] = "%s:%s" % (self.__class__.__module__, self.__class__.__name__)
        return result

    @classmethod
    def from_dict(cls, items):
        return from_dict(cls, items)

    @classmethod
    def module_path(cls):
        return "%s:%s" % (cls.__module__, cls.__name__)


@define()
class DataLoader(BaseBean):

    def _load(self):
        raise NotImplementedError

    def load(self):
        try:
            return self._load()
        except Exception as e:
            raise


@define()
class ValidationResult(BaseBean):
    success = field(default=None, type=bool)
    metrics = field(factory=dict, type=dict, repr=False)
    extra = field(factory=dict, type=dict, repr=False)
    run_time = field(factory=lambda: datetime.datetime.now(), repr=lambda x: str(x))
    name = field(type=str, init=False)
    params = field(init=False)


class Validator(object):
    @define()
    class Params:
        pass

    def __init__(self, params: Params):
        self._data = None
        self.result = None
        self.params = params

    def params_to_dict(self):
        return to_dict(self.params)

    def _validation(self):
        raise NotImplementedError

    def validation(self):
        result = self._validation()
        return result

    def set_data(self, data):
        self._data = data

    def get_data(self):
        return self._data

    @classmethod
    def get_validator_name(cls):
        return to_snake(cls.__name__)

    @classmethod
    def module_path(cls):
        return "%s:%s" % (cls.__module__, cls.__name__)

    def to_dict(self):
        result = dict()
        result['params'] = to_dict(self.params)
        # result['params']['__class__'] = "%s:%s" % (self.params.__class__.__module__, self.params.__class__.__name__)
        result['__class__'] = "%s:%s" % (self.__class__.__module__, self.__class__.__name__)
        return result

    @classmethod
    def from_dict(cls, items: dict):
        # params = cls.Params(**items['params'])
        params = from_dict(cls.Params, items['params'])
        return cls(params)
