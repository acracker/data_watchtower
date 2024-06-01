# data_watchtower

数据监控校验工具

在你的CTO发现问题前, 发现问题

## 安装

```
pip install data-watchtower
```

## 数据加载器

加载数据到内存中,供校验器使用

## 校验器

校验加载器加载的数据是否符合预期

### 内置加载器

* ExpectColumnValuesToNotBeNull
* ExpectColumnRecentlyUpdated
* ExpectColumnStdToBeBetween
* ExpectColumnMeanToBeBetween
* ExpectColumnNullRatioToBeBetween
* ExpectRowCountToBeBetween
* ExpectColumnDistinctValuesToContainSet
* ExpectColumnDistinctValuesToEqualSet
* ExpectColumnValuesToNotBeNull
* ExpectColumnDistinctValuesToBeInSet

### 自定义加载器

。。。

## 宏

通过自定义宏, 可以在监控项中引用一些自定义的变量, 比如日期, 配置文件等

### 生效范围

* Watchtower的名称
* 校验器的参数
* 数据加载器的参数

### 自定义宏

。。。

## 支持的数据库

* MySQL
* Postgresql
* SQLite
* ...

## 示例

```python
import datetime
from data_watchtower import (DbServices, Watchtower, DatabaseLoader,
                             ExpectRowCountToBeBetween, ExpectColumnValuesToNotBeNull)

dw_test_data_db_url = "sqlite:///test.db"
dw_backend_db_url = "sqlite:///data.db"

# 自定义宏模板
custom_macro_map = {
    'today': {'impl': lambda: datetime.datetime.today().strftime("%Y-%m-%d")},
    'start_date': '2024-04-01',
    'column': 'name',
}
# 设置数据加载器,用来加载需要校验的数据
query = "SELECT * FROM score where date='${today}'"
data_loader = DatabaseLoader(query=query, connection=dw_test_data_db_url)
data_loader.load()
# 创建监控项
wt = Watchtower(name='score of ${today}', data_loader=data_loader, custom_macro_map=custom_macro_map)
# 添加校验器
params = ExpectRowCountToBeBetween.Params(min_value=20, max_value=None)
wt.add_validator(ExpectRowCountToBeBetween(params))

params = ExpectColumnValuesToNotBeNull.Params(column='${column}')
wt.add_validator(ExpectColumnValuesToNotBeNull(params))

result = wt.run()
print(result['success'])

# 保存监控配置以及监控结果
db_svr = DbServices(dw_backend_db_url)
# 创建表
db_svr.create_tables()
# 保存监控配置
db_svr.add_watchtower(wt)
# 保存监控结果
db_svr.save_result(wt, result)
# 重新计算监控项的成功状态
db_svr.update_watchtower_success_status(wt)


```