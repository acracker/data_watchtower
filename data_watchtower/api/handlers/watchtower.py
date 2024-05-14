#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .base import BaseHandler
from ...core.watchtower import Watchtower
from ...core.base import get_get_registered_data_loader_maps


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
        data_loader_maps = get_get_registered_data_loader_maps()
        data_loader_cls = data_loader_maps[params.pop('data_loader_cls')]
        data_loader = data_loader_cls.from_dict(params.pop('data_loader_params'))
        watchtower = Watchtower(name=params.pop('name'), data_loader=data_loader, **params)
        self.database.add_watchtower(watchtower)
        return self.json([])

    def put(self):
        params = self.json_loads(self.request.body)
        data_loader_maps = get_get_registered_data_loader_maps()
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
                data_loader_maps = get_get_registered_data_loader_maps()
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


class DataLoaderListHandler(BaseHandler):
    def get(self):
        name = self.get_argument('name')
        data = []
        data_loaders = get_registered_data_loaders()
        for cls in data_loaders:
            row = dict(
                name=cls.__name__,
                module_path=cls.module_path(),
                schema=cls.to_schema(),
            )
            data.append(row)
        result = dict(
            records=data
        )
        self.json(result)
        return

    def post(self):
        return self.get()
