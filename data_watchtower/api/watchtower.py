#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Any, List, Union
from fastapi import APIRouter, Query, Depends
from fastapi_pagination import Page

from data_watchtower.database import get_db
from data_watchtower.services import paginate_watchtowers, add_watchtower
from data_watchtower import schemas
from data_watchtower.exceptions import CustomHTTPException

router = APIRouter(
    prefix="/watchtower",
    tags=["items"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=Page[schemas.Watchtower])
def _get_watchtowers(db=Depends(get_db)):
    watchtowers = paginate_watchtowers(db)
    return watchtowers


@router.post("/add", response_model=schemas.Watchtower)
def _add_watchtower(wt: schemas.WatchtowerCreate, db=Depends(get_db)):
    return add_watchtower(db, wt)


@router.get("/err")
async def err():
    raise CustomHTTPException(err_msg="aabbcc")
