#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import pytest
import polars as pl
from unittest.mock import patch, MagicMock
from data_watchtower import ExpectColumnValuesToBeInReferenceColumn


class TestExpectColumnValuesToBeInReferenceColumn:
    """跨表引用完整性校验器测试"""

    def _make_validator(self, column, ref_loader_config, reference_column=None):
        params = ExpectColumnValuesToBeInReferenceColumn.Params(
            column=column,
            reference_data_loader=json.dumps(ref_loader_config),
            reference_column=reference_column,
        )
        return ExpectColumnValuesToBeInReferenceColumn(params)

    def _mock_ref_loader(self, ref_df):
        """返回一个 mock 的 spawn_data_loader_from_dict，使其返回 ref_df"""
        mock_loader = MagicMock()
        mock_loader.load.return_value = ref_df
        return mock_loader

    @pytest.fixture
    def ref_loader_config(self):
        return {
            "__class__": "data_watchtower.core.data_loaders:DatabaseLoader",
            "query": "SELECT DISTINCT product_id FROM product_info",
            "connection": "sqlite:///test.db",
        }

    @patch("data_watchtower.core.validators.spawn_data_loader_from_dict")
    def test_all_values_exist(self, mock_spawn, ref_loader_config):
        """所有值都存在于参考数据源中 → 校验通过"""
        source_df = pl.DataFrame({"product_id": ["P001", "P002", "P003"]})
        ref_df = pl.DataFrame({"product_id": ["P001", "P002", "P003", "P004"]})

        mock_spawn.return_value = self._mock_ref_loader(ref_df)

        v = self._make_validator("product_id", ref_loader_config)
        v.set_data(source_df)
        result = v.validation()

        assert result.success is True
        assert result.metrics["missing_count"] == 0
        assert result.metrics["missing_values"] == []

    @patch("data_watchtower.core.validators.spawn_data_loader_from_dict")
    def test_missing_values(self, mock_spawn, ref_loader_config):
        """部分值不存在于参考数据源中 → 校验失败，返回缺失值"""
        source_df = pl.DataFrame({"product_id": ["P001", "P002", "P999"]})
        ref_df = pl.DataFrame({"product_id": ["P001", "P002", "P003"]})

        mock_spawn.return_value = self._mock_ref_loader(ref_df)

        v = self._make_validator("product_id", ref_loader_config)
        v.set_data(source_df)
        result = v.validation()

        assert result.success is False
        assert result.metrics["missing_count"] == 1
        assert "P999" in result.metrics["missing_values"]

    @patch("data_watchtower.core.validators.spawn_data_loader_from_dict")
    def test_different_column_names(self, mock_spawn, ref_loader_config):
        """两边字段名不同时，使用 reference_column 指定"""
        source_df = pl.DataFrame({"pid": ["P001", "P002", "P003"]})
        ref_df = pl.DataFrame({"product_id": ["P001", "P002"]})

        mock_spawn.return_value = self._mock_ref_loader(ref_df)

        v = self._make_validator("pid", ref_loader_config, reference_column="product_id")
        v.set_data(source_df)
        result = v.validation()

        assert result.success is False
        assert result.metrics["missing_count"] == 1
        assert "P003" in result.metrics["missing_values"]

    @patch("data_watchtower.core.validators.spawn_data_loader_from_dict")
    def test_null_values_ignored(self, mock_spawn, ref_loader_config):
        """源数据中的 null 值应被忽略，不参与比较"""
        source_df = pl.DataFrame({"product_id": ["P001", None, "P002"]})
        ref_df = pl.DataFrame({"product_id": ["P001", "P002"]})

        mock_spawn.return_value = self._mock_ref_loader(ref_df)

        v = self._make_validator("product_id", ref_loader_config)
        v.set_data(source_df)
        result = v.validation()

        assert result.success is True
        assert result.metrics["missing_count"] == 0
        assert result.metrics["source_distinct_count"] == 2

    @patch("data_watchtower.core.validators.spawn_data_loader_from_dict")
    def test_ref_null_values_ignored(self, mock_spawn, ref_loader_config):
        """参考数据源中的 null 值应被忽略"""
        source_df = pl.DataFrame({"product_id": ["P001"]})
        ref_df = pl.DataFrame({"product_id": ["P001", None]})

        mock_spawn.return_value = self._mock_ref_loader(ref_df)

        v = self._make_validator("product_id", ref_loader_config)
        v.set_data(source_df)
        result = v.validation()

        assert result.success is True
        assert result.metrics["ref_distinct_count"] == 1

    @patch("data_watchtower.core.validators.spawn_data_loader_from_dict")
    def test_empty_source(self, mock_spawn, ref_loader_config):
        """源数据为空 → 校验通过（没有需要检查的值）"""
        source_df = pl.DataFrame({"product_id": pl.Series([], dtype=pl.Utf8)})
        ref_df = pl.DataFrame({"product_id": ["P001"]})

        mock_spawn.return_value = self._mock_ref_loader(ref_df)

        v = self._make_validator("product_id", ref_loader_config)
        v.set_data(source_df)
        result = v.validation()

        assert result.success is True
        assert result.metrics["missing_count"] == 0

    @patch("data_watchtower.core.validators.spawn_data_loader_from_dict")
    def test_empty_reference(self, mock_spawn, ref_loader_config):
        """参考数据源为空 → 校验失败（所有值都缺失）"""
        source_df = pl.DataFrame({"product_id": ["P001", "P002"]})
        ref_df = pl.DataFrame({"product_id": pl.Series([], dtype=pl.Utf8)})

        mock_spawn.return_value = self._mock_ref_loader(ref_df)

        v = self._make_validator("product_id", ref_loader_config)
        v.set_data(source_df)
        result = v.validation()

        assert result.success is False
        assert result.metrics["missing_count"] == 2

    @patch("data_watchtower.core.validators.spawn_data_loader_from_dict")
    def test_missing_values_capped_at_100(self, mock_spawn, ref_loader_config):
        """缺失值列表最多返回100条"""
        source_ids = [f"P{i:04d}" for i in range(150)]
        source_df = pl.DataFrame({"product_id": source_ids})
        ref_df = pl.DataFrame({"product_id": pl.Series([], dtype=pl.Utf8)})

        mock_spawn.return_value = self._mock_ref_loader(ref_df)

        v = self._make_validator("product_id", ref_loader_config)
        v.set_data(source_df)
        result = v.validation()

        assert result.success is False
        assert result.metrics["missing_count"] == 150
        assert len(result.metrics["missing_values"]) == 100

    @patch("data_watchtower.core.validators.spawn_data_loader_from_dict")
    def test_integer_column(self, mock_spawn, ref_loader_config):
        """支持整数类型的字段"""
        source_df = pl.DataFrame({"id": [1, 2, 3, 4]})
        ref_df = pl.DataFrame({"id": [1, 2, 3]})

        mock_spawn.return_value = self._mock_ref_loader(ref_df)

        v = self._make_validator("id", ref_loader_config)
        v.set_data(source_df)
        result = v.validation()

        assert result.success is False
        assert result.metrics["missing_count"] == 1

    @patch("data_watchtower.core.validators.spawn_data_loader_from_dict")
    def test_reference_column_defaults_to_column(self, mock_spawn, ref_loader_config):
        """reference_column 为 None 时，默认使用 column 的值"""
        source_df = pl.DataFrame({"product_id": ["P001"]})
        ref_df = pl.DataFrame({"product_id": ["P001"]})

        mock_spawn.return_value = self._mock_ref_loader(ref_df)

        v = self._make_validator("product_id", ref_loader_config, reference_column=None)
        v.set_data(source_df)
        result = v.validation()

        assert result.success is True
        mock_spawn.assert_called_once()

    def test_disallowed_class_raises(self, ref_loader_config):
        """__class__ 不在白名单中时，应抛出 ValueError"""
        malicious_config = {
            "__class__": "os:system",
            "query": "SELECT 1",
            "connection": "sqlite:///test.db",
        }
        v = self._make_validator("product_id", malicious_config)
        v.set_data(pl.DataFrame({"product_id": ["P001"]}))
        with pytest.raises(ValueError, match="not allowed"):
            v.validation()
