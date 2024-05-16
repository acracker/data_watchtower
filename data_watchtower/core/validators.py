#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import datetime
from functools import lru_cache
from attrs import define, field
from .base import Validator, ValidationResult

from ..utils import get_subclasses, load_subclasses

CUSTOM_VALIDATOR_PATH = os.getenv("DW_CUSTOM_VALIDATOR_PATH", "dw_custom.data_loaders")


@lru_cache()
def get_registered_validator_maps():
    custom_path = CUSTOM_VALIDATOR_PATH.split(";")
    subclasses = get_subclasses(Validator)
    try:
        custom_subclasses = load_subclasses(custom_path, Validator)
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


def get_registered_validators():
    result = get_registered_validator_maps()
    return list(result.values())


class ExpectColumnValuesToNotBeNull(Validator):
    @define()
    class Params:
        column = field(type=str)

    def __init__(self, params: Params):
        super().__init__(params)
        self.params = params

    def _validation(self):
        df = self.get_data()
        temp = df.filter(df[self.params.column].is_null())
        return ValidationResult(
            success=len(temp) == 0,
            metrics=dict(
                null_rows=len(temp),
                total_rows=len(df),
            )
        )


class ExpectColumnRecentlyUpdated(Validator):
    """
    期望最近更新过. 注意是与当前时间比较的
    """

    @define()
    class Params:
        update_time_column = field(type=str, metadata={'help': 'update_time字段名称'})
        days = field(default=0, type=int)
        hours = field(default=0, type=int)

    def __init__(self, params: Params):
        super().__init__(params)
        self.params = params

    @staticmethod
    def value_to_datetime(value):
        return value

    def _validation(self):
        df = self.get_data()
        try:
            last_updated_time = df[self.params.update_time_column].max()
        except (IndexError, KeyError, ValueError):
            return ValidationResult(
                success=False,
                metrics=dict(
                    last_updated_time=None,
                )
            )
        last_updated_time = self.value_to_datetime(last_updated_time)
        now = datetime.datetime.now()
        delta = datetime.timedelta(days=self.params.days, hours=self.params.hours)
        return ValidationResult(
            success=last_updated_time > now - delta,
            metrics=dict(
                last_updated_time=last_updated_time,
            )
        )


class ExpectColumnStdToBeBetween(Validator):
    """
    期望某个字段的标准差在某个范围
    """

    @define()
    class Params:
        column = field(type=str, metadata={'help': 'The column name'})
        min_value = field(default=None, type=float,
                          metadata={'help': 'The minimum value for the column standard deviation.'})
        max_value = field(default=None, type=float,
                          metadata={'help': 'The maximum value for the column standard deviation.'})

    def __init__(self, params: Params):
        super().__init__(params)
        self.params = params

    def _validation(self):
        df = self.get_data()
        column = self.params.column
        min_value = self.params.min_value
        max_value = self.params.max_value
        std = round(df[column].std(), 2)
        mean = round(df[column].mean(), 2)
        success = True
        if min_value is not None or max_value is not None:
            min_value = min_value or -float('inf')
            max_value = max_value or float('inf')
            success = min_value < std < max_value

        result = ValidationResult(
            success=success,
            metrics=dict(
                values=list(df[column]),
                std=std,
                mean=mean,
            )
        )
        return result


class ExpectColumnMeanToBeBetween(Validator):
    """
    指定字段平均值在某个范围
    """

    @define()
    class Params:
        column = field(type=str, metadata={'help': 'The column name'})
        min_value = field(default=None, type=float, metadata={'help': 'The minimum value for the column mean.'})
        max_value = field(default=None, type=float, metadata={'help': 'The maximum value for the column mean.'})

    def __init__(self, params: Params):
        super().__init__(params)
        self.params = params

    def _validation(self):
        df = self.get_data()
        column = self.params.column
        min_value = self.params.min_value
        max_value = self.params.max_value
        mean = round(df[column].mean(), 2)
        std = round(df[column].std(), 2)
        success = True
        if min_value is not None or max_value is not None:
            min_value = min_value or -float('inf')
            max_value = max_value or float('inf')
            success = min_value < mean < max_value

        result = ValidationResult(
            success=success,
            metrics=dict(
                values=list(df[column]),
                mean=mean,
                std=std,
            )
        )

        return result


class ExpectColumnNullRatioToBeBetween(Validator):
    """
    指定字段的空值比率
    """

    @define()
    class Params:
        column = field(type=str, metadata={'help': 'The column name'})
        min_value = field(default=None, type=float, metadata={'help': 'The minimum value for the column null ratio.'})
        max_value = field(default=None, type=float, metadata={'help': 'The maximum value for the column null ratio.'})

    def __init__(self, params: Params):
        super().__init__(params)
        self.params = params

    def _validation(self):
        df = self.get_data()
        column = self.params.column
        min_value = self.params.min_value
        max_value = self.params.max_value
        total_rows = len(df)
        null_rows = df[column].is_null().sum()
        if total_rows > 0:
            null_ratio = round(null_rows / total_rows, 3)
        else:
            null_ratio = 0
        success = True
        if min_value is not None or max_value is not None:
            min_value = min_value or -float('inf')
            max_value = max_value or float('inf')
            success = min_value < null_ratio < max_value

        result = ValidationResult(
            success=success,
            metrics=dict(
                null_ratio=null_ratio,
                total_rows=total_rows,
                null_rows=null_rows,
            )
        )

        return result


class ExpectRowCountToBeBetween(Validator):
    """
    Expect the number of rows to be between two values.

    """

    @define()
    class Params:
        min_value = field(default=None, type=float, metadata={'help': 'The minimum number of rows, inclusive'})
        max_value = field(default=None, type=float, metadata={'help': 'The maximum number of rows, inclusive.'})

    def __init__(self, params: Params):
        super().__init__(params)
        self.params = params

    def _validation(self):
        df = self.get_data()
        min_value = self.params.min_value
        max_value = self.params.max_value
        total_rows = len(df)
        success = True
        if min_value is not None or max_value is not None:
            min_value = min_value or -float('inf')
            max_value = max_value or float('inf')
            success = min_value < total_rows < max_value

        result = ValidationResult(
            success=success,
            metrics=dict(
                total_rows=total_rows,
            )
        )

        return result


class ExpectColumnDistinctValuesToContainSet(Validator):
    """
    Expect the set of distinct column values to contain a given set.
    """

    @define()
    class Params:
        column = field(type=str, metadata={'help': 'The column name'})
        value_set = field(
            type=set, metadata={'help': 'A set of objects used for comparison.'},
            converter=lambda x: set(x),
        )

    def __init__(self, params: Params):
        super().__init__(params)
        self.params = params

    def _validation(self):
        df = self.get_data()
        column = self.params.column
        value_set = self.params.value_set
        column_values = set(df[column])
        success = column_values >= value_set
        laced_values = sorted(value_set - column_values)
        result = ValidationResult(
            success=success,
            metrics=dict(
                laced_values=laced_values,
            )
        )
        return result


class ExpectColumnDistinctValuesToEqualSet(Validator):
    """
    Expect the set of distinct column values to equal a given set.
    """

    @define()
    class Params:
        column = field(type=str, metadata={'help': 'The column name'})
        value_set = field(
            type=set, metadata={'help': 'A set of objects used for comparison.'},
            converter=lambda x: set(x),
        )

    def __init__(self, params: Params):
        super().__init__(params)
        self.params = params

    def _validation(self):
        df = self.get_data()
        column = self.params.column
        value_set = self.params.value_set
        column_values = set(df[column])
        success = column_values == value_set
        column_laced_values = sorted(value_set - column_values)
        param_laced_values = sorted(column_values - value_set)
        result = ValidationResult(
            success=success,
            metrics=dict(
                column_laced_values=column_laced_values,
                param_laced_values=param_laced_values,
            )
        )
        return result


class ExpectColumnDistinctValuesToBeInSet(Validator):
    """
    Expect the set of distinct column values to be contained by a given set.
    """

    @define()
    class Params:
        column = field(type=str, metadata={'help': 'The column name'})
        value_set = field(
            type=set, metadata={'help': 'A set of objects used for comparison.'},
            converter=lambda x: set(x),
        )

    def __init__(self, params: Params):
        super().__init__(params)
        self.params = params

    def _validation(self):
        df = self.get_data()
        column = self.params.column
        value_set = self.params.value_set
        column_values = set(df[column])
        success = column_values <= value_set
        # 指定字段的值比参数多的数据
        excrescent_values = sorted(column_values - value_set)
        result = ValidationResult(
            success=success,
            metrics=dict(
                excrescent_values=excrescent_values,
            )
        )
        return result
