#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import asyncio

import tornado.web

from tornado.options import define, options
from data_watchtower import DbServices
from data_watchtower.api.url import URLS

default_db_url = os.getenv('DW_DB_URL', "sqlite:///data.db")
define("port", default=8888, type=int, help="port to listen on")
define("db_url", default=default_db_url, help="db url")


def make_app():
    database = DbServices(options.db_url)
    app = tornado.web.Application(
        URLS,
        database=database
    )
    return app


async def main():
    options.parse_command_line()
    app = make_app()
    app.listen(options.port)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
