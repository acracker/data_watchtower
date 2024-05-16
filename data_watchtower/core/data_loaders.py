#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from functools import lru_cache

import pandas as pd
import polars as pl
from attrs import define, field

from .base import DataLoader
from ..utils import connect_db_from_url, get_subclasses, load_subclasses

CUSTOM_DATA_LOADER_PATH = os.getenv("DW_CUSTOM_DATA_LOADER_PATH", "dw_custom.data_loaders")


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


@lru_cache()
def get_registered_data_loader_maps():
    custom_path = CUSTOM_DATA_LOADER_PATH.split(";")
    subclasses = get_subclasses(DataLoader)
    try:
        custom_subclasses = load_subclasses(custom_path, DataLoader)
    except ModuleNotFoundError:
        custom_subclasses = []
    result = {}
    for cls in (subclasses + custom_subclasses):
        cls_name = cls.__name__
        if cls_name in result:
            raise ValueError("Duplicate data loader name: %s" % cls_name)
        else:
            result[cls.__name__] = cls
    return result


def get_registered_data_loaders():
    result = get_registered_data_loader_maps()
    return list(result.values())
