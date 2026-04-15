#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import datetime
import logging
from functools import lru_cache
import arrow
from attrs import define, field
from .base import Validator, ValidationResult

from ..utils import get_subclasses, load_subclasses, spawn_data_loader_from_dict, json_loads

CUSTOM_VALIDATOR_PATH = os.getenv("DW_CUSTOM_VALIDATOR_PATH", "dw_custom.validators")
logger = logging.getLogger(__name__)


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
        if isinstance(value, datetime.datetime):
            return value
        try:
            value = arrow.get(value).datetime.replace(tzinfo=None)
        except Exception as e:
            logger.warning("value_to_datetime error: %s", exc_info=e)
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
        if last_updated_time is None:
            return ValidationResult(
                success=False,
                metrics=dict(last_updated_time=None)
            )
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
            type=list, metadata={'help': 'A set of objects used for comparison.'},
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
            type=list, metadata={'help': 'A set of objects used for comparison.'},
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
            type=list, metadata={'help': 'A set of objects used for comparison.'},
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


class ExpectColumnValuesToBeInReferenceColumn(Validator):
    """
    检查当前数据源中某个字段的所有值，是否都存在于另一个数据源的某个字段中。
    常用于跨表引用完整性检查，例如：流水表的商品ID是否都在商品基本信息表中。

    如果两个数据源的字段名不同，使用 reference_column 指定参考数据源的字段名。
    参考数据源使用 reference_data_loader 配置，支持 JSON 字符串或字典，
    格式与普通 DataLoader 配置一致（包含 __class__ 和对应参数）。
    参考数据源的 DataLoader 可以配置 ttl_cache 来利用 DuckDB 缓存，避免重复加载大表。
    """

    @define()
    class Params:
        column = field(
            type=str,
            metadata={'help': '当前数据源的字段名'},
        )
        reference_data_loader = field(
            type=str,
            metadata={'help': '参考数据源的DataLoader配置（JSON字符串，包含__class__和对应参数）'},
        )
        reference_column = field(
            type=str,
            default=None,
            metadata={'help': '参考数据源的字段名，为空则与column相同'},
        )

    def __init__(self, params: Params):
        super().__init__(params)
        self.params = params

    def _validation(self):
        source_col = self.params.column
        ref_col = self.params.reference_column or source_col
        df = self.get_data()
        source_values = set(df[source_col].drop_nulls().to_list())

        ref_loader_meta = json_loads(self.params.reference_data_loader)
        cls_path = ref_loader_meta.get('__class__', '')
        from .data_loaders import get_registered_data_loader_maps
        allowed = {cls.module_path() for cls in get_registered_data_loader_maps().values()}
        if cls_path not in allowed:
            raise ValueError("reference_data_loader __class__ not allowed: %s" % cls_path)

        ref_loader = spawn_data_loader_from_dict(ref_loader_meta)
        ref_df = ref_loader.load()
        ref_values = set(ref_df[ref_col].drop_nulls().to_list())

        missing_values = sorted(source_values - ref_values, key=str)
        return ValidationResult(
            success=len(missing_values) == 0,
            metrics=dict(
                missing_count=len(missing_values),
                missing_values=missing_values[:100],
                source_distinct_count=len(source_values),
                ref_distinct_count=len(ref_values),
            )
        )
