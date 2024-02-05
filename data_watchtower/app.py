#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from typing import Union
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi_pagination import Page, add_pagination, paginate

from data_watchtower.exceptions import CustomHTTPException
from data_watchtower.api import watchtower, wt


logger = logging.getLogger(__name__)


app = FastAPI()

add_pagination(app)


@app.exception_handler(CustomHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
            {"err_code": exc.err_code, "err_msg": exc.err_msg},
            status_code=exc.status_code,
            headers=exc.headers,
    )


if __name__ == "__main__":
    # CREATE USER `dw_user`@`%` IDENTIFIED WITH mysql_native_password BY 'Dw_user123!';
    import uvicorn
    app.include_router(watchtower.router)
    # app.include_router(wt.router)
    uvicorn.run(app, host="0.0.0.0", port=8000)
