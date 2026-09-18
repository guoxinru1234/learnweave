# 数据加载(SQL/NoSQL/Parquet)

> 模块：ETL数据管道 | 编号：第34讲 | Python数据分析实战

---

## 1. 概念

数据加载（Data Loading）是ETL（Extract-Transform-Load）数据管道中的最后一个环节，指将经过抽取和转换后的数据写入目标存储系统的过程。目标存储系统可以是关系型数据库（SQL，如MySQL、PostgreSQL）、非关系型数据库（NoSQL，如MongoDB、Redis），也可以是列式存储文件（如Parquet、ORC）。

**生活化类比**：数据加载就像搬家。抽取（Extract）是把你所有物品从旧房子搬出来，转换（Transform）是分类打包、贴标签、处理破损物品，而加载（Load）则是把整理好的箱子按照规划摆放进新家的各个房间——有的放进储物柜（SQL数据库，结构化存放）、有的放进展示架（NoSQL数据库，灵活摆放）、有的放进密封仓库（Parquet文件，高效压缩存储）。

**适用场景**：
- **SQL加载**：数据需要强一致性、事务支持、复杂关联查询时，如订单系统、用户管理系统。
- **NoSQL加载**：数据结构灵活多变、需要高并发读写、海量数据分布式存储时，如日志系统、社交网络Feed流。
- **Parquet加载**：数据分析与机器学习场景，需要列式存储、高压缩比、与大数据生态（Spark、Hive）无缝集成时，如数据仓库的ODS层和DWD层。

---

## 2. 核心API与原理

| API/方法 | 签名 | 参数说明 | 返回值 | 核心原理 |
|---------|------|---------|--------|----------|
| `pandas.read_sql_query()` | `read_sql_query(sql, con, params=None)` | `sql`: SQL查询字符串；`con`: SQLAlchemy连接引擎或DBAPI连接；`params`: 查询参数（可选） | `DataFrame` | 将SQL查询结果集转换为DataFrame，底层通过DBAPI游标逐行获取数据 |
| `pandas.DataFrame.to_sql()` | `to_sql(name, con, schema=None, if_exists='fail', index=True)` | `name`: 目标表名；`con`: 连接引擎；`if_exists`: `'fail'`/`'replace'`/`'append'`；`index`: 是否写入索引 | `int`（受影响行数） | 将DataFrame批量写入SQL表，内部使用SQLAlchemy的`insert`多值语法 |
| `pymongo.MongoClient` + `collection.insert_many()` | `insert_many(documents, ordered=True)` | `documents`: 字典列表；`ordered`: 是否按顺序插入 | `InsertManyResult` | 将文档列表批量插入MongoDB集合，BSON序列化后通过MongoDB Wire Protocol传输 |
| `pandas.read_parquet()` | `read_parquet(path, engine='auto')` | `path`: 文件路径或文件对象；`engine`: `'pyarrow'`或`'fastparquet'` | `DataFrame` | 读取Parquet文件，利用列式存储的page索引和字典编码加速读取 |
| `pandas.DataFrame.to_parquet()` | `to_parquet(path, engine='pyarrow', compression='snappy')` | `path`: 输出路径；`engine`: 写入引擎；`compression`: 压缩算法（`'snappy'`/`'gzip'`/`'lz4'`） | `None` | 将DataFrame写入Parquet格式，按列分块压缩存储 |

---

## 3. 代码示例

### 示例1：SQL数据加载（基础）——从SQLite读取与写入

```python
import pandas as pd
import sqlite3

# 创建内存数据库连接
conn = sqlite3.connect(':memory:')

# 准备示例数据
df_source = pd.DataFrame({
    'user_id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35]
})

# 将DataFrame写入SQL表
df_source.to_sql('users', conn, if_exists='replace', index=False)
print("✅ 数据已写入SQLite表")

# 从SQL表读取数据
df_loaded = pd.read_sql_query("SELECT * FROM users WHERE age > 26", conn)
print("📊 查询结果（age > 26）：")
print(df_loaded)
# 输出:
#    user_id     name  age
# 0        2      Bob   30
# 1        3  Charlie   35

conn.close()
```

### 示例2：NoSQL数据加载（进阶）——MongoDB文档操作

```python
import pandas as pd
from pymongo import MongoClient
from datetime import datetime

# 连接本地MongoDB（需提前启动mongod服务）
client = MongoClient('mongodb://localhost:27017/')
db = client['etl_demo']
collection = db['user_logs']

# 构造待加载的日志数据
log_records = [
    {'user_id': 101, 'action': 'login', 'timestamp': datetime(2024, 1, 15, 10, 30)},
    {'user_id': 102, 'action': 'purchase', 'amount': 199.9, 'timestamp': datetime(2024, 1, 15, 10, 45)},
    {'user_id': 101, 'action': 'logout', 'timestamp': datetime(2024, 1, 15, 11, 0)}
]

# 批量插入文档
result = collection.insert_many(log_records)
print(f"✅ 已插入 {len(result.inserted_ids)} 条日志")

# 查询并转换为DataFrame
cursor = collection.find({'user_id': 101})
df_logs = pd.DataFrame(list(cursor))
print("📊 user_id=101 的日志：")
print(df_logs[['user_id', 'action', 'timestamp']])
# 输出:
#    user_id  action           timestamp
# 0      101   login 2024-01-15 10:30:00
# 1      101  logout 2024-01-15 11:00:00

# 清理
collection.drop()
client.close()
```

### 示例3：Parquet文件加载（综合）——列式存储的高效读写

```python
import pandas as pd
import numpy as np

# 生成模拟销售数据（10万行）
np.random.seed(42)
df_sales = pd.DataFrame({
    'order_id': np.arange(100000),
    'product': np.random.choice(['A', 'B', 'C', 'D'], 100000),
    'quantity': np.random.randint(1, 10, 100000),
    'price': np.round(np.random.uniform(10, 500, 100000), 2),
    'order_date': pd.date_range('2024-01-01', periods=100000, freq='min')
})

# 写入Parquet文件（带snappy压缩）
df_sales.to_parquet('sales.parquet', engine='pyarrow', compression='snappy')
print("✅ Parquet文件已写入，大小：", end="")

import os
size_mb = os.path.getsize('sales.parquet') / 1024 / 1024
print(f"{size_mb:.2f} MB")

# 读取Parquet文件，只加载部分列（列式存储的优势）
df_loaded = pd.read_parquet('sales.parquet', columns=['order_id', 'product', 'price'])
print("📊 读取3列数据，形状：", df_loaded.shape)
print(df_loaded.head(3))
# 输出:
#    order_id product   price
# 0         0       C  426.63
# 1         1       D  448.26
# 2         2       B  117.53

# 对比CSV文件大小（展示Parquet压缩优势）
df_sales.to_csv('sales.csv', index=False)
csv_size_mb = os.path.getsize('sales.csv') / 1024 / 1024
print(f"📈 CSV文件大小：{csv_size_mb:.2f} MB，Parquet压缩比：{csv_size_mb/size_mb:.1f}x")

# 清理文件
os.remove('sales.parquet')
os.remove('sales.csv')
```

---

## 4. 常见错误

### 错误1：`to_sql()` 写入时遇到 "Table already exists"

**错误原因**：目标表已存在，而`if_exists`参数默认值为`'fail'`，导致写入失败。

```python
# ❌ 错误写法
df.to_sql('users', conn)  # ValueError: Table 'users' already exists

# ✅ 正确写法
df.to_sql('users', conn, if_exists='append')   # 追加数据
# 或
df.to_sql('users', conn, if_exists='replace')  # 删除原表后重建
```

### 错误2：MongoDB连接超时或认证失败

**错误原因**：未指定`serverSelectionTimeoutMS`或认证参数，导致连接建立失败时抛出`ServerSelectionTimeoutError`。

```python
# ❌ 错误写法（无超时控制，可能长时间阻塞）
client = MongoClient('mongodb://localhost:27017/')

# ✅ 正确写法（设置超时和认证）
client = MongoClient(
    'mongodb://user:password@localhost:27017/',
    serverSelectionTimeoutMS=5000,  # 5秒超时
    authSource='admin'
)
# 连接前主动测试
client.admin.command('ping')  # 立即验证连接是否成功
```

### 错误3：Parquet读取时出现 `ArrowTypeError` 或 `ParquetDecodingError`

**错误原因**：Parquet文件中的数据类型与Pandas推断的类型不兼容，或文件损坏、引擎版本不匹配。

```python
# ❌ 错误写法（忽略引擎和类型问题）
df = pd.read_parquet('data.parquet')  # 可能抛出ArrowTypeError

# ✅ 正确写法（指定引擎并处理类型）
df = pd.read_parquet('data.parquet', engine='pyarrow')
# 如果仍有问题，检查列类型并显式转换
df['date_col'] = pd.to_datetime(df['date_col'], errors='coerce')
# 或使用fastparquet引擎尝试
# df = pd.read_parquet('data.parquet', engine='fastparquet')
```

---

## 5. 练习

### 练习1：混合数据管道——SQL到Parquet转换

**题目**：创建一个SQLite数据库，包含`orders`表（字段：`order_id`, `customer_id`, `amount`, `order_date`）。插入100条模拟数据后，完成以下任务：
1. 使用`read_sql_query`读取`amount > 100`的订单
2. 对读取的数据新增一列`discounted_amount = amount * 0.9`
3. 使用`to_parquet`将结果保存为`high_value_orders.parquet`
4. 验证：重新读取Parquet文件，确认行数和列数正确

**答案提示**：
```python
# 关键步骤
import sqlite3, pandas as pd, numpy as np

# 1. 建库建表插入数据
conn = sqlite3.connect('orders.db')
df_orders = pd.DataFrame({
    'order_id': range(1, 101),
    'customer_id': np.random.randint(1000, 2000, 100),
    'amount': np.round(np.random.uniform(50, 500, 100), 2),
    'order_date': pd.date_range('2024-01-01', periods=100)
})
df_orders.to_sql('orders', conn, if_exists='replace', index=False)

# 2. 读取并转换
df_high = pd.read_sql_query("SELECT * FROM orders WHERE amount > 100", conn)
df_high['discounted_amount'] = df_high['amount'] * 0.9

# 3. 写入Parquet
df_high.to_parquet('high_value_orders.parquet')

# 4. 验证
df_check = pd.read_parquet('high_value_orders.parquet')
assert len(df_check) == len(df_high), "行数不一致"
assert 'discounted_amount' in df_check.columns, "缺少折扣列"
print(f"✅ 验证通过，共{len(df_check)}条记录")
```

### 练习2：NoSQL与Parquet结合——日志分析管道

**题目**：假设MongoDB中有一个`web_events`集合，包含字段：`user_id`, `event_type`（`'click'`/`'view'`/`'purchase'`）, `page_url`, `event_time`。请设计一个ETL流程：
1. 从MongoDB抽取最近7天的`purchase`事件
2. 转换为DataFrame并添加`event_date`（从`event_time`提取日期）
3. 按`event_date`和`page_url`分组统计购买次数
4. 将统计结果加载为Parquet文件，并按日期分区存储（如`output/2024-01-15/`）

**答案提示**：
```python
# 关键步骤
from pymongo import MongoClient
import pandas as pd
from datetime import datetime, timedelta

# 1. 抽取（MongoDB聚合查询）
client = MongoClient('mongodb://localhost:27017/')
db = client['analytics']
seven_days_ago = datetime.now() - timedelta(days=7)
cursor = db['web_events'].find({
    'event_type': 'purchase',
    'event_time': {'$gte': seven_days_ago}
})

# 2. 转换
df_events = pd.DataFrame(list(cursor))
df_events['event_date'] = pd.to_datetime(df_events['event_time']).dt.date

# 3. 聚合
df_stats = df_events.groupby(['event_date', 'page_url']).size().reset_index(name='purchase_count')

# 4. 按日期分区加载为Parquet
for date, group in df_stats.groupby('event_date'):
    partition_path = f"output/{date}/purchase_stats.parquet"
    group.to_parquet(partition_path, engine='pyarrow')
    print(f"✅ 已写入 {partition_path}，{len(group)}条记录")
```

---

> **本讲小结**：数据加载是ETL管道的收尾环节，SQL适合强结构化数据、NoSQL适合灵活文档、Parquet适合分析型列式存储。掌握`read_sql_query`/`to_sql`、`pymongo`、`read_parquet`/`to_parquet`这五组核心API，即可覆盖绝大多数数据加载场景。实际项目中，建议结合数据量、查询模式、并发要求选择最合适的存储方案。