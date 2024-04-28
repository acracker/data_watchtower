#!/usr/bin/env python
# -*- coding: utf-8 -*-
import polars as pl
from attrs import define, field
from .base import DataLoader


@define()
class DatabaseLoader(DataLoader):
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
