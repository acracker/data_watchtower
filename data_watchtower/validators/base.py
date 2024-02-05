#!/usr/bin/env python
# -*- coding: utf-8 -*-
from data_watchtower.utils.msic import to_snake


class Validator(object):
    _validator_name = None

    def __init__(self):
        self._data_loader = None
        self._data = None
        self.success = None
        self.metrics = None

    def set_data_loader(self, loader):
        self._data_loader = loader

    @classmethod
    def get_validator_name(cls):
        if cls._validator_name is not None:
            return cls._validator_name
        else:
            return to_snake(cls.__name__)

    @property
    def data(self):
        if self._data is None:
            self._data = self._data_loader.load()
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    def _validation(self):
        raise NotImplementedError

    def metrics_to_json_schema(self):
        pass

    def validation(self):
        result = self._validation()
        self.success = result['success']
        self.metrics = result['metrics']
        return result


class ExpectColumnValuesToNotBeNull(Validator):

    def __init__(self, column):
        super().__init__()
        self.column = column

    def _validation(self):
        df = self.data
        temp = df.filter(df[self.column].is_null())
        result = dict(
            success=len(temp) == 0,
            metrics=dict(
                null_rows=len(temp),
                total_rows=len(df),
            )
        )
        return result


class ExpectRowCountToBeBetween(Validator):

    def __init__(self, min_rows=None, max_rows=None):
        super().__init__()
        self.min_rows = min_rows
        self.max_rows = max_rows

    def _validation(self):
        rows = len(self.data)
        success = True
        if self.min_rows is not None:
            if rows < self.min_rows:
                success = False
        if self.max_rows is not None:
            if rows > self.max_rows:
                success = False
        result = dict(
            success=success,
            metrics=dict(
                rows=rows,
            )
        )
        return result
