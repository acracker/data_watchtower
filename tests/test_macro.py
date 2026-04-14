#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""MacroTemplate 单元测试"""
import datetime
import pytest
from data_watchtower.utils import MacroTemplate


@pytest.fixture
def raw_macro_config():
    """原始宏配置（含 dict/impl 格式），模拟真实的 macro_config"""
    return {
        'today': {'impl': lambda: '2026-03-19'},
        'yesterday': {'impl': lambda: '2026-03-18'},
        'static_val': 'hello',
        'year:1': {'impl': lambda: '2026'},
    }


@pytest.fixture
def resolved_macro_config():
    """已解析的宏配置（纯值），模拟 get_macro_map 的输出"""
    return {
        'today': '2026-03-19',
        'yesterday': '2026-03-18',
        'static_val': 'hello',
        'year:1': '2026',
    }


@pytest.fixture
def raw_template(raw_macro_config):
    return MacroTemplate(raw_macro_config)


@pytest.fixture
def resolved_template(resolved_macro_config):
    return MacroTemplate(resolved_macro_config)


class TestMacroTemplate:
    def test_apply_string_replaces_resolved_macro(self, resolved_template):
        """apply_string 使用已解析值时正常替换"""
        result = resolved_template.apply_string("date is ${today}")
        assert result == "date is 2026-03-19"

    def test_apply_string_static_value(self, resolved_template):
        result = resolved_template.apply_string("say ${static_val}")
        assert result == "say hello"

    def test_apply_string_no_macro(self, resolved_template):
        result = resolved_template.apply_string("no macros here")
        assert result == "no macros here"

    def test_apply_string_unknown_macro_kept(self, resolved_template):
        result = resolved_template.apply_string("${unknown_macro}")
        assert result == "${unknown_macro}"

    def test_apply_dict(self, resolved_template):
        data = {'query': "SELECT * WHERE date='${today}'", 'name': 'test'}
        result = resolved_template.apply(data)
        assert result['query'] == "SELECT * WHERE date='2026-03-19'"
        assert result['name'] == 'test'

    def test_apply_nested_dict(self, resolved_template):
        data = {'outer': {'inner': '${yesterday}'}}
        result = resolved_template.apply(data)
        assert result['outer']['inner'] == '2026-03-18'

    def test_apply_non_string_passthrough(self, resolved_template):
        assert resolved_template.apply(42) == 42
        assert resolved_template.apply(None) is None

    def test_get_using_macro_names(self, raw_template):
        names = raw_template.get_using_macro_names("${today} and ${yesterday}")
        assert 'today' in names
        assert 'yesterday' in names

    def test_get_using_macro_names_with_colon(self, raw_template):
        names = raw_template.get_using_macro_names("${year:1}")
        assert 'year:1' in names

    def test_get_macro_map_calls_impl(self, raw_template):
        """get_macro_map 应该调用 impl callable 并返回值"""
        result = raw_template.get_macro_map(['today', 'static_val', 'nonexistent'])
        assert result['today'] == '2026-03-19'
        assert result['static_val'] == 'hello'
        assert 'nonexistent' not in result

    def test_get_used_macro_maps(self, raw_template):
        strings = ["query ${today}", "another ${static_val}"]
        result = raw_template.get_used_macro_maps(strings)
        assert 'today' in result
        assert result['today'] == '2026-03-19'
        assert 'static_val' in result

    def test_apply_does_not_mutate_original(self, resolved_template):
        original = {'query': '${today}'}
        resolved_template.apply(original)
        assert original['query'] == '${today}'

    def test_full_workflow_raw_to_resolved(self, raw_template):
        """完整流程：先用 get_used_macro_maps 解析，再用解析后的值 apply"""
        strings = ["date is ${today}", "year is ${year:1}"]
        resolved = raw_template.get_used_macro_maps(strings)
        resolved_mt = MacroTemplate(resolved)
        result = resolved_mt.apply_string("date is ${today}")
        assert result == "date is 2026-03-19"
