#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web
from data_watchtower.utils import json_dumps


class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, *args, **kwargs):
        self.database = self.settings.get('database')

    @staticmethod
    def json_dumps(data):
        return json_dumps(data)

    def json(self, data=None, error=None):
        if data is None:
            data = []
        if error is None:
            error = dict(
                err_code=0,
                err_msg="",
            )
        data = {
            'data': data,
            'error': error,
        }
        self.write(self.json_dumps(data))
