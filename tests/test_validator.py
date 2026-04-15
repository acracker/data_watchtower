#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import pytest
import polars as pl
from data_watchtower import ExpectColumnValuesToNotBeNull, ExpectColumnRecentlyUpdated, \
    ExpectColumnStdToBeBetween, ExpectColumnMeanToBeBetween, ExpectColumnNullRatioToBeBetween, \
    ExpectRowCountToBeBetween, ExpectColumnDistinctValuesToContainSet, ExpectColumnDistinctValuesToEqualSet, \
    ExpectColumnDistinctValuesToBeInSet


# 定义测试类
class TestValidators:
    # 定义测试用例
    def test_expect_column_values_to_not_be_null(self):
        # 创建需要的测试数据
        data = {
            'column1': [1, 2, 3, 4, 5],
            'column2': ['a', 'b', 'c', 'd', 'e'],
            'column3': [True, False, True, False, True]
        }
        df = pl.DataFrame(data)

        # 创建验证器实例
        validator = ExpectColumnValuesToNotBeNull(ExpectColumnValuesToNotBeNull.Params(column='column1'))
        validator.set_data(df)
        # 执行验证
        result = validator.validation()
        # 断言验证结果是否符合预期
        assert result.success
        assert result.metrics['null_rows'] == 0
        assert result.metrics['total_rows'] == 5

    def test_expect_column_recently_updated(self):
        data = {
            'column1': [1, 2, 3, 4, 5],
            'update_time': [
                datetime.now() - timedelta(days=10),
                datetime.now() - timedelta(days=5), datetime.now() - timedelta(days=3),
                datetime.now() - timedelta(days=1), datetime.now() - timedelta(hours=10),
            ]
        }
        df = pl.DataFrame(data)
        validator = ExpectColumnRecentlyUpdated(None)
        validator.set_data(df)

        params = ExpectColumnRecentlyUpdated.Params(
            update_time_column='update_time',
            hours=12
        )
        validator.params = params
        result = validator.validation()
        assert result.success is True
        assert result.metrics['last_updated_time'] + timedelta(minutes=2) >= datetime.now() - timedelta(hours=10)

        params = ExpectColumnRecentlyUpdated.Params(
            update_time_column='update_time',
            days=1
        )
        validator.params = params
        result = validator.validation()
        assert result.success is True
        assert result.metrics['last_updated_time'] + timedelta(minutes=2) >= datetime.now() - timedelta(hours=10)

        params = ExpectColumnRecentlyUpdated.Params(
            update_time_column='update_time',
            hours=1
        )
        validator.params = params
        result = validator.validation()
        assert result.success is False
        assert result.metrics['last_updated_time'] + timedelta(minutes=2) >= datetime.now() - timedelta(hours=10)

    def test_expect_column_std_to_be_between(self):
        # 创建需要的测试数据
        data = {
            'column1': [1, 2, 3, 4, 5],
            'column2': [10, 20, 30, 40, 50]
        }
        df = pl.DataFrame(data)

        # 创建验证器实例
        validator = ExpectColumnStdToBeBetween(
            ExpectColumnStdToBeBetween.Params(column='column1', min_value=1, max_value=2))
        validator.set_data(df)
        # 执行验证
        result = validator.validation()
        # 断言验证结果是否符合预期
        assert result.success
        assert round(result.metrics['std'], 2) == 1.58
        assert result.metrics['mean'] == 3

    def test_expect_column_mean_to_be_between(self):
        # 创建需要的测试数据
        data = {
            'column1': [1, 2, 3, 4, 5],
            'column2': [10, 20, 30, 40, 50]
        }
        df = pl.DataFrame(data)

        # 创建验证器实例
        validator = ExpectColumnMeanToBeBetween(
            ExpectColumnMeanToBeBetween.Params(column='column2', min_value=20, max_value=40))
        validator.set_data(df)
        # 执行验证
        result = validator.validation()
        # 断言验证结果是否符合预期
        assert result.success
        assert result.metrics['mean'] == 30
        assert round(result.metrics['std'], 2) == 15.81

    def test_expect_column_null_ratio_to_be_between(self):
        # 创建需要的测试数据
        data = {
            'column1': [1, 2, 3, 4, 5],
            'column2': ['a', None, 'c', None, 'e']
        }
        df = pl.DataFrame(data)

        # 创建验证器实例
        validator = ExpectColumnNullRatioToBeBetween(
            ExpectColumnNullRatioToBeBetween.Params(column='column2', min_value=0.2, max_value=0.4))
        validator.set_data(df)
        # 执行验证
        result = validator.validation()
        # 断言验证结果是否符合预期
        assert result.success is False
        assert result.metrics['null_ratio'] == 0.4
        assert result.metrics['total_rows'] == 5
        assert result.metrics['null_rows'] == 2

    def test_expect_row_count_to_be_between(self):
        # 创建需要的测试数据
        data = {
            'column1': [1, 2, 3, 4, 5],
            'column2': ['a', 'b', 'c', 'd', 'e']
        }
        df = pl.DataFrame(data)

        # 创建验证器实例
        validator = ExpectRowCountToBeBetween(ExpectRowCountToBeBetween.Params(min_value=3, max_value=7))
        validator.set_data(df)
        # 执行验证
        result = validator.validation()
        # 断言验证结果是否符合预期
        assert result.success
        assert result.metrics['total_rows'] == 5

    def test_expect_column_distinct_values_to_contain_set(self):
        # 创建需要的测试数据
        data = {
            'column1': [1, 2, 3, 4, 5],
            'column2': ['a', 'b', 'c', 'd', 'e']
        }
        df = pl.DataFrame(data)

        # 创建验证器实例
        validator = ExpectColumnDistinctValuesToContainSet(
            ExpectColumnDistinctValuesToContainSet.Params(column='column2', value_set={'b', 'c', 'e'}))
        validator.set_data(df)
        # 执行验证
        result = validator.validation()
        # 断言验证结果是否符合预期
        assert result.success
        assert len(result.metrics['laced_values']) == 0

    def test_expect_column_distinct_values_to_equal_set(self):
        # 创建需要的测试数据
        data = {
            'column1': [1, 2, 3, 4, 5],
            'column2': ['a', 'b', 'c', 'd', 'e']
        }
        df = pl.DataFrame(data)

        # 创建验证器实例
        validator = ExpectColumnDistinctValuesToEqualSet(
            ExpectColumnDistinctValuesToEqualSet.Params(column='column2', value_set={'a', 'b', 'c', 'd', 'e'}))
        validator.set_data(df)
        # 执行验证
        result = validator.validation()
        # 断言验证结果是否符合预期
        assert result.success
        assert len(result.metrics['column_laced_values']) == 0
        assert len(result.metrics['param_laced_values']) == 0

    def test_expect_column_distinct_values_to_be_in_set(self):
        # 创建需要的测试数据
        data = {
            'column1': [1, 2, 3, 4, 5],
            'column2': ['a', 'b', 'c', 'd', 'e']
        }
        df = pl.DataFrame(data)

        # 创建验证器实例
        validator = ExpectColumnDistinctValuesToBeInSet(
            ExpectColumnDistinctValuesToBeInSet.Params(column='column2', value_set={'a', 'b', 'd', 'f'}))
        validator.set_data(df)
        # 执行验证
        result = validator.validation()
        # 断言验证结果是否符合预期
        assert result.success is False
        assert set(result.metrics['excrescent_values']) == {'c', 'e'}


class TestExpectColumnValuesToNotBeNull:
    def test_fail_when_has_nulls(self):
        df = pl.DataFrame({'a': [1, None, 3]})
        v = ExpectColumnValuesToNotBeNull(ExpectColumnValuesToNotBeNull.Params(column='a'))
        v.set_data(df)
        result = v.validation()
        assert result.success is False
        assert result.metrics['null_rows'] == 1
        assert result.metrics['total_rows'] == 3

    def test_all_null(self):
        df = pl.DataFrame({'a': [None, None]})
        v = ExpectColumnValuesToNotBeNull(ExpectColumnValuesToNotBeNull.Params(column='a'))
        v.set_data(df)
        result = v.validation()
        assert result.success is False
        assert result.metrics['null_rows'] == 2


class TestExpectColumnRecentlyUpdated:
    def test_empty_dataframe_returns_false(self):
        df = pl.DataFrame({'update_time': []}).cast({'update_time': pl.Datetime})
        v = ExpectColumnRecentlyUpdated(
            ExpectColumnRecentlyUpdated.Params(update_time_column='update_time', hours=1)
        )
        v.set_data(df)
        result = v.validation()
        assert result.success is False
        assert result.metrics['last_updated_time'] is None

    def test_exactly_on_boundary_fails(self):
        # 最大值恰好等于 now - delta，应该失败（严格大于）
        from datetime import datetime, timedelta
        old_time = datetime.now() - timedelta(hours=2)
        df = pl.DataFrame({'ts': [old_time]})
        v = ExpectColumnRecentlyUpdated(
            ExpectColumnRecentlyUpdated.Params(update_time_column='ts', hours=1)
        )
        v.set_data(df)
        result = v.validation()
        assert result.success is False


class TestExpectRowCountToBeBetween:
    def test_fail_below_min(self):
        df = pl.DataFrame({'a': [1, 2]})
        v = ExpectRowCountToBeBetween(ExpectRowCountToBeBetween.Params(min_value=5, max_value=10))
        v.set_data(df)
        assert v.validation().success is False

    def test_fail_above_max(self):
        df = pl.DataFrame({'a': list(range(20))})
        v = ExpectRowCountToBeBetween(ExpectRowCountToBeBetween.Params(min_value=1, max_value=10))
        v.set_data(df)
        assert v.validation().success is False

    def test_no_bounds_always_success(self):
        df = pl.DataFrame({'a': [1]})
        v = ExpectRowCountToBeBetween(ExpectRowCountToBeBetween.Params())
        v.set_data(df)
        assert v.validation().success is True

    def test_boundary_exclusive(self):
        # min_value=5, max_value=10, row_count=5 → 不满足 5 < 5
        df = pl.DataFrame({'a': list(range(5))})
        v = ExpectRowCountToBeBetween(ExpectRowCountToBeBetween.Params(min_value=5, max_value=10))
        v.set_data(df)
        assert v.validation().success is False


class TestExpectColumnMeanToBeBetween:
    def test_fail_mean_out_of_range(self):
        df = pl.DataFrame({'v': [100, 200, 300]})
        v = ExpectColumnMeanToBeBetween(
            ExpectColumnMeanToBeBetween.Params(column='v', min_value=1, max_value=10)
        )
        v.set_data(df)
        assert v.validation().success is False

    def test_only_min_bound(self):
        df = pl.DataFrame({'v': [5, 10, 15]})
        v = ExpectColumnMeanToBeBetween(
            ExpectColumnMeanToBeBetween.Params(column='v', min_value=5)
        )
        v.set_data(df)
        result = v.validation()
        assert result.success is True  # mean=10 > 5

    def test_only_max_bound(self):
        df = pl.DataFrame({'v': [1, 2, 3]})
        v = ExpectColumnMeanToBeBetween(
            ExpectColumnMeanToBeBetween.Params(column='v', max_value=1)
        )
        v.set_data(df)
        assert v.validation().success is False  # mean=2 > 1


class TestExpectColumnStdToBeBetween:
    def test_fail_std_out_of_range(self):
        df = pl.DataFrame({'v': [1, 1, 1, 1]})  # std=0
        v = ExpectColumnStdToBeBetween(
            ExpectColumnStdToBeBetween.Params(column='v', min_value=1, max_value=5)
        )
        v.set_data(df)
        assert v.validation().success is False

    def test_no_bounds_always_success(self):
        df = pl.DataFrame({'v': [1, 2, 3]})
        v = ExpectColumnStdToBeBetween(ExpectColumnStdToBeBetween.Params(column='v'))
        v.set_data(df)
        assert v.validation().success is True


class TestExpectColumnNullRatioToBeBetween:
    def test_empty_dataframe_ratio_zero(self):
        df = pl.DataFrame({'a': pl.Series([], dtype=pl.Utf8)})
        v = ExpectColumnNullRatioToBeBetween(
            ExpectColumnNullRatioToBeBetween.Params(column='a', min_value=0.1, max_value=0.5)
        )
        v.set_data(df)
        result = v.validation()
        assert result.metrics['null_ratio'] == 0
        assert result.success is False  # 0 不在 (0.1, 0.5)

    def test_no_nulls_ratio_zero(self):
        df = pl.DataFrame({'a': ['x', 'y', 'z']})
        v = ExpectColumnNullRatioToBeBetween(
            ExpectColumnNullRatioToBeBetween.Params(column='a', min_value=0.0, max_value=0.5)
        )
        v.set_data(df)
        result = v.validation()
        assert result.metrics['null_ratio'] == 0.0
        # min_value=0.0 是 falsy，源码替换为 -inf，所以 0.0 > -inf 成立
        assert result.success is True

    def test_all_null(self):
        df = pl.DataFrame({'a': [None, None, None]})
        v = ExpectColumnNullRatioToBeBetween(
            ExpectColumnNullRatioToBeBetween.Params(column='a', min_value=0.5, max_value=1.5)
        )
        v.set_data(df)
        result = v.validation()
        assert result.metrics['null_ratio'] == 1.0
        assert result.success is True


class TestExpectColumnDistinctValuesToContainSet:
    def test_fail_missing_values(self):
        df = pl.DataFrame({'c': ['a', 'b']})
        v = ExpectColumnDistinctValuesToContainSet(
            ExpectColumnDistinctValuesToContainSet.Params(column='c', value_set=['a', 'b', 'c'])
        )
        v.set_data(df)
        result = v.validation()
        assert result.success is False
        assert 'c' in result.metrics['laced_values']

    def test_superset_passes(self):
        df = pl.DataFrame({'c': ['a', 'b', 'c', 'd']})
        v = ExpectColumnDistinctValuesToContainSet(
            ExpectColumnDistinctValuesToContainSet.Params(column='c', value_set=['a', 'b'])
        )
        v.set_data(df)
        assert v.validation().success is True


class TestExpectColumnDistinctValuesToEqualSet:
    def test_fail_extra_values(self):
        df = pl.DataFrame({'c': ['a', 'b', 'c']})
        v = ExpectColumnDistinctValuesToEqualSet(
            ExpectColumnDistinctValuesToEqualSet.Params(column='c', value_set=['a', 'b'])
        )
        v.set_data(df)
        result = v.validation()
        assert result.success is False
        assert 'c' in result.metrics['param_laced_values']

    def test_fail_missing_values(self):
        df = pl.DataFrame({'c': ['a']})
        v = ExpectColumnDistinctValuesToEqualSet(
            ExpectColumnDistinctValuesToEqualSet.Params(column='c', value_set=['a', 'b'])
        )
        v.set_data(df)
        result = v.validation()
        assert result.success is False
        assert 'b' in result.metrics['column_laced_values']


class TestExpectColumnDistinctValuesToBeInSet:
    def test_pass_subset(self):
        df = pl.DataFrame({'c': ['a', 'b']})
        v = ExpectColumnDistinctValuesToBeInSet(
            ExpectColumnDistinctValuesToBeInSet.Params(column='c', value_set=['a', 'b', 'c'])
        )
        v.set_data(df)
        assert v.validation().success is True

    def test_pass_exact_match(self):
        df = pl.DataFrame({'c': ['a', 'b', 'c']})
        v = ExpectColumnDistinctValuesToBeInSet(
            ExpectColumnDistinctValuesToBeInSet.Params(column='c', value_set=['a', 'b', 'c'])
        )
        v.set_data(df)
        assert v.validation().success is True
