#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import datetime
import shortuuid
from peewee import *
from playhouse.shortcuts import model_to_dict
from playhouse.sqlite_ext import TextField
from ..utils import json_loads

database_proxy = DatabaseProxy()


class BaseModel(Model):

    def to_dict(self, fields_from_query=None):
        return model_to_dict(self, fields_from_query=fields_from_query)

    class Meta:
        database = database_proxy


class ValidationDetailModel(BaseModel):
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
        table_name = 'dw_validation_detail'


class WatchtowerModel(BaseModel):
    name = CharField(max_length=128, primary_key=True)  # wt_name
    success = BooleanField(null=True)  # success
    run_time = DateTimeField(null=True)  # 最后一次运行的时间
    data_loader = TextField()
    params = TextField()
    update_time = DateTimeField(default=datetime.datetime.now)
    create_time = DateTimeField(default=datetime.datetime.now)

    class Meta:
        table_name = 'dw_watchtower'

    def to_dict(self, fields_from_query=None):
        result = super().to_dict(fields_from_query=fields_from_query)
        if 'data_loader' in result:
            result['data_loader'] = json_loads(result['data_loader'])
        if 'validators' in result:
            result['validators'] = json_loads(result['validators'])
        return result


class ValidatorRelationModel(BaseModel):
    id = AutoField(primary_key=True)
    wt_name = CharField(max_length=128, index=True)
    validator = CharField(index=True)
    params = TextField(null=True)
    update_time = DateTimeField(default=datetime.datetime.now)
    create_time = DateTimeField(default=datetime.datetime.now)

    class Meta:
        table_name = 'dw_validator_relation'
