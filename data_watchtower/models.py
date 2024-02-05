# coding: utf-8
from sqlalchemy import BigInteger, Column, DateTime, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, TEXT, TINYINT, VARCHAR
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class DwValidatorRunLog(Base):
    __tablename__ = 'dw_validator_run_logs'

    id = Column(BIGINT, primary_key=True)
    wt_id = Column(BIGINT)
    wt_run_id = Column(BigInteger)
    wt_name = Column(String(255))
    validator = Column(VARCHAR(255))
    success = Column(TINYINT)
    params = Column(Text)
    metrics = Column(Text)
    run_time = Column(DateTime)
    update_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    create_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


class DwWatchtower(Base):
    __tablename__ = 'dw_watchtower'

    id = Column(INTEGER, primary_key=True)
    wt_name = Column(VARCHAR(64))
    data_loader = Column(VARCHAR(255), comment='数据加载器')
    params = Column(TEXT, comment='加载器参数')
    params_schema = Column(TEXT, comment='参数schema')
    schedule = Column(VARCHAR(64), comment='调度时间')
    macro_names = Column(VARCHAR(255))
    update_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    create_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


class DwWtRunLog(Base):
    __tablename__ = 'dw_wt_run_logs'

    id = Column(BIGINT, primary_key=True)
    wt_id = Column(BigInteger, nullable=False)
    name = Column(VARCHAR(255))
    success = Column(Integer)
    run_time = Column(DateTime)
    macro_maps = Column(TEXT)
    metrics = Column(TEXT)
    update_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    create_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


class DwWtValidatorAssoc(Base):
    __tablename__ = 'dw_wt_validator_assoc'

    id = Column(Integer, primary_key=True)
    watchtower_id = Column(Integer)
    validator = Column(VARCHAR(255))
    validator_params = Column(TEXT)
    macro_names = Column(VARCHAR(255))
    update_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    create_time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
