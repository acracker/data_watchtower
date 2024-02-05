#!/usr/bin/env python
# -*- coding: utf-8 -*-
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import datetime
from sqlalchemy import select


from playhouse.shortcuts import model_to_dict
from fastapi_pagination.ext.sqlalchemy import paginate

from data_watchtower.utils.macro import MacroTemplate, default_macro_config
from data_watchtower import models
from data_watchtower.database import SessionLocal

logger = logging.getLogger(__name__)


def get_watchtower():
    session = SessionLocal()
    query = select(models.DwWatchtower)
    return paginate(session, query)


def paginate_watchtowers(db):
    query = select(models.DwWatchtower)
    return paginate(db, query)


def add_watchtower(db, watchtower):
    inst = models.DwWatchtower(
        wt_name=watchtower.wt_name,
        data_loader=watchtower.data_loader,
        params=watchtower.params,
        params_schema=watchtower.params_schema,
        macro_names=watchtower.macro_names,
        schedule=watchtower.schedule,
        create_time=datetime.datetime.now(),
        update_time=datetime.datetime.now(),
    )
    db.add(inst)
    db.flush()
    # db.refresh(inst)
    return inst


def add_validator_for_watchtower(db, watchtower_id, validator, params):
    watchtower = db.query(models.DwWatchtower).filter(models.DwWatchtower.id == watchtower_id).first()
    if watchtower is None:
        return None
    params = params or {}
    macro = MacroTemplate(default_macro_config)
    macro_names = set()
    for k, v in params.items():
        if isinstance(v, str):
            macro_names.update(set(macro.get_using_macro_names(v)))
    inst = models.DwWtValidatorAssoc(
        watchtower_id=watchtower_id,
        validator=validator,
        validator_params=json.dumps(params),
        macro_names=json.dumps(list(macro_names)),
        create_time=datetime.datetime.now(),
        update_time=datetime.datetime.now(),
    )
    db.add(inst)
    db.flush()
    return inst


def remove_validator_of_watchtower(watchtower_id, association_id):
    cond = ((models.DwWtValidatorAssoc.data_watchtower_id == watchtower_id)
            & (models.DwWtValidatorAssoc.id == association_id))
    models.DwWtValidatorAssoc.delete().where(cond)


def save_run_log(db, wt_id, run_log):
    wt_name = run_log['name']
    inst = models.DwWtRunLog(
        wt_id=wt_id,
        name=run_log['name'],
        run_time=run_log['run_time'],
        macro_maps=json.dumps(run_log['macro_maps']),
        metrics=json.dumps(run_log['metrics']),
        success=int(run_log['success']),
    )
    db.add(inst)
    db.flush()
    wt_run_id = inst.id
    for item in run_log['validators_result']:
        inst = models.DwValidatorRunLog(
            wt_id=wt_id,
            wt_run_id=wt_run_id,
            wt_name=wt_name,
            validator=item['validator'],
            params=json.dumps(item['params']),
            metrics=json.dumps(item['metrics']),
            run_time=item['run_time'],
            success=int(item['success']),
        )
        db.add(inst)
    db.commit()


def main():
    from data_watchtower.database import SessionLocal
    import pprint
    db = SessionLocal()
    r = db.query(models.DwWatchtower).filter(models.DwWatchtower.id == 1).first()
    params = dict(
        sql=("SELECT `code`, `trading_day`,  `open`, `high`, `low`, `settle`, `close` FROM `t_eodprices` "
             "WHERE trading_day='${today}'   LIMIT ${n}")
    )
    # add_data_watchtower("test", 'loader2', {})
    add_validator_for_watchtower(1, 'xx', params)
    # remove_validator_of_watchtower(1, 1)
    pprint.pp(get_watchtower())


if __name__ == '__main__':
    main()
