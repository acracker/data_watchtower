#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import tempfile
import os
import pytest
import polars as pl
from unittest.mock import patch, MagicMock
from data_watchtower import DatabaseLoader


class TestDatabaseLoaderLoad:
    """测试 DatabaseLoader._load() 方法"""

    def test_load_returns_data_on_success(self):
        mock_data = MagicMock()
        with patch('data_watchtower.core.data_loaders.pl.read_database_uri', return_value=mock_data) as mock_read:
            loader = DatabaseLoader(query="SELECT 1", connection="sqlite:///test.db")
            result = loader._load()
        mock_read.assert_called_once_with("SELECT 1", uri="sqlite:///test.db")
        assert result is mock_data

    def test_load_raises_on_query_error(self):
        with patch('data_watchtower.core.data_loaders.pl.read_database_uri', side_effect=RuntimeError("query failed")):
            loader = DatabaseLoader(query="SELECT bad", connection="sqlite:///test.db")
            with pytest.raises(RuntimeError, match="query failed"):
                loader._load()


class TestDatabaseLoaderCache:
    """测试 ttl_cache 缓存逻辑"""

    def _loader(self, tmp_dir, ttl_cache=None):
        loader = DatabaseLoader(query="SELECT 1", connection="sqlite:///test.db", ttl_cache=ttl_cache)
        with patch('data_watchtower.core.data_loaders.CACHE_DIR_PATH', tmp_dir):
            return loader

    def test_cache_miss_calls_db_and_writes_cache(self):
        df = pl.DataFrame({'a': [1, 2, 3]})
        with tempfile.TemporaryDirectory() as tmp:
            loader = self._loader(tmp, ttl_cache=60)
            with patch('data_watchtower.core.data_loaders.CACHE_DIR_PATH', tmp), \
                 patch('data_watchtower.core.data_loaders.pl.read_database_uri', return_value=df) as mock_read:
                result = loader._load()
            mock_read.assert_called_once()
            assert result.equals(df)
            # 缓存文件已写入
            db_path, _ = loader._cache_paths()
            # 重新 patch CACHE_DIR_PATH 获取路径
            with patch('data_watchtower.core.data_loaders.CACHE_DIR_PATH', tmp):
                db_path, _ = loader._cache_paths()
            assert os.path.exists(db_path)

    def test_cache_hit_skips_db(self):
        df = pl.DataFrame({'a': [1, 2, 3]})
        with tempfile.TemporaryDirectory() as tmp:
            loader = self._loader(tmp, ttl_cache=60)
            with patch('data_watchtower.core.data_loaders.CACHE_DIR_PATH', tmp), \
                 patch('data_watchtower.core.data_loaders.pl.read_database_uri', return_value=df) as mock_read:
                loader._load()  # 第一次写缓存
                mock_read.reset_mock()
                result = loader._load()  # 第二次应命中缓存
            mock_read.assert_not_called()
            assert result.equals(df)

    def test_cache_expired_calls_db_again(self):
        df = pl.DataFrame({'a': [1, 2, 3]})
        with tempfile.TemporaryDirectory() as tmp:
            loader = self._loader(tmp, ttl_cache=60) # ttl_cache=None
            with patch('data_watchtower.core.data_loaders.CACHE_DIR_PATH', tmp), \
                 patch('data_watchtower.core.data_loaders.pl.read_database_uri', return_value=df) as mock_read:
                loader._load()  # 写缓存
                mock_read.reset_mock()
                # 伪造缓存时间为 2 分钟前（已过期）
                expired_time = datetime.datetime.now() - datetime.timedelta(seconds=120)
                with patch.object(loader, '_is_cache_valid', return_value=False):
                    result = loader._load()
            mock_read.assert_called_once()

    def test_ttl_none_never_caches(self):
        df = pl.DataFrame({'a': [1]})
        with tempfile.TemporaryDirectory() as tmp:
            loader = self._loader(tmp) # ttl_cache=None
            with patch('data_watchtower.core.data_loaders.CACHE_DIR_PATH', tmp), \
                 patch('data_watchtower.core.data_loaders.pl.read_database_uri', return_value=df) as mock_read:
                loader._load()
                loader._load()
            assert mock_read.call_count == 2  # 每次都查 DB

    def test_ttl_zero_treated_as_none(self):
        loader = self._loader("/tmp", ttl_cache=0)
        assert loader.ttl_cache is None
