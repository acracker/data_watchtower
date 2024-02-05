#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fastapi import HTTPException
from fastapi.responses import JSONResponse


class CustomHTTPException(HTTPException):
    def __init__(self, err_code: int = -1, err_msg: str = '', status_code: int = 418, headers=None):
        self.status_code = status_code
        self.err_code = err_code
        self.err_msg = err_msg
        self.headers = headers
