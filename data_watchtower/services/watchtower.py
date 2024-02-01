#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import datetime
from playhouse.shortcuts import model_to_dict

from data_watchtower.utils.macro import MacroTemplate, default_macro_config
from data_watchtower.core.models import DwWatchtower, DwWtValidatorAssoc

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
    result = []
    for item in query:
        result.append(model_to_dict(item, only=columns))
    return result


def add_watchtower(wt_name, data_loader, data_loader_params, schedule=None):
    inst = DwWatchtower(
        wt_name=wt_name,
        data_loader=data_loader,
        params=data_loader_params,
        schedule=schedule,
        create_time=datetime.datetime.now(),
        update_time=datetime.datetime.now(),
    )
    return inst.save()


def add_validator_for_watchtower(watchtower_id, validator, params):
    watchtower = DwWatchtower.get_or_none(DwWatchtower.id == watchtower_id)
    if watchtower is None:
        return None
    params = params or {}
    macro = MacroTemplate(default_macro_config)
    macro_names = set()
    for k, v in params.items():
        if isinstance(v, str):
            macro_names.update(set(macro.get_using_macro_names(v)))
    inst = DwWtValidatorAssoc(
        watchtower_id=watchtower_id,
        validator=validator,
        validator_params=json.dumps(params),
        macro_names=json.dumps(list(macro_names)),
        create_time=datetime.datetime.now(),
        update_time=datetime.datetime.now(),
    )
    return inst.save()


def remove_validator_of_watchtower(watchtower_id, association_id):
    cond = ((DwWtValidatorAssoc.data_watchtower_id == watchtower_id)
            & (DwWtValidatorAssoc.id == association_id))
    DwWtValidatorAssoc.delete().where(cond)


def main():
    import pprint
    params = dict(
        sql=("SELECT `code`, `trading_day`,  `open`, `high`, `low`, `settle`, `close` FROM `t_eodprices` "
             "WHERE trading_day='${today}'   LIMIT ${n}")
    )
    # add_data_watchtower("test", 'loder2', {})
    # add_validator_for_watchtower(1, 'xx', params)
    # remove_validator_of_watchtower(1, 1)
    pprint.pp(get_watchtower())


if __name__ == '__main__':
    main()
