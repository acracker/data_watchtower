#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import polars as pl
from attrs import define, field
from ..utils import connect_db_from_url

from .base import DataLoader


@define()
class DatabaseLoader(DataLoader):
    """
    使用playhouse.db_url连接数据库
    """
    query = field(type=str)
    connection = field(type=str)

    def _load(self):
        if pl.__version__ > '0.18.4':
            database = connect_db_from_url(self.connection)
            connection = database.connection()
            data = pl.read_database(self.query, connection=connection)
            connection.close()
            database.close()
            return data
        else:
            database = connect_db_from_url(self.connection)
            connection = database.connection()
            data = pd.read_sql(sql=self.query, con=connection)
            connection.close()
            database.close()
            return data
