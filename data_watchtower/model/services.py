#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import datetime
import shortuuid
from peewee import fn, JOIN, DoesNotExist
from peewee import IntegrityError
from data_watchtower import DataLoader
from data_watchtower.model.models import ValidationDetailModel, WatchtowerModel, database_proxy, ValidatorRelationModel
from data_watchtower.utils import json_dumps, json_loads, connect_db_from_url

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
            self.database = connect_db_from_url(url=connection)
        else:
            self.database = connection
        database_proxy.initialize(self.database)

    def create_tables(self):
        models = [WatchtowerModel, ValidationDetailModel, ValidatorRelationModel]
        with self.database:
            for model in models:
                if not self.database.table_exists(model):
                    self.database.create_tables([model])

    def get_watchtower(self, name):
        try:
            model = WatchtowerModel.get(WatchtowerModel.name == name).get()
        except DoesNotExist:
            return None
        item = model.to_dict()
        item['params'] = json_loads(item['params'])
        item['data_loader'] = json_loads(item['data_loader'])
        validators = ValidatorRelationModel.select().where(ValidatorRelationModel.wt_name == name)
        item['validators'] = []
        for validator_item in validators:
            validator = dict(
                params=json_loads(validator_item.params),
                __class__=validator_item.validator,
            )
            item['validators'].append(validator)
        return item

    def get_watchtowers(self):
        """
        获取所有的watchtower
        :return:
        """
        result = []
        query = WatchtowerModel.select(
            WatchtowerModel.name,
            WatchtowerModel.success,
            WatchtowerModel.run_time,
            WatchtowerModel.data_loader,
            WatchtowerModel.params,
        )
        for item in query:
            row = item.to_dict(fields_from_query=query)
            row['params'] = json_loads(row['params'])
            result.append(row)
        return result

    def add_watchtower(self, watchtower):
        update_time = datetime.datetime.now()
        try:
            with self.database.atomic():
                item = watchtower.to_dict()
                item['create_time'] = update_time
                item['update_time'] = update_time
                wt = WatchtowerModel(**item)
                wt.save(force_insert=True)
                validators = []
                for validator_item in watchtower.get_validator_meta():
                    inst = ValidatorRelationModel(
                        wt_name=watchtower.name,
                        validator=validator_item['__class__'],
                        params=json_dumps(validator_item['params']),
                    )
                    validators.append(inst)
                ValidatorRelationModel.bulk_create(validators, batch_size=100)
        except IntegrityError as e:
            logger.warning('add watchtower error!. msg:%s' % str(e))
            return

    def update_watchtower(self, name, **item):
        if len(item) == 0:
            return 0
        update_time = datetime.datetime.now()
        with self.database.atomic():
            wt = WatchtowerModel.select().where(WatchtowerModel.name == name).get()
            if wt:
                if 'data_loader' in item:
                    data_loader = item.pop('data_loader')
                    if isinstance(data_loader, DataLoader):
                        data_loader = data_loader.to_dict()
                    wt.data_loader = json_dumps(data_loader)
                if 'params' in item:
                    wt.params = json_dumps(item.pop('params'))
                for k, v in item.items():
                    setattr(wt, k, v)
                wt.update_time = update_time
                return wt.save()
            else:
                return 0

    def delete_watchtower(self, name):
        with self.database.atomic():
            try:
                wt = WatchtowerModel.select().where(WatchtowerModel.name == name).get()
            except DoesNotExist:
                return 0
            return wt.delete_instance()

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
            ValidationDetailModel.insert_many(records).execute()
        self.update_watchtower_success_status(watchtower)
        return

    def compute_watchtower_success_status(self, watchtower):
        wt_name = watchtower.name
        success_method = watchtower.validator_success_method
        if success_method == 'all':
            DetailAlias = ValidationDetailModel.alias()
            DetailAliasBase = ValidationDetailModel.alias('base')
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
                ValidationDetailModel.select(ValidationDetailModel.success)
                .where((ValidationDetailModel.wt_name == wt_name) & (ValidationDetailModel.run_type == 1))
                .order_by(ValidationDetailModel.run_time.desc())
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

    def add_validator_to_watchtower(self, wt_name, validator, params):
        inst = ValidatorRelationModel(
            wt_name=wt_name,
            validator=validator,
            params=params,
        )
        return inst.save(force_insert=True)

    def get_validators_of_watchtower(self, name):
        """
        获取watchtower下的所有validator
        :param name:
        :return:
        """
        validators = ValidatorRelationModel.select().where(ValidatorRelationModel.wt_name == name)
        result = []
        for validator_item in validators:
            validator = dict(
                params=json_loads(validator_item.params),
                __class__=validator_item.validator,
            )
            result.append(validator)
        return result
