#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import asyncio

import tornado.web

from tornado.options import define, options
from data_watchtower import DbServices
from data_watchtower.api.url import URLS

default_db_url = os.getenv('DW_BACKEND_DB_URL', "sqlite:///data.db")
default_debug = os.getenv('DW_DEBUG', 'false').lower() in ('true', '1', 'yes')
define("port", default=8888, type=int, help="port to listen on")
define("db_url", default=default_db_url, help="db url")
define("debug", default=default_debug, type=bool, help="enable debug mode")


def make_app():
    database = DbServices(options.db_url)
    app = tornado.web.Application(
        URLS,
        database=database,
        debug=options.debug,
        autoreload=False,
    )
    return app


async def main():
    options.parse_command_line()
    app = make_app()
    app.listen(options.port)
    print("http://127.0.0.1:%s" % options.port)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
