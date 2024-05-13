#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .base import BaseHandler
from ...utils import get_subclasses
from ...core.base import get_registered_data_loaders


class DataLoaderListHandler(BaseHandler):
    def get(self):
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
