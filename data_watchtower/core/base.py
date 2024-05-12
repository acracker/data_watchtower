#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import logging
from functools import lru_cache
import polars as pl
import pandas as pd
from attrs import define, field, NOTHING
from apischema import settings, schema
from apischema.json_schema import deserialization_schema
from apischema.objects import ObjectField

from ..utils import to_dict, from_dict, to_snake, get_subclasses, load_subclasses

logger = logging.getLogger(__name__)

prev_default_object_fields = settings.default_object_fields


def attrs_fields(cls: type):
    if hasattr(cls, "__attrs_attrs__"):
        return [
            ObjectField(
                a.name, a.type, required=a.default == NOTHING, default=a.default,
                metadata=schema(**(a.metadata or {})),
            )
            for a in getattr(cls, "__attrs_attrs__")
        ]
    else:
        return prev_default_object_fields(cls)


def field_base_schema(tp, name: str, alias: str):
    return schema(title=alias)


settings.base_schema.field = field_base_schema
settings.default_object_fields = attrs_fields


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
            logger.error("Data loading failure. DataLoader: %s" % self.__class__.__name__)
            raise

    @classmethod
    def to_schema(cls):
        return deserialization_schema(cls)


@lru_cache()
def get_get_registered_data_loader_maps():
    custom_path = ["dw_custom.data_loaders"]
    subclasses = get_subclasses(DataLoader)
    try:
        custom_subclasses = load_subclasses(custom_path, DataLoader)
    except ModuleNotFoundError:
        custom_subclasses = []
    result = {}
    for cls in (subclasses + custom_subclasses):
        cls_name = cls.__name__
        if cls_name in result:
            raise ValueError("Duplicate data loader name: %s" % cls_name)
        else:
            result[cls.__name__] = cls
    return result


def get_registered_data_loaders():
    result = get_get_registered_data_loader_maps()
    return list(result.values())


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

    @classmethod
    def from_params(cls, **kwargs):
        params = cls.Params(**kwargs)
        return cls(params)

    def params_to_dict(self):
        return to_dict(self.params)

    def _validation(self):
        raise NotImplementedError

    def validation(self):
        result = self._validation()
        return result

    def set_data(self, data):
        if isinstance(data, pl.DataFrame):
            self._data = data
        elif isinstance(data, pd.DataFrame):
            self._data = pl.from_pandas(data)
        else:
            self._data = pl.DataFrame(data)

    def get_data(self):
        if isinstance(self._data, pl.DataFrame):
            return self._data
        else:
            raise TypeError("data type error, must be pl.DataFrame. type:%s" % type(self._data))

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
