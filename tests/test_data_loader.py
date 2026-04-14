#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DatabaseLoader 测试

实际 DatabaseLoader._load() 使用 pl.read_database_uri()，
不涉及手动连接管理。
"""
import pytest
from unittest.mock import patch, MagicMock
from data_watchtower import DatabaseLoader


class TestDatabaseLoaderLoad:
    """测试 DatabaseLoader._load() 方法"""

    def test_load_returns_data_on_success(self):
        """_load() 成功时返回 read_database_uri 的结果"""
        mock_data = MagicMock()

        with patch('data_watchtower.core.data_loaders.pl.read_database_uri', return_value=mock_data) as mock_read:
            loader = DatabaseLoader(query="SELECT 1", connection="sqlite:///test.db")
            result = loader._load()

        mock_read.assert_called_once_with("SELECT 1", uri="sqlite:///test.db")
        assert result is mock_data

    def test_load_raises_on_query_error(self):
        """查询失败时 _load() 应抛出异常"""
        with patch('data_watchtower.core.data_loaders.pl.read_database_uri', side_effect=RuntimeError("query failed")):
            loader = DatabaseLoader(query="SELECT bad", connection="sqlite:///test.db")
            with pytest.raises(RuntimeError, match="query failed"):
                loader._load()
