# data_watchtower

数据监控校验工具
在你的CTO发现问题前, 发现问题

```python
import datetime
from data_watchtower import (DbServices, Watchtower, DatabaseLoader,
                             ExpectRowCountToBeBetween, ExpectColumnValuesToNotBeNull)

# 自定义宏模板
custom_macro_map = {
    'today': {'impl': lambda: datetime.datetime.today().strftime("%Y-%m-%d")},
    'start_date': '2024-04-01',
}
# 设置数据加载器,用来加载需要校验的数据
connection = 'sqlite://test.db'
query = "SELECT * FROM score where date='${today}'"
data_loader = DatabaseLoader(query=query, connection=connection)

# 创建监控项
wt = Watchtower(name='score of ${today}', data_loader=data_loader, custom_macro_map=custom_macro_map)
# 添加校验器
params = ExpectRowCountToBeBetween.Params(min_value=20, max_value=None)
wt.add_validator(ExpectRowCountToBeBetween(params))

params = ExpectColumnValuesToNotBeNull.Params(column='name')
wt.add_validator(ExpectColumnValuesToNotBeNull(params))

result = wt.run()
print(result['success'])

# 保存监控配置以及监控结果
db_svr = DbServices("sqlite:///data.db")
# 创建表
db_svr.create_tables()
# 保存监控配置
db_svr.add_watchtower(wt)
# 保存监控结果
db_svr.save_result(wt, result)
# 重新计算监控项的成功状态
db_svr.compute_watchtower_success_status(wt)

```