#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import datetime
import shortuuid
from peewee import fn, JOIN
from peewee import IntegrityError
from playhouse.db_url import connect
from data_watchtower.model.models import ValidationDetail, Watchtower, database_proxy
from data_watchtower.utils import json_dumps, json_loads

logger = logging.getLogger(__name__)


class DbServices(object):
    def __init__(self, connection):
        """
        可以使用db_url进行数据库连接. 用法: https://docs.peewee-orm.com/en/latest/peewee/playhouse.html#db-url
        或者直接使用peewee的Database对象
        :param connection:
            str: eg: sqlite:///data.db mysql://user:passwd@ip:port/my_db
            other: eg. MySQLDatabase, PostgresqlDatabase ...
        """
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
        return item

    def get_watchtowers(self):
        """
        获取所有的watchtower
        :return:
        """
        result = []
        query = Watchtower.select(
            Watchtower.name,
            Watchtower.success,
            Watchtower.run_time,
            Watchtower.data_loader,
            Watchtower.validators,
            Watchtower.success_method,
            Watchtower.validator_success_method,
        )
        for item in query:
            result.append(item.to_dict(fields_from_query=query))
        return result

    def add_watchtower(self, watchtower):
        update_time = datetime.datetime.now()
        try:
            with self.database.atomic():
                item = watchtower.to_dict()
                item['create_time'] = update_time
                item['update_time'] = update_time
                wt = Watchtower(**item)
                return wt.save(force_insert=True)
        except IntegrityError as e:
            logger.warning('add watchtower error!. msg:%s' % str(e))
            return None

    def update_watchtower(self, wt_name, **item):
        if len(item) == 0:
            return 0
        update_time = datetime.datetime.now()
        with self.database.atomic():
            wt = Watchtower.select().where(Watchtower.name == wt_name).get()
            if wt:
                if 'validators' in item:
                    wt.validators = json_dumps(item.pop('validators'))
                if 'data_loader' in item:
                    wt.validators = json_dumps(item.pop('data_loader'))
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
