from peewee import *

database = SqliteDatabase(r'D:\code\data_watchtower\data.db')


class UnknownField(object):
    def __init__(self, *_, **__): pass


class BaseModel(Model):
    class Meta:
        database = database


class DwRunLogs(BaseModel):
    create_time = DateField(null=True)
    macro_maps = TextField(null=True)
    name = TextField(null=True)
    run_time = DateField(null=True)
    success = IntegerField(null=True)
    update_time = DateField(null=True)

    class Meta:
        table_name = 'dw_run_logs'


class DwWatchtower(BaseModel):
    create_time = DateField(null=True)
    data_loader = TextField(null=True)
    macro_names = TextField(null=True)
    params = TextField(null=True)
    params_schema = TextField(null=True)
    schedule = TextField(null=True)
    update_time = DateField(null=True)
    wt_name = TextField(null=True)

    class Meta:
        table_name = 'dw_watchtower'


class DwWtValidatorAssoc(BaseModel):
    create_time = DateField(null=True)
    macro_names = TextField(null=True)
    update_time = DateField(null=True)
    validator = TextField(null=True)
    validator_params = TextField(null=True)
    watchtower_id = IntegerField(null=True)

    class Meta:
        table_name = 'dw_wt_validator_assoc'


class SqliteSequence(BaseModel):
    name = BareField(null=True)
    seq = BareField(null=True)

    class Meta:
        table_name = 'sqlite_sequence'
        primary_key = False
