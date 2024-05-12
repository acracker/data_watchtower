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
        result = dict(
            data=wt.to_dict()
        )
        return self.json(result)

    def post(self):
        params = self.json_loads(self.request.body)
        data_loader_maps = get_get_registered_data_loader_maps()
        data_loader_cls = data_loader_maps[params['data_loader_cls']]
        data_loader = data_loader_cls.from_dict(params['data_loader_params'])
        watchtower = Watchtower(name=params['name'], data_loader=data_loader)
        self.database.add_watchtower(watchtower)
        return self.json([])


class WatchtowerListHandler(BaseHandler):
    def get(self):
        data = self.database.get_watchtowers()
        for item in data:
            params = item['data_loader']
            item['data_loader'] = params.pop('__class__')
            item['data_loader_cls'] = item['data_loader'].split(':')[-1]
            item['data_loader_params'] = params
        result = dict(
            records=data
        )
        self.json(result)
        return

    def post(self):
        return self.get()
