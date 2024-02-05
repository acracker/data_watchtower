#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fastapi_crudrouter import SQLAlchemyCRUDRouter
from data_watchtower.schemas import WatchtowerCreate, Watchtower
from data_watchtower.models import DwWatchtower
from data_watchtower.database import get_db


router = SQLAlchemyCRUDRouter(
    schema=Watchtower,
    create_schema=WatchtowerCreate,
    db_model=DwWatchtower,
    db=get_db,
    prefix='potato'
)

