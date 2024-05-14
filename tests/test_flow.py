import os
import pytest
import random
import datetime
from faker import Faker
from peewee import *
from playhouse.db_url import connect
from data_watchtower import (DbServices, Watchtower, DatabaseLoader,
                             ExpectRowCountToBeBetween, ExpectColumnValuesToNotBeNull)

dw_test_data_db_url = os.getenv('DW_TEST_DATA_DB_URL', 'sqlite:///test.db')
dw_backend_db_url = os.getenv('DW_BACKEND_DB_URL', "sqlite:///data.db")
NUM_OF_STUDENTS = 20
NUM_OF_DAY = 10

database_proxy = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy


class Student(BaseModel):
    name = CharField()
    age = IntegerField()


class Score(BaseModel):
    name = CharField()
    date = DateField()
    chinese = IntegerField(null=True)
    english = IntegerField(null=True)
    math = IntegerField(null=True)


def setup_module():
    # print("初始化数据")
    database = connect(dw_test_data_db_url)
    database_proxy.initialize(database)
    with database:
        database.drop_tables([Student, Score])
        database.create_tables([Student, Score])

    fake = Faker(locale='zh_CN')
    students = []
    for i in range(NUM_OF_STUDENTS):
        student = Student.create(name=fake.unique.name(), age=fake.random_int(min=10, max=18))
        students.append(student)
    days = []
    for i in range(NUM_OF_DAY):
        date = (datetime.datetime.now() - datetime.timedelta(i)).date()
        days.append(date)
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
            score = Score.create(
                name=student.name,
                date=date,
                chinese=chinese,
                english=english,
                math=math,
            )


def teardown_module():
    # print('测试模块清理')
    pass


@pytest.fixture
def custom_macro_map():
    return {
        'today': {'impl': lambda: datetime.datetime.today().strftime("%Y-%m-%d")},
        'start_date': '2024-04-01',
        'column': 'name',
    }


@pytest.fixture
def db_svr():
    return DbServices(dw_backend_db_url)


def test_demo_data():
    assert Student.select().count() == NUM_OF_STUDENTS
    assert Score.select().count() == NUM_OF_DAY * (NUM_OF_STUDENTS - 1)


def test_create_table(db_svr):
    db_svr.create_tables()
    assert len(db_svr.get_watchtowers()) >= 0


def test_watchtower_crud(db_svr, custom_macro_map):
    wt_name = 'score of ${today}'
    query = "SELECT * FROM score where date='${today}'"
    params = dict(
        schedule="12:00",
        validator_success_method='all',
        success_method='all',
    )
    connection = dw_test_data_db_url
    # 先删除存在的
    db_svr.delete_watchtower(wt_name)

    data_loader = DatabaseLoader(query=query, connection=connection)
    watchtower = Watchtower(name=wt_name, data_loader=data_loader, custom_macro_map=custom_macro_map, **params)
    db_svr.add_watchtower(watchtower)
    wt = db_svr.get_watchtower(wt_name)
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

    db_svr.update_watchtower(name=wt_name, data_loader=data_loader, params=params)
    wt = db_svr.get_watchtower(wt_name)
    assert wt['name'] == wt_name
    assert wt['data_loader']['__class__'] == DatabaseLoader.module_path()
    assert wt['data_loader']['query'] == query
    assert wt['data_loader']['connection'] == connection
    assert wt['params'] == params

    assert db_svr.delete_watchtower(wt_name) == 1
    wt = db_svr.get_watchtower(wt_name)
    assert wt is None


def test_case1(db_svr):
    wt_name = 'score of ${today}'
    # 自定义宏模板
    custom_macro_map = {
        'today': {'impl': lambda: datetime.datetime.today().strftime("%Y-%m-%d")},
        'start_date': '2024-04-01',
        'column': 'name',
    }
    # 设置数据加载器,用来加载需要校验的数据
    query = "SELECT * FROM score where date='${today}'"
    data_loader = DatabaseLoader(query=query, connection=dw_test_data_db_url)
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
    db_svr.add_watchtower(watchtower)
    # 保存监控结果
    db_svr.save_result(watchtower, result)

    item = db_svr.get_watchtower(wt_name)
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
    return
