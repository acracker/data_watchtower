#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .handlers import watchtower, data_loader, validator

URLS = [
    (r"/", validator.ValidatorListHandler),
    (r"/data_watchtower/v1/watchtower", watchtower.WatchtowerHandler),
    (r"/data_watchtower/v1/watchtower/validator", watchtower.ValidatorRelationHandler),
    (r"/data_watchtower/v1/watchtowers", watchtower.WatchtowerListHandler),
    (r"/data_watchtower/v1/data_loaders", data_loader.DataLoaderListHandler),
    (r"/data_watchtower/v1/validators", validator.ValidatorListHandler),

]
