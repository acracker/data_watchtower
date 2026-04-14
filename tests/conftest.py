#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""共享 fixtures：数据库连接、测试数据生成、常用对象构造"""
import os
import pathlib
import random
import datetime

import pytest
from faker import Faker
from peewee import (
    Model, CharField, IntegerField, DateField,
    DatabaseProxy, SqliteDatabase,
)
from playhouse.db_url import connect

from data_watchtower import DbServices, Watchtower, DatabaseLoader
from data_watchtower.model.models import (
    database_proxy as backend_db_proxy,
    WatchtowerModel, ValidationDetailModel, ValidatorRelationModel,
)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
# connectorx 将 sqlite:///relative.db 解析为绝对路径 /relative.db，
# 因此需要使用绝对路径以确保 connectorx 和 peewee 都能正确定位文件。
_project_root = pathlib.Path(__file__).parent.parent

NUM_OF_STUDENTS = 20
NUM_OF_DAYS = 10

# ---------------------------------------------------------------------------
# 测试数据源 — Score / Student 模型（文件级 SQLite）
# ---------------------------------------------------------------------------
_test_data_db_proxy = DatabaseProxy()


class _BaseModel(Model):
    class Meta:
        database = _test_data_db_proxy


class Student(_BaseModel):
    name = CharField()
    age = IntegerField()


class Score(_BaseModel):
    name = CharField()
    date = DateField()
    chinese = IntegerField(null=True)
    english = IntegerField(null=True)
    math = IntegerField(null=True)


def _generate_test_data(db_url):
    """创建 Student / Score 表并填充随机测试数据"""
    database = connect(db_url)
    _test_data_db_proxy.initialize(database)

    with database:
        database.drop_tables([Student, Score])
        database.create_tables([Student, Score])

    fake = Faker(locale='zh_CN')
    students = []
    for _ in range(NUM_OF_STUDENTS):
        student = Student.create(
            name=fake.unique.name(),
            age=fake.random_int(min=10, max=18),
        )
        students.append(student)

    for i in range(NUM_OF_DAYS):
        date = (datetime.datetime.now() - datetime.timedelta(i)).date()
        random.shuffle(students)
        for j, student in enumerate(students):
            if j == 0:
                # 让一个学生缺考
                continue
            chinese = fake.random_int(min=0, max=100)
            english = fake.random_int(min=0, max=100)
            math = fake.random_int(min=0, max=100)
            if fake.random_int(min=1, max=10) == 1:
                chinese = None
            if fake.random_int(min=1, max=10) == 1:
                english = None
            if fake.random_int(min=1, max=10) == 1:
                math = None
            Score.create(
                name=student.name,
                date=date,
                chinese=chinese,
                english=english,
                math=math,
            )

    return database


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def test_data_db_url():
    """被监控数据源的 SQLite URL（绝对路径）"""
    return os.getenv(
        'DW_TEST_DATA_DB_URL',
        f'sqlite:///{_project_root / "test.db"}',
    )


@pytest.fixture(scope='session')
def backend_db_url():
    """后端存储的 SQLite URL（绝对路径）"""
    return os.getenv(
        'DW_BACKEND_DB_URL',
        f'sqlite:///{_project_root / "data.db"}',
    )


@pytest.fixture(scope='session')
def test_data_db(test_data_db_url):
    """Session 级别：生成 Student / Score 测试数据，返回 peewee Database"""
    database = _generate_test_data(test_data_db_url)
    yield database
    database.close()


@pytest.fixture
def db_svr():
    """函数级别：使用内存数据库的 DbServices，每个测试隔离"""
    database = SqliteDatabase(':memory:')
    backend_db_proxy.initialize(database)
    database.create_tables([WatchtowerModel, ValidationDetailModel, ValidatorRelationModel])
    svr = DbServices(database)
    yield svr
    database.close()


@pytest.fixture
def file_db_svr(backend_db_url):
    """函数级别：使用文件数据库的 DbServices（集成测试用）"""
    return DbServices(backend_db_url)


@pytest.fixture
def sample_watchtower():
    """创建一个简单的 Watchtower 用于测试"""
    data_loader = DatabaseLoader(query="SELECT 1", connection="sqlite:///test.db")
    return Watchtower(name='test_wt', data_loader=data_loader)


@pytest.fixture
def custom_macro_map():
    """通用的自定义宏配置"""
    return {
        'today': {'impl': lambda: datetime.datetime.today().strftime("%Y-%m-%d")},
        'start_date': '2024-04-01',
        'column': 'name',
    }
