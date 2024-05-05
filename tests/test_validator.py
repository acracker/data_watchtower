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
class TestDemoClass:
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
        # 创建需要的测试数据
        data = {
            'column1': [1, 2, 3, 4, 5],
            'update_time': [datetime.now() - timedelta(days=5), datetime.now() - timedelta(days=3),
                            datetime.now() - timedelta(days=1), datetime.now(), datetime.now()]
        }
        df = pl.DataFrame(data)

        # 创建验证器实例
        validator = ExpectColumnRecentlyUpdated(
            ExpectColumnRecentlyUpdated.Params(update_time_column='update_time', days=2, hours=1))
        validator.set_data(df)
        # 执行验证
        result = validator.validation()
        # 断言验证结果是否符合预期
        assert result.success
        assert result.metrics['last_updated_time'] == datetime.now()

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
        assert result.metrics['std'] == 2.8722813232690143
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
        assert result.metrics['std'] == 15.811388300841898

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
        assert result.success
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
        assert result.metrics['column_laced_values'] == set()
        assert result.metrics['param_laced_values'] == set()

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
