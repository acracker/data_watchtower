#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import pytest
from data_watchtower.core import get_registered_validators, get_registered_data_loaders


def test_validator_schema():
    for cls in get_registered_validators():
        try:
            cls.to_schema()
        except Exception as e:
            logging.error("failed to get schema for %s" % cls.__name__, exc_info=e)
            assert cls.__name__ is None


def test_data_loader_schema():
    for cls in get_registered_data_loaders():
        try:
            cls.to_schema()
        except Exception as e:
            logging.error("failed to get schema for %s" % cls.__name__, exc_info=e)
            assert cls.__name__ is None
