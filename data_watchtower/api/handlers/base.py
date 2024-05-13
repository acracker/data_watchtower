#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import tornado.web
from data_watchtower.utils import json_dumps, json_loads

logger = logging.getLogger(__name__)


class BaseHandler(tornado.web.RequestHandler):
    def _handle_request_exception(self, e):
        logger.exception(e)
        self.json(error={'err_code': 1, 'err_msg': str(e)})
        self.finish()
        return

    def set_default_headers(self) -> None:
        """
        设置允许跨域header
        :return:
        """
        super().set_default_headers()
        if self.application.settings['debug']:
            origin = self.request.headers.get('Referer')
            if origin:
                idx = origin.find('/', origin.find('//') + 2)
                origin = origin[:idx]
            origin = origin or "%s://%s" % (self.request.protocol, self.request.host)
            allow_headers = "Accept, Authorization, Cache-Control, Content-Type, DNT, If-Modified-Since, " \
                            "Keep-Alive, Origin, User-Agent, X-Requested-With, Token, x-access-token, " \
                            "X-Requested-With, yitoulogintoken "
            self.set_header("Access-Control-Allow-Origin", origin)
            self.set_header("Access-Control-Allow-Credentials", "true")
            self.set_header("Access-Control-Allow-Headers", allow_headers)
            self.set_header("Access-Control-Allow-Methods", "GET,POST,PUT,POST,DELETE,OPTIONS")

    def options(self, *args, **kwargs):
        return self.json()


    def initialize(self, *args, **kwargs):
        self.database = self.settings.get('database')

    @staticmethod
    def json_dumps(data):
        return json_dumps(data)

    @staticmethod
    def json_loads(data):
        return json_loads(data)

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
        }
        data.update(error)
        self.write(self.json_dumps(data))
