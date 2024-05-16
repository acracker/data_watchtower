#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .base import BaseHandler
from ...utils import get_subclasses
from ... import get_registered_validators


class ValidatorListHandler(BaseHandler):
    def get(self):
        data = []
        validators = get_registered_validators()
        for cls in validators:

            if isinstance(cls.__doc__, str):
                description = cls.__doc__.split("\f")[0].strip()
            else:
                description = ""
            row = dict(
                name=cls.__name__,
                module_path=cls.module_path(),
                schema=cls.to_schema(),
                description=description,
            )
            data.append(row)
        result = dict(
            records=data
        )
        self.json(result)
        return

    def post(self):
        return self.get()
