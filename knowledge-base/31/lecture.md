# ETL概念与架构模式
> 模块：ETL数据管道 | 编号：第31讲 | Python数据分析实战

---

## 1. 概念

**ETL** 是 **Extract（抽取）、Transform（转换）、Load（加载）** 三个英文单词的首字母缩写，指将数据从源系统（Source）经过抽取、清洗、转换后，加载到目标系统（如数据仓库、数据湖）的完整流程。

- **Extract（抽取）**：从各类异构数据源（关系型数据库、API接口、日志文件、Excel等）读取原始数据。
- **Transform（转换）**：对数据进行清洗（去重、缺失值处理）、标准化（统一格式、单位换算）、聚合（汇总统计）、关联（多表合并）等操作，使其满足目标系统的存储和分析要求。
- **Load（加载）**：将处理后的数据写入目标存储（如 PostgreSQL、MySQL、Hive、Parquet 文件等），支持全量加载或增量加载。

**适用场景**：数据仓库建设、BI报表数据准备、数据迁移、实时/离线数据同步等。

**生活化类比**：ETL 就像**开一家奶茶店**——"抽取"是去农场采购新鲜水果（从不同供应商拿原料），"转换"是清洗水果、去皮去核、按配方调配成奶茶（加工处理），"加载"是把做好的奶茶整齐摆放到展示柜里（存入仓库供顾客取用）。没有 ETL，数据就像散落在地上的水果，无法直接"饮用"。

---

## 2. 核心API与原理

ETL 本身不是某个库的单一 API，而是由 Pandas 和 SQLAlchemy 等库协同实现的**架构模式**。以下是最核心的 4 个 API：

| API/方法 | 签名 | 参数说明 | 返回值 | 用途 |
|---------|------|---------|--------|------|
| `pandas.read_csv()` | `read_csv(filepath_or_buffer, sep=',', encoding=None, ...)` | `filepath_or_buffer`：文件路径或URL；`sep`：分隔符；`encoding`：文件编码 | `DataFrame` | **抽取**：从 CSV 文件读取数据 |
| `pandas.DataFrame.merge()` | `df.merge(right, how='inner', on=None, left_on=None, right_on=None)` | `right`：要合并的另一个 DataFrame；`how`：连接方式（'left'/'right'/'inner'/'outer'）；`on`：连接键列名 | `DataFrame` | **转换**：按键合并多个数据表 |
| `pandas.DataFrame.drop_duplicates()` | `df.drop_duplicates(subset=None, keep='first', inplace=False)` | `subset`：去重依据的列（默认全部列）；`keep`：保留哪个重复项（'first'/'last'/False）；`inplace`：是否原地修改 | `DataFrame` 或 `None` | **转换**：去除重复行 |
| `pandas.DataFrame.to_sql()` | `df.to_sql(name, con, if_exists='fail', index=True, ...)` | `name`：目标表名；`con`：SQLAlchemy 连接对象；`if_exists`：'fail'/'replace'/'append'；`index`：是否写入索引 | `int`（写入行数） | **加载**：将 DataFrame 写入数据库表 |

> **架构模式说明**：ETL 通常采用**管道模式（Pipeline Pattern）**，即每个阶段（E/T/L）是独立的函数或类，通过主流程串联。Pandas 提供 `pd.read_*` 系列（read_csv/read_excel/read_sql）完成抽取，`df.transform()`/`df.merge()`/`df.groupby()` 等完成转换，`df.to_csv()`/`df.to_sql()`/`df.to_parquet()` 完成加载。

---

## 3. 代码示例

### 示例 1：基础 ETL——CSV 抽取 → 清洗转换 → 加载为新 CSV

```python
import pandas as pd

# ========== 1. EXTRACT（抽取） ==========
# 从原始 CSV 文件读取销售数据
df_raw = pd.read_csv('sales_raw.csv', encoding='utf-8')
print("抽取完成，原始数据形状:", df_raw.shape)

# ========== 2. TRANSFORM（转换） ==========
# 2.1 去除重复订单
df_clean = df_raw.drop_duplicates(subset=['order_id'], keep='first')

# 2.2 处理缺失值：金额缺失填充 0，日期缺失删除该行
df_clean['amount'] = df_clean['amount'].fillna(0)
df_clean = df_clean.dropna(subset=['order_date'])

# 2.3 标准化日期格式（统一为 YYYY-MM-DD）
df_clean['order_date'] = pd.to_datetime(df_clean['order_date']).dt.strftime('%Y-%m-%d')

# 2.4 新增列：计算含税金额（税率 13%）
df_clean['amount_tax'] = df_clean['amount'] * 1.13

print("转换完成，清洗后数据形状:", df_clean.shape)

# ========== 3. LOAD（加载） ==========
# 将处理结果写入新文件
df_clean.to_csv('sales_clean.csv', index=False, encoding='utf-8-sig')
print("加载完成，已写入 sales_clean.csv")

# 输出示例
# 抽取完成，原始数据形状: (1000, 6)
# 转换完成，清洗后数据形状: (985, 7)
# 加载完成，已写入 sales_clean.csv
```

### 示例 2：进阶 ETL——多表合并 + 聚合转换 + 写入 SQLite

```python
import pandas as pd
from sqlalchemy import create_engine

# ========== 1. EXTRACT（抽取） ==========
# 从两个数据源抽取：订单表和用户表
df_orders = pd.read_csv('orders.csv')
df_users = pd.read_csv('users.csv')
print("抽取完成：订单 {} 行，用户 {} 行".format(len(df_orders), len(df_users)))

# ========== 2. TRANSFORM（转换） ==========
# 2.1 合并订单与用户信息（左连接，保留所有订单）
df_merged = df_orders.merge(df_users, on='user_id', how='left')

# 2.2 按用户分组聚合：计算每个用户的订单总金额
df_user_stats = df_merged.groupby('user_name', as_index=False).agg(
    total_amount=('amount', 'sum'),
    order_count=('order_id', 'count')
)

# 2.3 筛选高价值用户（消费总额 > 1000）
df_vip = df_user_stats[df_user_stats['total_amount'] > 1000].copy()
df_vip['avg_order_value'] = df_vip['total_amount'] / df_vip['order_count']

print("转换完成，VIP 用户数:", len(df_vip))

# ========== 3. LOAD（加载） ==========
# 创建 SQLite 数据库连接（内存中演示）
engine = create_engine('sqlite:///etl_demo.db')

# 写入数据库表（若表已存在则追加）
df_vip.to_sql('vip_users', con=engine, if_exists='replace', index=False)
print("加载完成，已写入 SQLite 的 vip_users 表")

# 验证加载结果
df_check = pd.read_sql("SELECT * FROM vip_users LIMIT 3", con=engine)
print(df_check)

# 输出示例
# 抽取完成：订单 500 行，用户 200 行
# 转换完成，VIP 用户数: 18
# 加载完成，已写入 SQLite 的 vip_users 表
#    user_name  total_amount  order_count  avg_order_value
# 0   张三      3560.5        12           296.71
# 1   李四      2843.0         8           355.38
# 2   王五      2100.0         5           420.00
```

### 示例 3：完整 ETL 管道函数（架构模式封装）

```python
import pandas as pd
from sqlalchemy import create_engine

def extract_data(file_path: str) -> pd.DataFrame:
    """抽取阶段：从 CSV 读取数据"""
    return pd.read_csv(file_path, encoding='utf-8')

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """转换阶段：清洗、标准化、聚合"""
    # 去重
    df = df.drop_duplicates(subset=['id'], keep='first')
    # 类型转换
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    # 缺失值处理
    df['price'] = df['price'].fillna(df['price'].median())
    # 新增派生列
    df['total'] = df['price'] * df['quantity']
    return df

def load_data(df: pd.DataFrame, db_url: str, table_name: str) -> int:
    """加载阶段：写入数据库"""
    engine = create_engine(db_url)
    rows = df.to_sql(table_name, con=engine, if_exists='append', index=False)
    return rows

# ========== 主流程：串联 ETL 三阶段 ==========
if __name__ == "__main__":
    # 1. 抽取
    raw_df = extract_data('products.csv')
    print(f"[ETL] 抽取阶段完成，共 {len(raw_df)} 行")

    # 2. 转换
    clean_df = transform_data(raw_df)
    print(f"[ETL] 转换阶段完成，剩余 {len(clean_df)} 行")

    # 3. 加载
    affected = load_data(clean_df, 'sqlite:///warehouse.db', 'dim_product')
    print(f"[ETL] 加载阶段完成，写入 {affected} 行")

# 输出示例
# [ETL] 抽取阶段完成，共 1200 行
# [ETL] 转换阶段完成，剩余 1180 行
# [ETL] 加载阶段完成，写入 1180 行
```

---

## 4. 常见错误

### 错误 1：`to_sql` 写入时未安装/未创建 SQLAlchemy 引擎

```python
# ❌ 错误写法：直接用 pandas 连接字符串
df.to_sql('my_table', con='sqlite:///db.sqlite')

# ✅ 正确写法：必须使用 SQLAlchemy 的 create_engine 创建连接对象
from sqlalchemy import create_engine
engine = create_engine('sqlite:///db.sqlite')
df.to_sql('my_table', con=engine, if_exists='replace', index=False)
```
**原因**：`to_sql` 的 `con` 参数要求是 SQLAlchemy 连接对象或 DBAPI 连接，不能直接传连接字符串。

### 错误 2：读取 CSV 时忽略编码导致乱码

```python
# ❌ 错误写法：不指定编码，遇到 GBK 编码文件直接报错或乱码
df = pd.read_csv('中文数据.csv')

# ✅ 正确写法：根据文件实际编码指定 encoding 参数
df = pd.read_csv('中文数据.csv', encoding='utf-8')
# 若仍乱码，尝试 gbk 或 gb18030
df = pd.read_csv('中文数据.csv', encoding='gbk')
```
**原因**：Pandas 默认使用 `utf-8` 解析文件，而 Windows 下常见的中文 CSV 文件多为 `gbk/gb18030` 编码。

### 错误 3：`merge` 时连接键类型不一致导致匹配失败

```python
# ❌ 错误写法：两个表连接键一个为 int，一个为 str
df_orders['user_id'] = df_orders['user_id'].astype(int)
df_users['user_id'] = df_users['user_id'].astype(str)
merged = df_orders.merge(df_users, on='user_id', how='left')  # 结果全是 NaN

# ✅ 正确写法：统一连接键的数据类型
df_orders['user_id'] = df_orders['user_id'].astype(str)
df_users['user_id'] = df_users['user_id'].astype(str)
merged = df_orders.merge(df_users, on='user_id', how='left')
```
**原因**：Pandas 的 `merge` 对连接键做严格匹配，`1`（int）和 `'1'`（str）被视为不同值，导致合并结果大量缺失。

---

## 5. 练习

### 练习 1：实现一个"增量加载"ETL 流程

**题目**：假设你有一个每日更新的订单文件 `orders_20250101.csv`、`orders_20250102.csv`……请编写一个 ETL 函数，实现：
1. 抽取指定日期的订单文件；
2. 转换：过滤掉金额为负的异常订单，并将日期列转为标准格式；
3. 加载：将数据追加写入 SQLite 数据库的 `orders` 表（使用 `if_exists='append'`），并打印每次加载的行数。

**答案提示**：
```python
def daily_etl(date_str: str):
    df = pd.read_csv(f'orders_{date_str}.csv')
    df = df[df['amount'] >= 0]
    df['order_date'] = pd.to_datetime(df['order_date']).dt.date
    engine = create_engine('sqlite:///orders.db')
    rows = df.to_sql('orders', con=engine, if_exists='append', index=False)
    print(f"{date_str}: 加载 {rows} 行")
```

### 练习 2：多源数据整合与质量校验

**题目**：你有两个数据源——`customers.xlsx`（Excel 格式）和 `transactions.csv`（CSV 格式）。请完成：
1. 抽取两个文件的数据；
2. 转换：将两个表按 `customer_id` 合并，检查并报告合并后 `customer_id` 为空的记录数（即孤儿交易）；
3. 加载：将合并结果写入 Parquet 文件（使用 `df.to_parquet()`），并统计最终数据量。

**答案提示**：
```python
df_cust = pd.read_excel('customers.xlsx')
df_txn = pd.read_csv('transactions.csv')
df_merged = df_txn.merge(df_cust, on='customer_id', how='left')
orphan_count = df_merged['customer_name'].isna().sum()
print(f"孤儿交易数: {orphan_count}")
df_merged.to_parquet('merged_data.parquet', index=False)
print(f"最终数据量: {len(df_merged)} 行")
```