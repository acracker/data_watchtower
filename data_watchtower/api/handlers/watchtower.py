#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .base import BaseHandler


class WatchtowerHandler(BaseHandler):
    def get(self):
        name = self.get_argument('name')
        wt = self.database.get_watchtower(name)
        if not wt:
            self.json(error={'err_code': 1001, 'err_msg': 'watchtower not found'})
            return
        return self.json(wt.to_dict())


class WatchtowerListHandler(BaseHandler):
    def get(self):
        data = self.database.get_watchtowers()
        self.json(data)
        return
