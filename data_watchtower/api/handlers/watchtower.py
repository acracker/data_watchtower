#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .base import BaseHandler
from ...core.watchtower import Watchtower
from ... import get_registered_data_loader_maps
from ...core import get_registered_validators, get_registered_validator_maps


class WatchtowerHandler(BaseHandler):
    def get(self):
        name = self.get_argument('name')
        wt = self.database.get_watchtower(name)

        if not wt:
            self.json(error={'err_code': 1001, 'err_msg': 'watchtower not found'})
            return
        item = wt.to_dict()
        if isinstance(item.get('params'), dict):
            for k, v in item['params'].items():
                item[k] = v
            del item['params']
        result = dict(
            data=item
        )
        return self.json(result)

    def post(self):
        params = self.json_loads(self.request.body)
        data_loader_maps = get_registered_data_loader_maps()
        data_loader_cls = data_loader_maps[params.pop('data_loader_cls')]
        data_loader = data_loader_cls.from_dict(params.pop('data_loader_params'))
        watchtower = Watchtower(name=params.pop('name'), data_loader=data_loader, **params)
        self.database.add_watchtower(watchtower)
        return self.json([])

    def put(self):
        params = self.json_loads(self.request.body)
        data_loader_maps = get_registered_data_loader_maps()
        data_loader_cls = data_loader_maps[params.pop('data_loader_cls')]
        data_loader = data_loader_cls.from_dict(params.pop('data_loader_params'))
        watchtower = Watchtower(name=params.pop('name'), data_loader=data_loader, **params)
        item = watchtower.to_dict()
        self.database.update_watchtower(item.pop('name'), **item)
        return self.json([])


class WatchtowerListHandler(BaseHandler):
    def get(self):
        data = self.database.get_watchtowers()
        for item in data:
            data_loader = item['data_loader']
            if isinstance(data_loader, dict):
                item['data_loader'] = data_loader.pop('__class__')
                item['data_loader_cls'] = item['data_loader'].split(':')[-1]
                item['data_loader_params'] = data_loader
                data_loader_maps = get_registered_data_loader_maps()
                # todo 如果data_loader被删除， 则会报错
                data_loader_cls = data_loader_maps[item['data_loader_cls']]
                item['data_loader_schema'] = data_loader_cls.to_schema()
            if isinstance(item.get('params'), dict):
                for k, v in item['params'].items():
                    item[k] = v
                del item['params']
        result = dict(
            records=data
        )
        self.json(result)
        return

    def post(self):
        return self.get()


class ValidatorRelationHandler(BaseHandler):
    def post(self):
        """
        处理POST请求，用于向数据库中的watchtower添加新的validator。

        接收JSON格式的请求体，包含watchtower的名称（name）、validator的类名（validator），
        以及validator的参数（params）。然后根据这些信息，从数据库中获取对应的watchtower，
        实例化指定的validator，并将其添加到watchtower中。

        参数:
        - 无

        返回值:
        - 如果操作成功，返回一个空的JSON对象；如果watchtower或validator未找到，返回包含错误信息的JSON对象。
        """

        # 从请求体中加载JSON数据
        data = self.json_loads(self.request.body)
        name = data['name']  # watchtower的名称
        validator_class_name = data['validator']  # validator的类名
        params = data['params']  # validator的参数

        # 尝试从数据库获取指定名称的watchtower
        wt = self.database.get_watchtower(name)
        if not wt:
            # 如果watchtower未找到，返回错误信息
            self.json(error={'err_code': 1001, 'err_msg': 'watchtower not found'})
            return

        # 获取注册的validator类
        validator_cls = get_registered_validator_maps().get(validator_class_name)
        if validator_cls is None:
            # 如果validator类未找到，返回错误信息
            self.json(error={'err_code': 1002, 'err_msg': 'validator not found'})
            return

        # 实例化validator，并将其转换为字典格式
        validator = validator_cls.from_params(**params)
        validator_item = validator.to_dict()

        # 从validator字典中提取类名和参数，准备添加到数据库
        validator = validator_item['__class__']
        params = self.json_dumps(validator_item['params'])

        # 将validator添加到watchtower中
        self.database.add_validator_to_watchtower(name, validator, params)

        # 返回成功的JSON响应
        return self.json()
