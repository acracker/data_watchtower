#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Watchtower.run_from_db 测试，使用 :memory: SQLite + mock DataLoader 避免外部依赖

db_svr fixture 由 conftest.py 提供
"""
from unittest.mock import patch

import polars as pl
import pytest

from data_watchtower import (
    DbServices, Watchtower, DatabaseLoader,
    ExpectRowCountToBeBetween, ExpectColumnValuesToNotBeNull,
)
from data_watchtower.model.models import ValidationDetailModel


MOCK_DF = pl.DataFrame({
    'id': [1, 2, 3],
    'name': ['a', 'b', 'c'],
    'value': [10, 20, 30],
})


def _seed_watchtower(db_svr, name='test_wt'):
    """向数据库中插入一个带 validator 的 Watchtower 配置"""
    data_loader = DatabaseLoader(query='SELECT 1', connection='sqlite:///test.db')
    wt = Watchtower(name=name, data_loader=data_loader)
    params = ExpectRowCountToBeBetween.Params(min_value=1, max_value=100)
    wt.add_validator(ExpectRowCountToBeBetween(params))
    db_svr.add_watchtower(wt)
    return wt


class TestRunFromDb:

    @patch('data_watchtower.core.data_loaders.DatabaseLoader.load', return_value=MOCK_DF)
    def test_run_from_db_success(self, mock_load, db_svr):
        """从 DB 加载并运行，验证结果和持久化"""
        _seed_watchtower(db_svr, 'test_wt')

        result = Watchtower.run_from_db('test_wt', db_svr)

        assert result['success'] is True
        assert result['name'] == 'test_wt'
        assert len(result['validators_result']) == 1
        mock_load.assert_called_once()

        # 验证结果已持久化
        details = list(ValidationDetailModel.select().where(
            ValidationDetailModel.wt_name == 'test_wt'
        ))
        assert len(details) >= 1

    def test_run_from_db_not_found(self, db_svr):
        """名称不存在时抛 ValueError"""
        with pytest.raises(ValueError, match='watchtower not found'):
            Watchtower.run_from_db('nonexistent', db_svr)

    @patch('data_watchtower.core.data_loaders.DatabaseLoader.load', return_value=MOCK_DF)
    def test_run_from_db_no_save(self, mock_load, db_svr):
        """save_result=False 时不保存结果到数据库"""
        _seed_watchtower(db_svr, 'test_no_save')

        result = Watchtower.run_from_db('test_no_save', db_svr, save_result=False)

        assert result['success'] is True
        # 验证没有持久化记录
        details = list(ValidationDetailModel.select().where(
            ValidationDetailModel.wt_name == 'test_no_save'
        ))
        assert len(details) == 0

    @patch('data_watchtower.core.data_loaders.DatabaseLoader.load', return_value=MOCK_DF)
    def test_run_from_db_with_custom_macro(self, mock_load, db_svr):
        """传入 custom_macro_map 正常工作"""
        _seed_watchtower(db_svr, 'test_macro')

        custom_macro = {
            'today': {'impl': lambda: '2026-03-19'},
        }
        result = Watchtower.run_from_db(
            'test_macro', db_svr,
            custom_macro_map=custom_macro,
            save_result=False,
        )

        assert result['success'] is True

    def test_code_mode_unchanged(self):
        """代码模式（直接构造 Watchtower）不受 run_from_db 影响"""
        data_loader = DatabaseLoader(query='SELECT 1', connection='sqlite:///test.db')
        wt = Watchtower(name='code_mode', data_loader=data_loader)
        params = ExpectRowCountToBeBetween.Params(min_value=1, max_value=100)
        wt.add_validator(ExpectRowCountToBeBetween(params))

        with patch('data_watchtower.core.data_loaders.DatabaseLoader.load', return_value=MOCK_DF):
            result = wt.run()

        assert result['success'] is True
        assert result['name'] == 'code_mode'
