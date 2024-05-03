#!/usr/bin/env python
# -*- coding: utf-8 -*-
from attrs import define, field
from playhouse.db_url import connect

import polars as pl
from .base import DataLoader


@define()
class DatabaseLoaderCx(DataLoader):
    """
    使用connectorx连接数据库
    """
    query = field(type=str)
    connection = field(type=str)

    def _load(self):

        if isinstance(self.connection, str):
            try:
                return pl.read_database_uri(self.query, self.connection)
            except AttributeError:
                return pl.read_database(self.query, self.connection, engine='adbc')
        else:
            return pl.read_database(self.query, self.connection)


@define()
class DatabaseLoader(DataLoader):
    """
    使用playhouse.db_url连接数据库
    """
    query = field(type=str)
    connection = field(type=str)

    def _load(self):
        database = connect(self.connection)
        connection = database.connection()
        data = pl.read_database(self.query, connection=connection)
        connection.close()
        database.close()
        return data
