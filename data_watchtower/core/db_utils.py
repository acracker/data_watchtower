#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import datetime
import logging
from playhouse.shortcuts import model_to_dict

from data_watchtower.utils.macro import MacroTemplate, default_macro_config
from models import DwWatchtower, DwWtValidatorAssoc

logger = logging.getLogger(__name__)


def get_watchtower():
    columns = [
        DwWatchtower.wt_name,
        DwWatchtower.data_loader,
        DwWatchtower.params,
        DwWatchtower.macro_names,
        DwWatchtower.schedule,
    ]
    query = DwWatchtower.select(*columns)
    for handler in query:
        print(model_to_dict(handler))


def add_data_handler(name, data_loader, data_loader_params, schedule=None):
    inst = DwWatchtower(
        name=name, data_loader=data_loader,
        data_loader_params=data_loader_params,
        schedule=schedule,
        create_time=datetime.datetime.now(),
        update_time=datetime.datetime.now(),
    )
    return inst.save()


def add_validator_for_handler(handler_id, validator, params):
    handler = DwWatchtower.get_or_none(DwWatchtower.id == handler_id)
    if handler is None:
        return None
    params = params or {}
    macro = MacroTemplate(default_macro_config)
    macro_names = set()
    for k, v in params.items():
        if isinstance(v, str):
            macro_names.update(set(macro.get_using_macro_names(v)))
    inst = DwWtValidatorAssoc(
        data_handler_id=handler_id,
        validator=validator,
        validator_params=json.dumps(params),
        macro_names=json.dumps(list(macro_names)),
        create_time=datetime.datetime.now(),
        update_time=datetime.datetime.now(),
    )
    return inst.save()


def remove_validator_of_handler(handler_id, association_id):
    cond = ((DwWtValidatorAssoc.data_handler_id == handler_id)
            & (DwWtValidatorAssoc.id == association_id))
    DwWtValidatorAssoc.delete().where(cond)


def main():
    params = dict(
        sql=("SELECT `code`, `trading_day`,  `open`, `high`, `low`, `settle`, `close` FROM `t_eodprices` "
             "WHERE trading_day='${today}'   LIMIT ${n}")
    )
    # add_data_handler("test", 'loder2', {})
    # add_validator_for_handler(1, 'xx', params)
    # remove_validator_of_handler(1, 1)
    get_data_handler()


if __name__ == '__main__':
    main()
