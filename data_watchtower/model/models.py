#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import datetime
import shortuuid
from peewee import *
from playhouse.shortcuts import model_to_dict
from playhouse.sqlite_ext import TextField

database_proxy = DatabaseProxy()


class BaseModel(Model):

    def to_dict(self):
        return model_to_dict(self)

    """A base model that will use our Sqlite database."""

    class Meta:
        database = database_proxy


class ValidationDetail(BaseModel):
    id = AutoField(primary_key=True)
    wt_name = CharField(max_length=128, index=True)
    name = CharField(max_length=128)
    success = BooleanField()
    run_time = DateTimeField()
    metrics = TextField()
    params = TextField(null=True)
    macro_maps = TextField(null=True)
    run_id = CharField(max_length=32, default=shortuuid.uuid)
    run_type = SmallIntegerField()
    ignored = BooleanField(default=False)
    update_time = DateTimeField(default=datetime.datetime.now)
    create_time = DateTimeField(default=datetime.datetime.now)

    class Meta:
        table_name = 'st_validation_detail'


class Watchtower(BaseModel):
    name = CharField(max_length=128, primary_key=True)
    success = BooleanField(null=True)  # success
    run_time = DateTimeField(null=True)  # 最后一次运行的时间
    data_loader = TextField()
    validators = TextField()
    custom_macro_map = TextField()
    success_method = CharField(max_length=64)
    validator_success_method = CharField(max_length=64, default='all', help_text='option: any, all')
    update_time = DateTimeField(default=datetime.datetime.now)
    create_time = DateTimeField(default=datetime.datetime.now)

    class Meta:
        table_name = 'st_watchtower'
