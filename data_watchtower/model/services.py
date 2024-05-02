#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from data_watchtower.model.models import *
from peewee import fn, JOIN
from playhouse.db_url import connect


def json_dumps(obj):
    def _default_encoder(obj):
        return str(obj)

    if isinstance(obj, str):
        return obj
    return json.dumps(obj, default=_default_encoder, ensure_ascii=True)


def json_loads(data):
    if isinstance(data, str):
        return json.loads(data)
    else:
        return data


class DbServices(object):
    def __init__(self, connection):
        if isinstance(connection, str):
            self.database = connect(url=connection)
        else:
            self.database = connection
        database_proxy.initialize(self.database)

    def create_tables(self):
        models = [Watchtower, ValidationDetail]
        with self.database:
            for model in models:
                if not self.database.table_exists(model):
                    self.database.create_tables([model])

    def get_watchtower(self, name):
        model = Watchtower.get(Watchtower.name == name).get()
        item = model.to_dict()
        if item is not None:
            item['data_loader'] = json_loads(item['data_loader'])
            item['validators'] = json_loads(item['validators'])
            item['custom_macro_map'] = json_loads(item['custom_macro_map'])
        return item

    def add_watchtower(self, watchtower):
        update_time = datetime.datetime.now()
        try:
            with self.database.atomic():
                wt = Watchtower(
                    name=watchtower.name,
                    data_loader=json_dumps(watchtower.get_loader_meta()),
                    validators=json_dumps(watchtower.get_validator_meta()),
                    custom_macro_map=json_dumps(watchtower.custom_macro_map),
                    validator_success_method=watchtower.validator_success_method,
                    success_method=watchtower.success_method,
                    create_time=update_time,
                    update_time=update_time,
                )
                return wt.save(force_insert=True)
        except IntegrityError as e:
            return None

    def update_watchtower(self, wt_name, **item):
        if len(item) == 0:
            return
        update_time = datetime.datetime.now()
        with self.database.atomic():
            wt = Watchtower.select().where(Watchtower.name == wt_name).get()
            if wt:
                if 'validators' in item:
                    wt.validators = json_dumps(item.pop('validators'))
                if 'data_loader' in item:
                    wt.validators = json_dumps(item.pop('data_loader'))
                if 'custom_macro_map' in item:
                    wt.validators = json_dumps(item.pop('custom_macro_map'))
                for k, v in item.items():
                    setattr(wt, k, v)
                wt.update_time = update_time
                return wt.save()
            else:
                return 0

    def delete_watchtower(self, watchtower):
        with self.database.atomic():
            wt = Watchtower.select().where(Watchtower.name == watchtower.wt_name).get()
            if wt:
                return wt.delete_instance()
            else:
                return 0

    def save_result(self, watchtower, result):
        update_time = datetime.datetime.now()
        records = []
        wt_name = watchtower.name
        run_id = shortuuid.uuid()
        row = dict(
            wt_name=wt_name,
            name=result['name'],
            success=result['success'],
            run_time=result['run_time'],
            macro_maps=json_dumps(result['macro_maps']),
            metrics=json_dumps(result['metrics']),
            params=None,
            run_id=run_id,
            run_type=1,
            update_time=update_time,
            create_time=update_time,
        )
        records.append(row)
        for item in result['validators_result']:
            row = dict(
                wt_name=wt_name,
                name=item.name,
                success=item.success,
                run_time=item.run_time,
                macro_maps=None,
                metrics=json_dumps(item.metrics),
                params=json_dumps(item.params),
                run_id=run_id,
                run_type=2,
                update_time=update_time,
                create_time=update_time,

            )
            records.append(row)
        with self.database.atomic():
            ValidationDetail.insert_many(records).execute()
        return

    def compute_watchtower_success_status(self, watchtower):
        wt_name = "日行情-${last_trading_day}"
        wt_name = watchtower.name
        success_method = watchtower.validator_success_method
        if success_method == 'all':
            DetailAlias = ValidationDetail.alias()
            DetailAliasBase = ValidationDetail.alias('base')
            join_query = DetailAlias.select(
                DetailAlias.name,
                fn.MAX(DetailAlias.run_time).alias('run_time')
            ).where(
                (DetailAlias.wt_name == wt_name) & (DetailAlias.run_type == 1)
            ).group_by(DetailAlias.name).alias('join_query')
            predicate = ((DetailAliasBase.name == join_query.c.name) &
                         (DetailAliasBase.run_time == join_query.c.run_time))
            cond = (DetailAliasBase.ignored == 0) & (DetailAliasBase.success == 0)
            query = DetailAliasBase.select(
                DetailAliasBase.run_id
            ).join(
                join_query, JOIN.INNER, on=predicate
            ).where(cond)
            return not query.exists()
        elif success_method == 'last':
            query = (
                ValidationDetail.select(ValidationDetail.success)
                .where((ValidationDetail.wt_name == wt_name) & (ValidationDetail.run_type == 1))
                .order_by(ValidationDetail.run_time.desc())
                .limit(1)
            )
            item = query.get()
            if item:
                return True
            else:
                return item.success
        else:
            raise ValueError('success_method error. value:%s' % success_method)

    def update_watchtower_success_status(self, watchtower):
        run_time = datetime.datetime.now()
        success = self.compute_watchtower_success_status(watchtower)
        self.update_watchtower(watchtower.name, success=success, run_time=run_time)


def main():
    from data_watchtower import Watchtower
    svr = DbServices()
    # svr.foo()
    x = svr.get_watchtower('日行情-${last_trading_day}')
    ww = Watchtower.from_dict(x)
    r = ww.run()
    svr.update_watchtower_success_status(ww)
    return


if __name__ == '__main__':
    main()
