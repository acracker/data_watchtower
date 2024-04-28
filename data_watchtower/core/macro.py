#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import datetime
from data_watchtower.core.utils import load_object

logger = logging.getLogger(__name__)

DEFAULT_MACRO_CONFIG = {
    'year:1': {'impl': lambda: datetime.datetime.now().strftime("%Y")},
    'today': {
        'impl': lambda: datetime.datetime.now().strftime("%Y%m%d"),
        'description': "今天的日期.格式:yyyymmdd",
    },
    'today:1': {
        'impl': lambda: datetime.datetime.now().strftime("%Y%m%d"),
        'description': "今天的日期.格式:yyyymmdd",
    },
    'today:2': {
        'impl': lambda: datetime.datetime.now().strftime("%Y-%m-%d"),
        'description': "今天的日期.格式:yyyy-mm-dd",
    },

    'yesterday': {
        'impl': lambda: (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d"),
        'description': "昨天的日期.格式:yyyymmdd",
    },
    'yesterday:1': {
        'impl': lambda: (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d"),
        'description': "昨天的日期.格式:yyyymmdd",
    },
    'yesterday:2': {
        'impl': lambda: (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d"),
        'description': "昨天的日期.格式:yyyy-mm-dd",
    },

}
try:
    custom_macro = load_object('macros:DEFAULT_MACRO_CONFIG')
    DEFAULT_MACRO_CONFIG.update(custom_macro)
    logger.info('custom macros loaded. count:%s' % len(custom_macro))
except (ModuleNotFoundError, NameError):
    pass
