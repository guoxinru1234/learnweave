# Python操作MySQL/SQLite

> 模块：SQL与数据库 | 编号：第39讲 | Python数据分析实战

---

## 1. 概念

在数据分析工作中，数据往往存储在关系型数据库中（如 MySQL、SQLite）。Python 需要通过数据库驱动（DB-API）与数据库建立连接，执行 SQL 语句，并将查询结果转换为 Pandas DataFrame 进行后续分析。

**核心概念**：
- **连接（Connection）**：Python 程序与数据库之间的通信通道，需指定主机、端口、用户名、密码等参数。
- **游标（Cursor）**：用于执行 SQL 语句并获取结果的对象，通过 `connection.cursor()` 创建。
- **事务（Transaction）**：一组 SQL 操作的逻辑单元，需 `commit()` 提交或 `rollback()` 回滚。
- **SQLite 与 MySQL 的区别**：SQLite 是嵌入式文件数据库（无需服务器），MySQL 是客户端/服务器架构的数据库。

**生活化类比**：可以把数据库看作一个大型图书馆。连接（Connection）就是你办理的借书证（进入图书馆的凭证）；游标（Cursor）是你手中的借书篮（用来装你挑选的书）；执行 SQL 语句就像向图书管理员提出查询请求；`commit()` 相当于确认借书手续完成，`rollback()` 则是取消本次借书操作。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 | 说明 |
|-----|------|----------|--------|------|
| `sqlite3.connect()` | `sqlite3.connect(database)` | `database`: 数据库文件路径（如 `'mydb.db'`），或 `':memory:'` 表示内存数据库 | `Connection` 对象 | 建立 SQLite 连接 |
| `MySQLdb.connect()` / `pymysql.connect()` | `pymysql.connect(host, user, password, database, port)` | `host`: 主机地址；`user`: 用户名；`password`: 密码；`database`: 数据库名；`port`: 端口（默认3306） | `Connection` 对象 | 建立 MySQL 连接 |
| `connection.cursor()` | `cursor()` | 无 | `Cursor` 对象 | 创建游标，用于执行 SQL |
| `cursor.execute()` | `execute(sql, parameters=None)` | `sql`: SQL语句字符串；`parameters`: 可选参数元组/列表，用于参数化查询 | 受影响行数（int） | 执行单条 SQL 语句 |
| `cursor.fetchall()` | `fetchall()` | 无 | 元组列表（每行是一个元组） | 获取查询结果的所有行 |
| `cursor.fetchone()` | `fetchone()` | 无 | 单行元组或 `None` | 获取查询结果的一行 |
| `connection.commit()` | `commit()` | 无 | 无 | 提交事务，使更改生效 |
| `connection.close()` | `close()` | 无 | 无 | 关闭数据库连接 |

> **注意**：Python 标准库自带 `sqlite3`，无需安装。MySQL 需要安装驱动，常用的是 `pymysql`（`pip install pymysql`）或 `mysql-connector-python`。

---

## 3. 代码示例

### 示例1：SQLite 基础操作（创建表、插入、查询）

```python
import sqlite3

# 1. 连接数据库（若文件不存在会自动创建）
conn = sqlite3.connect('example.db')
cursor = conn.cursor()

# 2. 创建表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        score REAL
    )
''')

# 3. 插入数据（使用参数化查询，防止SQL注入）
cursor.execute('INSERT INTO students (name, score) VALUES (?, ?)', ('Alice', 92.5))
cursor.execute('INSERT INTO students (name, score) VALUES (?, ?)', ('Bob', 85.0))
cursor.execute('INSERT INTO students (name, score) VALUES (?, ?)', ('Charlie', 78.5))

# 4. 提交事务
conn.commit()

# 5. 查询数据
cursor.execute('SELECT * FROM students')
rows = cursor.fetchall()
for row in rows:
    print(row)

# 6. 关闭连接
cursor.close()
conn.close()

# 输出：
# (1, 'Alice', 92.5)
# (2, 'Bob', 85.0)
# (3, 'Charlie', 78.5)
```

### 示例2：SQLite 与 Pandas 结合（数据分析场景）

```python
import sqlite3
import pandas as pd

# 连接数据库
conn = sqlite3.connect('example.db')

# 使用 pandas.read_sql_query 直接读取查询结果为 DataFrame
df = pd.read_sql_query('SELECT * FROM students WHERE score >= 80', conn)
print("查询结果：")
print(df)

# 将 DataFrame 写入数据库（追加模式）
new_data = pd.DataFrame({'name': ['David', 'Eva'], 'score': [88.0, 95.5]})
new_data.to_sql('students', conn, if_exists='append', index=False)

# 验证写入结果
df_all = pd.read_sql_query('SELECT * FROM students', conn)
print("\n全部学生：")
print(df_all)

conn.close()

# 输出：
# 查询结果：
#    id   name  score
# 0   1  Alice   92.5
# 1   2    Bob   85.0
#
# 全部学生：
#    id    name  score
# 0   1   Alice   92.5
# 1   2     Bob   85.0
# 2   3 Charlie   78.5
# 3   4   David   88.0
# 4   5     Eva   95.5
```

### 示例3：MySQL 操作（使用 pymysql）

```python
import pymysql

# 连接 MySQL 数据库（请根据实际环境修改参数）
conn = pymysql.connect(
    host='localhost',      # 数据库主机地址
    user='root',           # 用户名
    password='123456',     # 密码
    database='test_db',    # 数据库名
    charset='utf8mb4'      # 字符集
)

try:
    with conn.cursor() as cursor:
        # 创建表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                price DECIMAL(10, 2)
            )
        ''')

        # 插入数据
        cursor.execute('INSERT INTO products (name, price) VALUES (%s, %s)', ('Laptop', 5999.00))
        cursor.execute('INSERT INTO products (name, price) VALUES (%s, %s)', ('Mouse', 99.50))

    # 提交事务
    conn.commit()

    # 查询数据
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM products')
        rows = cursor.fetchall()
        for row in rows:
            print(row)

finally:
    conn.close()

# 输出（示例）：
# (1, 'Laptop', Decimal('5999.00'))
# (2, 'Mouse', Decimal('99.50'))
```

---

## 4. 常见错误

### 错误1：忘记调用 `commit()` 导致数据未保存

**错误原因**：SQLite/MySQL 默认开启事务，执行 `INSERT`、`UPDATE`、`DELETE` 后若不调用 `commit()`，关闭连接时更改会回滚。

```python
# 错误写法
import sqlite3
conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE t (id INTEGER)')
cursor.execute('INSERT INTO t VALUES (1)')
# 忘记 conn.commit()
cursor.close()
conn.close()  # 数据丢失！
```

**正确写法**：

```python
conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS t (id INTEGER)')
cursor.execute('INSERT INTO t VALUES (1)')
conn.commit()  # 必须提交
cursor.close()
conn.close()
```

### 错误2：SQL 字符串拼接导致语法错误或 SQL 注入

**错误原因**：直接使用 f-string 拼接用户输入，容易出错且不安全。

```python
# 错误写法
name = "Alice'; DROP TABLE students;--"
cursor.execute(f"SELECT * FROM students WHERE name = '{name}'")  # 灾难！
```

**正确写法**：使用参数化查询（`?` 或 `%s` 占位符）。

```python
# 正确写法（SQLite 用 ?，MySQL 用 %s）
cursor.execute('SELECT * FROM students WHERE name = ?', (name,))
```

### 错误3：忘记关闭连接导致资源泄漏

**错误原因**：未关闭连接会占用数据库资源，长时间运行可能导致连接数耗尽。

```python
# 错误写法
conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute('SELECT 1')
# 没有关闭 cursor 和 conn
```

**正确写法**：使用 `with` 语句或 `try-finally` 确保资源释放。

```python
# 正确写法：使用 with 自动管理资源
import sqlite3
with sqlite3.connect('test.db') as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    print(cursor.fetchone())
# 退出 with 块后自动关闭连接
```

---

## 5. 练习

### 练习1：数据迁移与汇总

**题目**：创建一个 SQLite 数据库 `sales.db`，包含 `orders` 表（字段：`order_id`、`product`、`amount`、`date`）。插入 5 条模拟订单数据。然后使用 Pandas 读取全部数据，计算每个产品的总销售额，并将结果写回一个新的表 `product_summary`。

**答案提示**：

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('sales.db')
# 建表 + 插入数据（略）
df = pd.read_sql_query('SELECT * FROM orders', conn)
summary = df.groupby('product')['amount'].sum().reset_index()
summary.to_sql('product_summary', conn, if_exists='replace', index=False)
conn.close()
```

### 练习2：MySQL 条件更新

**题目**：假设你有一个 MySQL 数据库 `inventory`，其中有 `items` 表（字段：`id`、`name`、`stock`）。编写代码将库存量低于 10 的商品价格提高 10%（假设还有 `price` 字段）。要求使用参数化查询，并正确处理事务。

**答案提示**：

```python
import pymysql

conn = pymysql.connect(host='localhost', user='root', password='xxx', database='inventory')
try:
    with conn.cursor() as cursor:
        cursor.execute('''
            UPDATE items 
            SET price = price * 1.1 
            WHERE stock < %s
        ''', (10,))
    conn.commit()
finally:
    conn.close()
```

---

> **延伸阅读**：官方文档 — [Python sqlite3 模块](https://docs.python.org/3/library/sqlite3.html)、[PyMySQL 文档](https://pymysql.readthedocs.io/)、[Pandas IO 工具](https://pandas.pydata.org/docs/reference/io.html)。