#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from typing import Any, List, Union

import peewee
from pydantic import BaseModel


class WatchtowerCreate(BaseModel):
    wt_name: str
    data_loader: str
    params: str
    params_schema: str
    schedule: str
    macro_names: str


class Watchtower(WatchtowerCreate):
    id: int

    # class Config:
    #     from_attributes = True

