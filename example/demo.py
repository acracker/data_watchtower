#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import random
import datetime
from faker import Faker
from peewee import *
from playhouse.db_url import connect
from data_watchtower import (DbServices, Watchtower, DatabaseLoader,
                             ExpectRowCountToBeBetween, ExpectColumnValuesToNotBeNull)

dw_test_data_db_url = os.getenv('DW_TEST_DATA_DB_URL', 'sqlite:///test.db')
dw_backend_db_url = os.getenv('DW_BACKEND_DB_URL', "sqlite:///data.db")
database = connect(dw_test_data_db_url)

NUM_OF_STUDENTS = 20
NUM_OF_DAY = 10


class BaseModel(Model):
    class Meta:
        database = database


class Student(BaseModel):
    name = CharField()
    age = IntegerField()


class Score(BaseModel):
    name = CharField()
    date = DateField()
    chinese = IntegerField(null=True)
    english = IntegerField(null=True)
    math = IntegerField(null=True)


def gen_data():
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
    return days


def main():
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
    data_loader.load()
    # 创建监控项
    wt = Watchtower(name=wt_name, data_loader=data_loader, custom_macro_map=custom_macro_map)
    # 添加校验器
    params = ExpectRowCountToBeBetween.Params(min_value=NUM_OF_STUDENTS, max_value=None)
    wt.add_validator(ExpectRowCountToBeBetween(params))

    params = ExpectColumnValuesToNotBeNull.Params(column='${column}')
    wt.add_validator(ExpectColumnValuesToNotBeNull(params))

    result = wt.run()
    print(result['success'])

    # 保存监控配置以及监控结果
    db_svr = DbServices(dw_backend_db_url)
    # 创建表
    db_svr.create_tables()
    # 保存监控配置
    db_svr.add_watchtower(wt)
    # 保存监控结果
    db_svr.save_result(wt, result)
    # 重新计算监控项的成功状态
    db_svr.update_watchtower_success_status(wt)

    wd = db_svr.get_watchtower(wt_name)
    validators = db_svr.get_validators_of_watchtower(wt_name)
    return


if __name__ == '__main__':
    gen_data()
    main()
