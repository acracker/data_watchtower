#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
跨表引用完整性检查示例

场景：商品基本信息表 + 商品买卖流水表
检查：流水表中的商品ID是否都在商品基本信息表中存在
"""
import os
import json
import random
import datetime
from faker import Faker
from peewee import *
from playhouse.db_url import connect
from data_watchtower import (
    DbServices, Watchtower, DatabaseLoader,
    ExpectColumnValuesToBeInReferenceColumn,
    ExpectRowCountToBeBetween,
)

_base_dir = os.path.dirname(os.path.abspath(__file__))
dw_test_data_db_url = os.getenv(
    'DW_TEST_DATA_DB_URL',
    'sqlite:///' + os.path.join(_base_dir, 'test.db'),
)
dw_backend_db_url = os.getenv(
    'DW_BACKEND_DB_URL',
    'sqlite:///' + os.path.join(_base_dir, 'data.db'),
)
database = connect(dw_test_data_db_url)


class BaseModel(Model):
    class Meta:
        database = database


class ProductInfo(BaseModel):
    """商品基本信息表"""
    product_id = CharField(unique=True)
    product_name = CharField()
    price = FloatField()


class TransactionFlow(BaseModel):
    """商品买卖流水表"""
    product_id = CharField()
    buyer = CharField()
    amount = IntegerField()
    trade_time = DateTimeField()


def gen_data():
    """生成测试数据，故意让部分流水记录引用不存在的商品"""
    with database:
        database.drop_tables([ProductInfo, TransactionFlow])
        database.create_tables([ProductInfo, TransactionFlow])

    fake = Faker(locale='zh_CN')

    # 创建商品
    product_ids = []
    for i in range(20):
        pid = f"P{i+1:04d}"
        product_ids.append(pid)
        ProductInfo.create(
            product_id=pid,
            product_name=fake.word(),
            price=round(random.uniform(10, 500), 2),
        )

    # 创建流水，故意混入不存在的商品ID
    orphan_ids = ["P9901", "P9902", "P9903"]
    all_ids = product_ids + orphan_ids

    for _ in range(100):
        TransactionFlow.create(
            product_id=random.choice(all_ids),
            buyer=fake.name(),
            amount=random.randint(1, 10),
            trade_time=datetime.datetime.now() - datetime.timedelta(hours=random.randint(0, 48)),
        )

    print(f"商品数: {len(product_ids)}, 流水数: 100, 孤儿商品ID: {orphan_ids}")


def main():
    # --- 示例1: 两边字段名相同 ---
    # DataLoader: 加载流水表中的商品ID（去重）
    flow_loader = DatabaseLoader(
        query="SELECT DISTINCT product_id FROM transactionflow",
        connection=dw_test_data_db_url,
    )

    # 参考数据源: 商品基本信息表（可配置 ttl_cache 缓存）
    ref_loader_config = json.dumps({
        "__class__": "data_watchtower.core.data_loaders:DatabaseLoader",
        "query": "SELECT DISTINCT product_id FROM productinfo",
        "connection": dw_test_data_db_url,
        "ttl_cache": 3600,
    })

    wt = Watchtower(name='商品引用完整性检查', data_loader=flow_loader)

    # 检查流水表的 product_id 是否都在商品表中
    validator = ExpectColumnValuesToBeInReferenceColumn.from_params(
        column="product_id",
        reference_data_loader=ref_loader_config,
    )
    wt.add_validator(validator)

    result = wt.run()
    print(f"\n--- 示例1: 相同字段名 ---")
    print(f"校验通过: {result['success']}")
    for vr in result['validators_result']:
        print(f"缺失数量: {vr.metrics['missing_count']}")
        print(f"缺失值: {vr.metrics['missing_values']}")

    # --- 示例2: 两边字段名不同 ---
    # 假设流水表用 pid，商品表用 product_id
    flow_loader2 = DatabaseLoader(
        query="SELECT DISTINCT product_id AS pid FROM transactionflow",
        connection=dw_test_data_db_url,
    )
    wt2 = Watchtower(name='商品引用完整性检查(不同字段名)', data_loader=flow_loader2)
    validator2 = ExpectColumnValuesToBeInReferenceColumn.from_params(
        column="pid",
        reference_column="product_id",
        reference_data_loader=ref_loader_config,
    )
    wt2.add_validator(validator2)

    result2 = wt2.run()
    print(f"\n--- 示例2: 不同字段名 ---")
    print(f"校验通过: {result2['success']}")
    for vr in result2['validators_result']:
        print(f"缺失数量: {vr.metrics['missing_count']}")
        print(f"缺失值: {vr.metrics['missing_values']}")

    # 保存到后端数据库
    db_svr = DbServices(dw_backend_db_url)
    db_svr.create_tables()
    db_svr.add_watchtower(wt)
    db_svr.save_result(wt, result)


if __name__ == '__main__':
    gen_data()
    main()
