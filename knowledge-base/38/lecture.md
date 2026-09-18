# 索引优化与执行计划
> 模块：SQL与数据库 | 编号：第38讲 | Python数据分析实战

## 1. 概念

索引（Index）是数据库中一种独立于表结构的物理存储结构，其核心作用是通过维护排序后的键值（Key）与行指针（Row Pointer）的映射关系，将数据查询的时间复杂度从全表扫描的 O(n) 降低到 B+ 树查找的 O(log n)。执行计划（Execution Plan）则是数据库查询优化器（Query Optimizer）根据表统计信息（如行数、列基数、索引选择性）生成的"查询路线图"，它详细说明了数据访问方式（全表扫描/索引扫描/索引查找）、连接顺序、连接算法（嵌套循环/哈希连接/归并连接）以及过滤条件下推等关键决策。

**生活化类比**：想象一本没有目录的字典（全表扫描），你要找"Python"这个词必须从第一页翻到最后一页；而有了按字母排序的目录（索引），你可以直接翻到 P 开头的那几页，快速定位。执行计划就像是导航软件根据实时路况（统计信息）为你规划的最优路线——它可能选择走高速（索引查找），也可能因为高速堵车（索引选择性差）而选择走辅路（全表扫描）。

**适用场景**：当数据量超过万级且查询频繁涉及 WHERE、JOIN、ORDER BY 条件时，合理设计索引并分析执行计划是性能优化的核心手段。

## 2. 核心API与原理

以下 API 均来自 Python 标准库 `sqlite3`（Python 内置的 SQLite 数据库驱动），SQLite 是数据分析中最常用的嵌入式数据库。

| API/方法 | 签名 | 参数说明 | 返回值 | 原理说明 |
|---------|------|---------|--------|---------|
| `sqlite3.connect()` | `connect(database, timeout=5.0)` | `database`: 数据库文件路径或 `":memory:"` 表示内存库；`timeout`: 连接超时秒数 | `Connection` 对象 | 建立与数据库文件的连接，SQLite 以文件形式存储整个数据库 |
| `Connection.execute()` | `execute(sql, parameters=None)` | `sql`: SQL 语句字符串；`parameters`: 可选的参数序列或字典 | `Cursor` 对象 | 编译并执行单条 SQL 语句，返回游标用于获取结果集 |
| `Cursor.fetchall()` | `fetchall()` | 无 | `list[tuple]` | 获取查询结果的所有剩余行，每行是一个元组 |
| `Cursor.description` | 属性 | 无 | `list[tuple]` | 返回结果集的列元信息（列名、类型等），用于动态获取列名 |
| `Connection.executescript()` | `executescript(sql_script)` | `sql_script`: 包含多条 SQL 语句的字符串，以分号分隔 | `Cursor` 对象 | 批量执行 SQL 脚本，常用于创建表、插入初始数据 |

**执行计划查看方式**：在 SQLite 中，使用 `EXPLAIN QUERY PLAN` 前缀的 SQL 语句来获取执行计划，而非独立的 API 方法。例如：`cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM users WHERE age > 30")`。

## 3. 代码示例

### 示例 1：创建索引前后查询性能对比

```python
import sqlite3
import time
import random

# 创建内存数据库
conn = sqlite3.connect(":memory:")
cursor = conn.cursor()

# 创建测试表并插入 10 万条数据
cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
data = [(i, f"user_{i}", random.randint(18, 80)) for i in range(100000)]
cursor.executemany("INSERT INTO users (id, name, age) VALUES (?, ?, ?)", data)
conn.commit()

# 不带索引的查询
start = time.time()
cursor.execute("SELECT * FROM users WHERE age = 42")
result_no_index = cursor.fetchall()
time_no_index = time.time() - start
print(f"无索引查询耗时: {time_no_index:.4f} 秒, 返回 {len(result_no_index)} 行")
# 输出示例: 无索引查询耗时: 0.0523 秒, 返回 1587 行

# 创建索引
cursor.execute("CREATE INDEX idx_users_age ON users(age)")
conn.commit()

# 带索引的查询
start = time.time()
cursor.execute("SELECT * FROM users WHERE age = 42")
result_with_index = cursor.fetchall()
time_with_index = time.time() - start
print(f"有索引查询耗时: {time_with_index:.4f} 秒, 返回 {len(result_with_index)} 行")
# 输出示例: 有索引查询耗时: 0.0018 秒, 返回 1587 行

# 验证结果一致性
assert result_no_index == result_with_index, "两次查询结果不一致！"
print(f"性能提升: {time_no_index / time_with_index:.1f} 倍")
# 输出示例: 性能提升: 29.1 倍
```

### 示例 2：使用 EXPLAIN QUERY PLAN 分析执行计划

```python
import sqlite3

conn = sqlite3.connect(":memory:")
cursor = conn.cursor()

# 创建两张表并插入数据
cursor.executescript("""
    CREATE TABLE departments (dept_id INTEGER PRIMARY KEY, dept_name TEXT);
    CREATE TABLE employees (emp_id INTEGER PRIMARY KEY, emp_name TEXT, dept_id INTEGER, salary REAL);
    INSERT INTO departments VALUES (1, '研发部'), (2, '市场部'), (3, '销售部');
    INSERT INTO employees VALUES 
        (101, '张三', 1, 15000), (102, '李四', 1, 18000),
        (103, '王五', 2, 12000), (104, '赵六', 3, 9000);
""")
conn.commit()

# 查看无索引时的执行计划
cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM employees WHERE dept_id = 1")
print("无索引执行计划:")
for row in cursor.fetchall():
    print(f"  {row}")
# 输出:
#   无索引执行计划:
#   (0, 0, 0, 'SCAN employees')  -- 全表扫描

# 创建索引后再次查看
cursor.execute("CREATE INDEX idx_emp_dept ON employees(dept_id)")
cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM employees WHERE dept_id = 1")
print("\n有索引执行计划:")
for row in cursor.fetchall():
    print(f"  {row}")
# 输出:
#   有索引执行计划:
#   (0, 0, 0, 'SEARCH employees USING INDEX idx_emp_dept (dept_id=?)')  -- 索引查找

# 查看 JOIN 查询的执行计划
cursor.execute("""
    EXPLAIN QUERY PLAN 
    SELECT e.emp_name, d.dept_name 
    FROM employees e JOIN departments d ON e.dept_id = d.dept_id
""")
print("\nJOIN 查询执行计划:")
for row in cursor.fetchall():
    print(f"  {row}")
# 输出:
#   JOIN 查询执行计划:
#   (0, 0, 0, 'SCAN e')  -- 先扫描 employees
#   (0, 1, 1, 'SEARCH d USING INTEGER PRIMARY KEY (rowid=?)')  -- 用主键查找 departments
```

### 示例 3：复合索引与最左前缀原则

```python
import sqlite3
import time

conn = sqlite3.connect(":memory:")
cursor = conn.cursor()

# 创建订单表
cursor.execute("""
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        order_date TEXT,
        amount REAL
    )
""")

# 插入模拟数据（10000 条）
import random
from datetime import date, timedelta

base_date = date(2024, 1, 1)
data = []
for i in range(10000):
    cust_id = random.randint(1, 500)
    days_offset = random.randint(0, 365)
    order_date = (base_date + timedelta(days=days_offset)).isoformat()
    amount = round(random.uniform(50, 5000), 2)
    data.append((i, cust_id, order_date, amount))

cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", data)
conn.commit()

# 创建复合索引（customer_id, order_date）
cursor.execute("CREATE INDEX idx_cust_date ON orders(customer_id, order_date)")

# 场景 1：按 customer_id 查询（符合最左前缀）
start = time.time()
cursor.execute("SELECT * FROM orders WHERE customer_id = 100")
result1 = cursor.fetchall()
print(f"按 customer_id 查询: {len(result1)} 行, 耗时 {time.time()-start:.4f} 秒")
# 输出示例: 按 customer_id 查询: 18 行, 耗时 0.0009 秒

# 场景 2：按 customer_id + order_date 查询（完全匹配复合索引）
start = time.time()
cursor.execute("SELECT * FROM orders WHERE customer_id = 100 AND order_date > '2024-06-01'")
result2 = cursor.fetchall()
print(f"按 customer_id + order_date 查询: {len(result2)} 行, 耗时 {time.time()-start:.4f} 秒")
# 输出示例: 按 customer_id + order_date 查询: 9 行, 耗时 0.0007 秒

# 场景 3：仅按 order_date 查询（无法使用复合索引，触发全表扫描）
cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM orders WHERE order_date = '2024-06-15'")
plan = cursor.fetchall()
print(f"仅按 order_date 查询的执行计划: {plan[0][3]}")
# 输出示例: 仅按 order_date 查询的执行计划: SCAN orders
```

## 4. 常见错误

### 错误 1：索引过多导致写入性能下降

**错误原因**：新手往往认为索引越多越好，但每个索引都会增加 INSERT、UPDATE、DELETE 操作的开销，因为每次数据变更都需要同步维护所有相关索引。在频繁写入的表上创建大量索引，会导致写入性能急剧下降。

```python
# 错误写法：在频繁写入的表上创建 5 个索引
cursor.execute("CREATE INDEX idx_1 ON logs(level)")
cursor.execute("CREATE INDEX idx_2 ON logs(timestamp)")
cursor.execute("CREATE INDEX idx_3 ON logs(user_id)")
cursor.execute("CREATE INDEX idx_4 ON logs(ip_address)")
cursor.execute("CREATE INDEX idx_5 ON logs(status)")

# 正确写法：只对高频查询字段创建索引，合并相关字段为复合索引
cursor.execute("CREATE INDEX idx_logs_user_time ON logs(user_id, timestamp)")
```

### 错误 2：对索引列使用函数或计算导致索引失效

**错误原因**：当 WHERE 条件中对索引列应用函数（如 `UPPER()`）、算术运算或类型转换时，查询优化器无法直接使用索引进行范围查找，只能退化为全表扫描。

```python
# 错误写法：对索引列使用函数
cursor.execute("SELECT * FROM users WHERE UPPER(name) = 'ALICE'")

# 正确写法：预先存储规范化数据（如全大写），直接等值查询
cursor.execute("SELECT * FROM users WHERE name = 'ALICE'")

# 错误写法：对索引列进行算术运算
cursor.execute("SELECT * FROM orders WHERE amount * 1.1 > 1000")

# 正确写法：将运算移到常量一侧
cursor.execute("SELECT * FROM orders WHERE amount > 1000 / 1.1")
```

### 错误 3：忽视最左前缀原则

**错误原因**：复合索引 `(col1, col2, col3)` 只能用于查询条件中包含 `col1` 或以 `col1` 开头的列组合。如果查询条件只包含 `col2` 或 `col3`，索引将无法使用。

```python
# 创建复合索引
cursor.execute("CREATE INDEX idx_composite ON employees(dept_id, age, salary)")

# 错误写法：查询条件不包含最左列 dept_id
cursor.execute("SELECT * FROM employees WHERE age > 30 AND salary > 5000")
# 执行计划: SCAN employees（全表扫描）

# 正确写法：查询条件包含最左列 dept_id
cursor.execute("SELECT * FROM employees WHERE dept_id = 1 AND age > 30")
# 执行计划: SEARCH employees USING INDEX idx_composite (dept_id=? AND age>?)
```

## 5. 练习

### 练习 1：索引选择性分析

**题目**：创建一个包含 50000 条记录的用户表，包含 `gender`（性别，只有 'M'/'F' 两个值）和 `email`（邮箱，每个用户唯一）两个字段。分别在这两个字段上创建索引，使用 `EXPLAIN QUERY PLAN` 对比以下两个查询的执行计划：
- `SELECT * FROM users WHERE gender = 'M'`
- `SELECT * FROM users WHERE email = 'user123@example.com'`

**答案提示**：`gender` 字段的基数（Cardinality）极低（只有 2 个不同值），索引选择性差，优化器大概率选择全表扫描；`email` 字段基数极高（接近行数），索引选择性好，优化器会选择索引查找。可通过 `EXPLAIN QUERY PLAN` 验证，并思考：为什么低选择性索引有时反而不如全表扫描？

### 练习 2：复合索引设计优化

**题目**：某电商订单表 `orders` 包含字段 `customer_id`、`order_date`、`status`（'pending'/'paid'/'shipped'/'cancelled'），业务上有以下高频查询：
1. 查询某客户某天的订单：`WHERE customer_id = ? AND order_date = ?`
2. 查询某状态下某天的订单：`WHERE status = ? AND order_date = ?`

请设计最优的索引方案，并用 `EXPLAIN QUERY PLAN` 验证两个查询都能使用索引。提示：考虑是否需要创建两个复合索引，以及每个索引的列顺序。

**答案提示**：设计两个复合索引：`idx_customer_date (customer_id, order_date)` 和 `idx_status_date (status, order_date)`。验证时注意观察执行计划中是否出现 `SEARCH ... USING INDEX` 字样。思考：如果业务新增查询 3（仅按 `order_date` 查询），现有索引是否仍然有效？