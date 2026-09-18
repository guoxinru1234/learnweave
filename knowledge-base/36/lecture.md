# SQL查询语句精讲
> 模块：SQL与数据库 | 编号：第36讲 | Python数据分析实战

## 1. 概念

SQL（Structured Query Language，结构化查询语言）是用于管理和操作关系型数据库的标准语言。在 Python 数据分析中，SQL 主要用于从数据库中高效地提取、筛选、聚合和连接数据，是数据获取阶段的核心技能。其核心操作包括 SELECT（查询）、WHERE（过滤）、GROUP BY（分组）、ORDER BY（排序）和 JOIN（连接）等。

**生活化类比**：可以把 SQL 查询想象成在图书馆找书的过程。SELECT 是你想借的字段（比如书名、作者）；FROM 是你要去的书架（哪张表）；WHERE 是筛选条件（只要 2020 年后出版的书）；GROUP BY 是把书按出版社分类堆放；ORDER BY 是按价格从低到高排列；JOIN 则是把两本关联的书（比如书和作者信息）合并在一起看。

在 Python 中，通常通过 `sqlite3`（内置）或 `SQLAlchemy` 等库连接数据库，执行 SQL 语句并将结果转为 Pandas DataFrame 进行后续分析。

## 2. 核心API与原理

以下以 Python 内置的 `sqlite3` 模块为例（无需安装，Python 自带），核心 API 如下：

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `sqlite3.connect()` | `connect(database)` | `database`: 数据库文件路径（如 `':memory:'` 表示内存临时库） | 返回 `Connection` 连接对象 |
| `conn.execute()` | `execute(sql, parameters=None)` | `sql`: SQL 查询字符串；`parameters`: 可选参数元组，用于防注入 | 返回 `Cursor` 游标对象 |
| `cursor.fetchall()` | `fetchall()` | 无参数 | 返回列表，每个元素是查询结果的一行（元组） |
| `cursor.fetchone()` | `fetchone()` | 无参数 | 返回单行结果（元组），无结果时返回 `None` |
| `conn.commit()` | `commit()` | 无参数 | 无返回值，用于提交事务（增删改后必须调用） |
| `conn.close()` | `close()` | 无参数 | 无返回值，关闭数据库连接 |

**原理说明**：`sqlite3` 是 Python 标准库中对 SQLite 数据库的封装。SQLite 是一个轻量级文件型数据库，无需独立服务器进程。执行流程为：连接数据库 → 创建游标 → 执行 SQL → 获取结果 → 关闭连接。

## 3. 代码示例

### 示例 1：基础查询与筛选（SELECT + WHERE + ORDER BY）

```python
import sqlite3

# 1. 连接内存数据库
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# 2. 创建表并插入数据
cursor.execute('''
    CREATE TABLE employees (
        id INTEGER PRIMARY KEY,
        name TEXT,
        department TEXT,
        salary REAL
    )
''')

employees_data = [
    ('张三', '技术部', 15000),
    ('李四', '市场部', 12000),
    ('王五', '技术部', 18000),
    ('赵六', '人事部', 9000),
]
cursor.executemany('INSERT INTO employees (name, department, salary) VALUES (?, ?, ?)', employees_data)
conn.commit()

# 3. 查询：筛选技术部且薪资大于10000的员工，按薪资降序排列
cursor.execute('''
    SELECT name, salary 
    FROM employees 
    WHERE department = '技术部' AND salary > 10000
    ORDER BY salary DESC
''')
results = cursor.fetchall()
print("技术部高薪员工：", results)
# 输出：技术部高薪员工： [('王五', 18000.0), ('张三', 15000.0)]

conn.close()
```

### 示例 2：聚合查询与分组（GROUP BY + 聚合函数）

```python
import sqlite3

conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# 创建销售数据表
cursor.execute('CREATE TABLE sales (product TEXT, region TEXT, amount REAL)')
sales_data = [
    ('手机', '华东', 5000), ('手机', '华北', 4500),
    ('电脑', '华东', 8000), ('电脑', '华北', 7200),
    ('手机', '华南', 5200), ('电脑', '华南', 7600),
]
cursor.executemany('INSERT INTO sales VALUES (?, ?, ?)', sales_data)
conn.commit()

# 查询：按产品分组，统计每个产品的总销售额和平均销售额
cursor.execute('''
    SELECT product, 
           SUM(amount) AS total_sales, 
           AVG(amount) AS avg_sales
    FROM sales
    GROUP BY product
''')
for row in cursor.fetchall():
    print(f"产品: {row[0]}, 总销售额: {row[1]}, 平均销售额: {row[2]:.2f}")

# 输出：
# 产品: 手机, 总销售额: 14700.0, 平均销售额: 4900.00
# 产品: 电脑, 总销售额: 22800.0, 平均销售额: 7600.00

conn.close()
```

### 示例 3：表连接查询（JOIN）

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# 创建两张表：订单表和客户表
cursor.execute('CREATE TABLE orders (order_id INTEGER, customer_id INTEGER, amount REAL)')
cursor.execute('CREATE TABLE customers (customer_id INTEGER, name TEXT, city TEXT)')

orders_data = [(1, 101, 300), (2, 102, 500), (3, 101, 200)]
customers_data = [(101, '张三', '上海'), (102, '李四', '北京')]

cursor.executemany('INSERT INTO orders VALUES (?, ?, ?)', orders_data)
cursor.executemany('INSERT INTO customers VALUES (?, ?, ?)', customers_data)
conn.commit()

# 内连接：查询每个订单对应的客户姓名和城市
query = '''
    SELECT o.order_id, c.name, c.city, o.amount
    FROM orders o
    INNER JOIN customers c ON o.customer_id = c.customer_id
    ORDER BY o.amount DESC
'''
df = pd.read_sql_query(query, conn)
print(df)
# 输出：
#    order_id name  city  amount
# 0         2   李四   北京   500.0
# 1         1   张三   上海   300.0
# 2         3   张三   上海   200.0

conn.close()
```

## 4. 常见错误

### 错误 1：忘记提交事务（增删改后未调用 `commit()`）

```python
# 错误写法
conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute("INSERT INTO users (name) VALUES ('小明')")
# 忘记 conn.commit()，数据不会真正写入数据库

# 正确写法
conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute("INSERT INTO users (name) VALUES ('小明')")
conn.commit()  # 必须提交事务
conn.close()
```

### 错误 2：SQL 字符串拼接导致语法错误或注入风险

```python
# 错误写法：直接拼接用户输入
user_input = "张三' OR '1'='1"
cursor.execute(f"SELECT * FROM users WHERE name = '{user_input}'")  # 语法错误且不安全

# 正确写法：使用参数化查询
user_input = "张三' OR '1'='1"
cursor.execute("SELECT * FROM users WHERE name = ?", (user_input,))  # 安全，返回空结果
```

### 错误 3：混淆 `fetchall()` 与 `fetchone()` 的使用场景

```python
# 错误写法：只取一条却用 fetchall，导致索引越界
cursor.execute("SELECT name FROM employees")
row = cursor.fetchall()[0][0]  # 如果表为空会报 IndexError

# 正确写法：明确需求
cursor.execute("SELECT name FROM employees")
row = cursor.fetchone()  # 取第一条，无数据时返回 None
if row:
    print(row[0])
```

## 5. 练习

### 练习 1：分组统计与条件筛选

**题目**：使用 `sqlite3` 创建一张 `student_scores` 表（字段：`student_id`, `subject`, `score`），插入至少 6 条数据（涉及 3 个学生、3 门科目）。编写 SQL 查询：找出每个学生的平均分，并只显示平均分大于 80 的学生，按平均分降序排列。

**答案提示**：
```sql
SELECT student_id, AVG(score) AS avg_score
FROM student_scores
GROUP BY student_id
HAVING AVG(score) > 80
ORDER BY avg_score DESC;
```
注意：`WHERE` 不能与聚合函数连用，必须使用 `HAVING` 来过滤分组后的结果。

### 练习 2：多表连接与聚合

**题目**：有两张表：`products`（`product_id`, `product_name`, `category`）和 `order_items`（`order_id`, `product_id`, `quantity`, `price`）。请编写 SQL 查询：统计每个产品类别的总销售额（`quantity * price` 之和），并按总销售额降序排列。

**答案提示**：
```sql
SELECT p.category, SUM(oi.quantity * oi.price) AS total_revenue
FROM products p
INNER JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;
```
关键点：先 `JOIN` 关联两张表，再 `GROUP BY` 分类，最后用 `ORDER BY` 排序。