#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .handlers import watchtower

URLS = [
    (r"/", watchtower.WatchtowerHandler),
]
