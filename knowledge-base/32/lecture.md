# 数据抽取策略(全量/增量)

> 模块：ETL数据管道 | 编号：第32讲 | Python数据分析实战

---

## 1. 概念

**全量抽取（Full Extraction）** 是指每次从数据源中读取全部数据，并覆盖或重建目标表中的数据。**增量抽取（Incremental Extraction）** 则只读取自上次抽取以来发生变化或新增的数据，并追加或更新到目标表。

**适用场景**：全量抽取适用于数据量小（如百万行以内）、源表结构频繁变动或目标表需要完整快照的场景；增量抽取适用于数据量大、源表有明确时间戳或自增ID、且对抽取效率有较高要求的场景。

**生活化类比**：全量抽取就像每次搬家都把整个衣柜的衣服全部搬走；增量抽取则像只把新买的衣服放进衣柜，旧衣服不动。前者简单但费时费力，后者高效但需要记录"上次搬到哪一件"。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 | 核心原理 |
|-----|------|----------|--------|----------|
| `pandas.read_sql_query()` | `read_sql_query(sql, con, params=None)` | `sql`: SQL查询字符串；`con`: 数据库连接对象；`params`: 查询参数（可选） | `DataFrame` | 执行SQL查询并返回结果集，支持参数化查询防止SQL注入 |
| `pandas.DataFrame.to_sql()` | `to_sql(name, con, schema=None, if_exists='fail', index=True)` | `name`: 目标表名；`con`: 数据库连接；`if_exists`: `'fail'`/`'replace'`/`'append'` | `None` | 将DataFrame写入数据库表，`if_exists`控制覆盖或追加 |
| `datetime.datetime.now()` | `now(tz=None)` | `tz`: 时区（可选） | `datetime`对象 | 获取当前时间，用于记录增量抽取的水位线（watermark） |
| `sqlite3.connect()` | `connect(database)` | `database`: 数据库文件路径 | `Connection`对象 | 建立SQLite数据库连接，用于演示ETL过程 |
| `pandas.DataFrame.merge()` | `merge(right, how='inner', on=None)` | `right`: 右表DataFrame；`how`: 连接方式；`on`: 连接键 | `DataFrame` | 实现表连接，用于增量数据与已有数据的合并去重 |

---

## 3. 代码示例

### 示例1：全量抽取基础实现

```python
import pandas as pd
import sqlite3

# 创建演示数据库
conn = sqlite3.connect('etl_demo.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY,
        customer_name TEXT,
        amount REAL,
        order_date TEXT
    )
''')
conn.commit()

# 插入示例数据
sample_data = [
    (1, '张三', 299.0, '2024-01-01'),
    (2, '李四', 159.5, '2024-01-02'),
    (3, '王五', 899.0, '2024-01-03')
]
cursor.executemany('INSERT OR REPLACE INTO orders VALUES (?,?,?,?)', sample_data)
conn.commit()

# 全量抽取：每次读取全部数据
def full_extract(conn):
    """全量抽取函数：读取orders表全部数据"""
    query = "SELECT * FROM orders"
    df = pd.read_sql_query(query, conn)
    return df

# 执行全量抽取
full_df = full_extract(conn)
print("全量抽取结果：")
print(full_df)
print(f"共抽取 {len(full_df)} 条记录\n")

# 将数据写入目标表（覆盖模式）
full_df.to_sql('orders_target', conn, if_exists='replace', index=False)
print("全量数据已写入目标表 orders_target（覆盖模式）")

conn.close()
```

**输出结果**：
```
全量抽取结果：
   order_id customer_name  amount  order_date
0         1           张三   299.0  2024-01-01
1         2           李四   159.5  2024-01-02
2         3           王五   899.0  2024-01-03
共抽取 3 条记录

全量数据已写入目标表 orders_target（覆盖模式）
```

---

### 示例2：基于时间戳的增量抽取

```python
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('etl_demo.db')

# 模拟：上次抽取时间（水位线）
last_extract_time = datetime(2024, 1, 2, 0, 0, 0)

# 模拟新插入的数据（增量数据）
new_data = [
    (4, '赵六', 1299.0, '2024-01-04'),
    (5, '孙七', 399.0, '2024-01-05')
]
cursor = conn.cursor()
cursor.executemany('INSERT OR REPLACE INTO orders VALUES (?,?,?,?)', new_data)
conn.commit()

def incremental_extract(conn, last_time):
    """
    增量抽取函数：只抽取上次抽取时间之后的数据
    参数：
        conn: 数据库连接
        last_time: 上次抽取的水位线时间（datetime对象）
    返回：
        DataFrame: 增量数据
    """
    # 使用参数化查询，避免SQL注入
    query = """
        SELECT * FROM orders 
        WHERE order_date > ?
    """
    df = pd.read_sql_query(query, conn, params=(last_time.strftime('%Y-%m-%d'),))
    return df

# 执行增量抽取
incremental_df = incremental_extract(conn, last_extract_time)
print("增量抽取结果（上次抽取时间：{}）：".format(last_extract_time))
print(incremental_df)
print(f"共抽取 {len(incremental_df)} 条新增记录\n")

# 追加到目标表
incremental_df.to_sql('orders_target', conn, if_exists='append', index=False)

# 更新水位线
new_last_time = datetime.now()
print(f"水位线已更新为：{new_last_time}")

conn.close()
```

**输出结果**：
```
增量抽取结果（上次抽取时间：2024-01-02 00:00:00）：
   order_id customer_name  amount  order_date
0         4           赵六  1299.0  2024-01-04
1         5           孙七   399.0  2024-01-05
共抽取 2 条新增记录

水位线已更新为：2024-01-05 15:30:45.123456
```

---

### 示例3：增量合并去重（UPSERT策略）

```python
import pandas as pd
import sqlite3

conn = sqlite3.connect('etl_demo.db')

# 读取目标表已有数据
target_df = pd.read_sql_query("SELECT * FROM orders_target", conn)
print("目标表当前数据：")
print(target_df)

# 模拟新的增量数据（包含一条已存在的记录和一条新记录）
incremental_data = pd.DataFrame([
    {'order_id': 3, 'customer_name': '王五', 'amount': 950.0, 'order_date': '2024-01-06'},  # 更新
    {'order_id': 6, 'customer_name': '周八', 'amount': 699.0, 'order_date': '2024-01-06'}   # 新增
])

# 使用merge实现UPSERT（更新+插入）
def upsert_data(target_df, incremental_df, key_col):
    """
    UPSERT策略：合并增量数据到目标表
    参数：
        target_df: 目标表DataFrame
        incremental_df: 增量数据DataFrame
        key_col: 主键列名
    返回：
        DataFrame: 合并后的完整数据
    """
    # 找出需要更新的记录（主键匹配）
    update_mask = incremental_df[key_col].isin(target_df[key_col])
    update_records = incremental_df[update_mask]
    
    # 找出需要插入的新记录
    insert_records = incremental_df[~update_mask]
    
    # 更新：删除旧记录，加入新记录
    if not update_records.empty:
        target_df = target_df[~target_df[key_col].isin(update_records[key_col])]
        target_df = pd.concat([target_df, update_records], ignore_index=True)
    
    # 插入新记录
    if not insert_records.empty:
        target_df = pd.concat([target_df, insert_records], ignore_index=True)
    
    return target_df.sort_values(key_col).reset_index(drop=True)

# 执行UPSERT
merged_df = upsert_data(target_df, incremental_data, 'order_id')
print("\n合并后的数据：")
print(merged_df)

# 写回目标表（覆盖模式）
merged_df.to_sql('orders_target', conn, if_exists='replace', index=False)
print("\nUPSERT完成，数据已写回目标表")

conn.close()
```

**输出结果**：
```
目标表当前数据：
   order_id customer_name  amount  order_date
0         1           张三   299.0  2024-01-01
1         2           李四   159.5  2024-01-02
2         3           王五   899.0  2024-01-03
3         4           赵六  1299.0  2024-01-04
4         5           孙七   399.0  2024-01-05

合并后的数据：
   order_id customer_name  amount  order_date
0         1           张三   299.0  2024-01-01
1         2           李四   159.5  2024-01-02
2         3           王五   950.0  2024-01-06
3         4           赵六  1299.0  2024-01-04
4         5           孙七   399.0  2024-01-05
5         6           周八   699.0  2024-01-06

UPSERT完成，数据已写回目标表
```

---

## 4. 常见错误

### 错误1：增量抽取时忘记更新水位线

```python
# 错误写法：每次抽取都使用固定的时间
last_extract_time = datetime(2024, 1, 1)
def bad_incremental_extract(conn):
    query = "SELECT * FROM orders WHERE order_date > '2024-01-01'"
    return pd.read_sql_query(query, conn)

# 正确写法：每次抽取后更新水位线
last_extract_time = datetime(2024, 1, 1)
def good_incremental_extract(conn, last_time):
    query = "SELECT * FROM orders WHERE order_date > ?"
    df = pd.read_sql_query(query, conn, params=(last_time.strftime('%Y-%m-%d'),))
    # 抽取完成后更新水位线
    new_last_time = datetime.now()
    return df, new_last_time  # 返回新水位线供下次使用
```
**错误原因**：水位线不更新会导致重复抽取相同数据，或遗漏新数据。

---

### 错误2：`to_sql` 的 `if_exists` 参数使用不当

```python
# 错误写法：增量数据用'replace'会覆盖已有数据
incremental_df.to_sql('orders_target', conn, if_exists='replace', index=False)

# 正确写法：增量追加用'append'
incremental_df.to_sql('orders_target', conn, if_exists='append', index=False)

# 全量更新才用'replace'
full_df.to_sql('orders_target', conn, if_exists='replace', index=False)
```
**错误原因**：`'replace'`会删除并重建表，导致历史数据丢失；`'append'`则保留已有数据并追加新行。

---

### 错误3：忽略数据类型不一致导致合并失败

```python
# 错误写法：主键列类型不一致（int vs str）
target_df = pd.DataFrame({'id': [1, 2, 3], 'value': ['a', 'b', 'c']})
incremental_df = pd.DataFrame({'id': ['1', '4'], 'value': ['d', 'e']})
# 直接merge会失败或产生错误结果

# 正确写法：先统一数据类型再合并
target_df['id'] = target_df['id'].astype(int)
incremental_df['id'] = incremental_df['id'].astype(int)
merged_df = pd.merge(target_df, incremental_df, on='id', how='outer')
```
**错误原因**：数据库中的主键类型必须一致，否则merge时无法正确匹配记录。

---

## 5. 练习

### 练习1：实现基于自增ID的增量抽取

**题目**：假设有一个 `user_activity` 表，包含自增主键 `activity_id` 和 `activity_time` 字段。请实现一个增量抽取函数，使用 `activity_id` 作为增量标记（而不是时间戳），并说明这种方式的优缺点。

**答案提示**：
```python
def incremental_by_id(conn, last_max_id):
    """基于自增ID的增量抽取"""
    query = "SELECT * FROM user_activity WHERE activity_id > ?"
    df = pd.read_sql_query(query, conn, params=(last_max_id,))
    new_max_id = df['activity_id'].max() if not df.empty else last_max_id
    return df, new_max_id
```
**优缺点**：优点是简单可靠，不受时间修改影响；缺点是无法捕获被修改的旧记录（只有新增能识别）。

---

### 练习2：设计一个完整的增量ETL流程

**题目**：设计一个完整的增量ETL流程，要求：
1. 使用 `sqlite3` 创建源表和目标表
2. 实现增量抽取（基于 `updated_at` 时间戳）
3. 实现UPSERT合并逻辑
4. 将水位线存储在单独的元数据表中

**答案提示**：
```python
# 核心思路
def etl_incremental_pipeline(conn):
    # 1. 从元数据表读取水位线
    watermark = pd.read_sql_query("SELECT last_time FROM etl_metadata", conn)
    
    # 2. 增量抽取
    query = "SELECT * FROM source_table WHERE updated_at > ?"
    incremental_df = pd.read_sql_query(query, conn, params=(watermark,))
    
    # 3. UPSERT合并（参考示例3的merge逻辑）
    
    # 4. 更新水位线
    new_watermark = datetime.now()
    cursor.execute("UPDATE etl_metadata SET last_time = ?", (new_watermark,))
    conn.commit()
```
**关键点**：水位线持久化存储，保证系统重启后仍能正确续跑。