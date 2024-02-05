#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from sqlalchemy import MetaData
from sqlalchemy import create_engine

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}
metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)


DATABASE_URL = os.getenv('DW_DB_URL')

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=create_engine(DATABASE_URL)
)

# AsyncSessionLocal = sessionmaker(
#     class_=AsyncSession,
#     autocommit=False,
#     autoflush=False,
#     bind=create_async_engine(AIO_DATABASE_URL))


Base = declarative_base()


def get_db():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    finally:
        session.close()
