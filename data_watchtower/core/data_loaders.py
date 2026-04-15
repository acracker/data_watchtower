#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import datetime
import logging
from functools import lru_cache
from contextlib import contextmanager

import duckdb
import polars as pl
from attrs import define, field

from .base import DataLoader
from ..utils import get_subclasses, load_subclasses

logger = logging.getLogger(__name__)
CUSTOM_DATA_LOADER_PATH = os.getenv(
    "DW_CUSTOM_DATA_LOADER_PATH", "dw_custom.data_loaders"
)
CACHE_DIR_PATH = os.getenv("DW_CACHE_DIR_PATH", "_cache")

_CACHE_TABLE = "cache_data"
_META_TABLE = "cache_meta"

_IS_WINDOWS = sys.platform == "win32"

if _IS_WINDOWS:
    from filelock import FileLock

    @contextmanager
    def _read_lock(lock_path):
        """Windows: 独占锁（不支持共享锁）"""
        with FileLock(lock_path):
            yield

    @contextmanager
    def _write_lock(lock_path):
        """Windows: 独占锁"""
        with FileLock(lock_path):
            yield

else:
    import fcntl

    @contextmanager
    def _read_lock(lock_path):
        """Linux/macOS: 共享锁，允许多进程并发读"""
        with open(lock_path, "a+") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    @contextmanager
    def _write_lock(lock_path):
        """Linux/macOS: 独占锁，阻塞直到所有读锁释放"""
        with open(lock_path, "a+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)


@define()
class DatabaseLoader(DataLoader):
    """
    使用playhouse.db_url连接数据库; 带缓存的
    """

    query = field(type=str)
    connection = field(type=str)
    # 缓存过期秒数,为0则表示使用缓存
    ttl_cache = field(
        type=int,
        default=None,
        converter=lambda x: int(x) if str(x).isdigit() and int(x) > 0 else None,
    )  # 0:不能缓存;

    def _cache_key(self):
        import hashlib

        text = f"{self.query}-{self.connection}"
        return hashlib.sha1(text.encode()).hexdigest()

    def _cache_paths(self):
        os.makedirs(CACHE_DIR_PATH, exist_ok=True)
        key = self._cache_key()
        db_path = os.path.join(CACHE_DIR_PATH, f"{key}.duckdb")
        lock_path = os.path.join(CACHE_DIR_PATH, f"{key}.lock")
        return db_path, lock_path

    def _is_cache_valid(self, db_path, lock_path) -> bool:
        if not os.path.exists(db_path):
            return False
        with _read_lock(lock_path):
            with duckdb.connect(db_path, read_only=True) as conn:
                row = conn.execute(f"SELECT cached_at FROM {_META_TABLE}").fetchone()
        if row is None:
            return False
        cached_at = datetime.datetime.fromisoformat(str(row[0]))
        return (datetime.datetime.now() - cached_at).total_seconds() < self.ttl_cache

    def _read_cache(self, db_path, lock_path) -> pl.DataFrame:
        with _read_lock(lock_path):
            with duckdb.connect(db_path, read_only=True) as conn:
                return conn.execute(f"SELECT * FROM {_CACHE_TABLE}").pl()

    def _write_cache(self, db_path, lock_path, df: pl.DataFrame):
        logger.info("About to update data, starting to acquire lock")
        with _write_lock(lock_path):
            with duckdb.connect(db_path) as conn:
                conn.execute(
                    f"CREATE OR REPLACE TABLE {_CACHE_TABLE} AS SELECT * FROM df"
                )
                now = datetime.datetime.now().isoformat()
                conn.execute(
                    f"CREATE OR REPLACE TABLE {_META_TABLE} AS "
                    f"SELECT '{now}'::TIMESTAMP AS cached_at"
                )

    def _load(self):
        def _load_data():
            return pl.read_database_uri(self.query, uri=self.connection)

        if self.ttl_cache is None:
            return _load_data()

        db_path, lock_path = self._cache_paths()
        if self._is_cache_valid(db_path, lock_path):
            return self._read_cache(db_path, lock_path)

        df = _load_data()
        self._write_cache(db_path, lock_path, df)
        return df


@lru_cache()
def get_registered_data_loader_maps():
    custom_path = CUSTOM_DATA_LOADER_PATH.split(";")
    subclasses = get_subclasses(DataLoader)
    try:
        custom_subclasses = load_subclasses(custom_path, DataLoader)
    except ModuleNotFoundError:
        custom_subclasses = []
    result = {}
    for cls in subclasses + custom_subclasses:
        key = cls.__name__
        if key in result and result[key].module_path() != cls.module_path():
            raise ValueError("Duplicate data loader name: %s" % key)
        result[key] = cls
    return result


def get_registered_data_loaders():
    result = get_registered_data_loader_maps()
    return list(result.values())
