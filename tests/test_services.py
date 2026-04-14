#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DbServices 回归测试，使用 :memory: SQLite 避免文件残留

db_svr / sample_watchtower fixtures 由 conftest.py 提供
"""
import datetime
import pytest
from data_watchtower.model.models import ValidationDetailModel
from data_watchtower.utils import json_dumps


class TestComputeWatchtowerSuccessStatus:
    """Bug 1 回归测试：compute_watchtower_success_status 的 last 分支"""

    def _insert_detail(self, db_svr, wt_name, success, run_time):
        """插入一条 validation detail 记录"""
        record = dict(
            wt_name=wt_name,
            name=wt_name,
            success=success,
            run_time=run_time,
            metrics=json_dumps({}),
            params=None,
            macro_maps=None,
            run_id='test_run',
            run_type=1,
            update_time=datetime.datetime.now(),
            create_time=datetime.datetime.now(),
        )
        ValidationDetailModel.insert(record).execute()

    def test_last_returns_false_when_last_run_failed(self, db_svr, sample_watchtower):
        """last 分支应该返回最后一次运行的 success 值，而非始终 True"""
        db_svr.add_watchtower(sample_watchtower)
        now = datetime.datetime.now()

        # 插入一条成功记录和一条失败记录（失败记录时间更晚）
        self._insert_detail(db_svr, 'test_wt', True, now - datetime.timedelta(hours=2))
        self._insert_detail(db_svr, 'test_wt', False, now - datetime.timedelta(hours=1))

        # 强制使用 last 方法
        sample_watchtower.params['validator_success_method'] = 'last'
        sample_watchtower.params['success_method'] = 'last'

        result = db_svr.compute_watchtower_success_status(sample_watchtower)
        assert result is False

    def test_last_returns_true_when_last_run_succeeded(self, db_svr, sample_watchtower):
        """last 分支：最后一次成功则返回 True"""
        db_svr.add_watchtower(sample_watchtower)
        now = datetime.datetime.now()

        self._insert_detail(db_svr, 'test_wt', False, now - datetime.timedelta(hours=2))
        self._insert_detail(db_svr, 'test_wt', True, now - datetime.timedelta(hours=1))

        sample_watchtower.params['validator_success_method'] = 'last'
        sample_watchtower.params['success_method'] = 'last'

        result = db_svr.compute_watchtower_success_status(sample_watchtower)
        assert result is True

    def test_last_returns_true_when_no_records(self, db_svr, sample_watchtower):
        """last 分支：没有记录时返回 True（DoesNotExist）"""
        db_svr.add_watchtower(sample_watchtower)

        sample_watchtower.params['validator_success_method'] = 'last'
        sample_watchtower.params['success_method'] = 'last'

        result = db_svr.compute_watchtower_success_status(sample_watchtower)
        assert result is True


class TestGetWatchtower:
    """get_watchtower 返回 dict 而非 model 对象"""

    def test_get_watchtower_returns_dict(self, db_svr, sample_watchtower):
        db_svr.add_watchtower(sample_watchtower)
        result = db_svr.get_watchtower('test_wt')
        assert isinstance(result, dict)
        assert result['name'] == 'test_wt'

    def test_get_watchtower_not_found(self, db_svr):
        result = db_svr.get_watchtower('nonexistent')
        assert result is None
