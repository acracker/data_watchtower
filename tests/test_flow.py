#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""集成测试：完整流程 DataLoader → Watchtower → Validator → DbServices"""
from data_watchtower import (
    Watchtower, DatabaseLoader,
    ExpectRowCountToBeBetween, ExpectColumnValuesToNotBeNull,
)
from conftest import Student, Score, NUM_OF_STUDENTS, NUM_OF_DAYS


def test_demo_data(test_data_db):
    """验证测试数据已正确生成"""
    assert Student.select().count() == NUM_OF_STUDENTS
    assert Score.select().count() == NUM_OF_DAYS * (NUM_OF_STUDENTS - 1)


def test_create_table(file_db_svr):
    file_db_svr.create_tables()
    assert len(file_db_svr.get_watchtowers()) >= 0


def test_watchtower_crud(file_db_svr, test_data_db_url, custom_macro_map):
    wt_name = 'score of ${today}'
    query = "SELECT * FROM score where date='${today}'"
    params = dict(
        schedule="12:00",
        validator_success_method='all',
        success_method='all',
    )
    connection = test_data_db_url
    # 先删除存在的
    file_db_svr.delete_watchtower(wt_name)

    data_loader = DatabaseLoader(query=query, connection=connection)
    watchtower = Watchtower(name=wt_name, data_loader=data_loader, custom_macro_map=custom_macro_map, **params)
    file_db_svr.add_watchtower(watchtower)
    wt = file_db_svr.get_watchtower(wt_name)
    assert wt['name'] == wt_name
    assert wt['data_loader']['__class__'] == DatabaseLoader.module_path()
    assert wt['data_loader']['query'] == query
    assert wt['data_loader']['connection'] == connection
    assert wt['params'] == params

    params = dict(
        schedule="13:00",
        validator_success_method='any',
        success_method='all',
    )
    query = "SELECT * FROM score where date='${today}' and 1=1 "
    data_loader = DatabaseLoader(query=query, connection=connection)

    file_db_svr.update_watchtower(name=wt_name, data_loader=data_loader, params=params)
    wt = file_db_svr.get_watchtower(wt_name)
    assert wt['name'] == wt_name
    assert wt['data_loader']['__class__'] == DatabaseLoader.module_path()
    assert wt['data_loader']['query'] == query
    assert wt['data_loader']['connection'] == connection
    assert wt['params'] == params

    assert file_db_svr.delete_watchtower(wt_name) == 1
    wt = file_db_svr.get_watchtower(wt_name)
    assert wt is None


def test_case1(file_db_svr, test_data_db, test_data_db_url, custom_macro_map):
    wt_name = 'score of ${today}'
    # 设置数据加载器,用来加载需要校验的数据
    query = "SELECT * FROM score where date='${today}'"
    data_loader = DatabaseLoader(query=query, connection=test_data_db_url)
    # 创建监控项
    watchtower = Watchtower(name=wt_name, data_loader=data_loader, custom_macro_map=custom_macro_map)
    # 添加校验器
    params = ExpectRowCountToBeBetween.Params(min_value=NUM_OF_STUDENTS, max_value=None)
    watchtower.add_validator(ExpectRowCountToBeBetween(params))

    params = ExpectColumnValuesToNotBeNull.Params(column='${column}')
    watchtower.add_validator(ExpectColumnValuesToNotBeNull(params))

    result = watchtower.run()
    assert result['success'] is False
    watchtower.macro_template.macro_config = result['macro_maps']
    assert result['name'] == watchtower.macro_template.apply_string(watchtower.name)
    assert wt_name == watchtower.name

    # 保存监控配置
    file_db_svr.add_watchtower(watchtower)
    # 保存监控结果
    file_db_svr.save_result(watchtower, result)

    item = file_db_svr.get_watchtower(wt_name)
    watchtower = Watchtower.from_dict(item)

    watchtower.set_custom_macro(**custom_macro_map)

    params = ExpectRowCountToBeBetween.Params(min_value=NUM_OF_STUDENTS, max_value=None)
    watchtower.add_validator(ExpectRowCountToBeBetween(params))

    params = ExpectColumnValuesToNotBeNull.Params(column='${column}')
    watchtower.add_validator(ExpectColumnValuesToNotBeNull(params))

    result = watchtower.run()
    assert result['success'] is False
    watchtower.macro_template.macro_config = result['macro_maps']
    assert result['name'] == watchtower.macro_template.apply_string(watchtower.name)
    assert wt_name == watchtower.name
