# 窗口函数ROW_NUMBER/RANK

> 模块：SQL与数据库 | 编号：第37讲 | Python数据分析实战

---

## 1. 概念

窗口函数（Window Function）是 SQL 中一类特殊的函数，它能够在**不改变原始行数**的前提下，对每一行计算基于其所在"窗口"（即一组相关行）的聚合值或排名值。与 `GROUP BY` 不同，窗口函数不会将多行合并为一行，而是为每一行保留其原始位置，同时附加计算出的结果。

`ROW_NUMBER()` 和 `RANK()` 是其中最常用的两个排名窗口函数：
- **ROW_NUMBER()**：为窗口内的每一行分配一个**连续且唯一**的序号（1, 2, 3, ...），即使排序值相同也会强制区分先后。
- **RANK()**：为窗口内的每一行分配排名，**排序值相同则排名相同**，但下一个排名会跳过（如 1, 1, 3）。

**生活化类比**：想象一场班级考试排名。`ROW_NUMBER()` 就像老师按学号顺序点名，即使两人分数相同，也会按点名先后给出 1 号、2 号；而 `RANK()` 则像竞赛排名——两人并列第一，则没有第二名，下一位直接是第三名。

**适用场景**：数据去重（取每组最新一条）、分组 Top-N 查询、排行榜生成、数据分页等。

---

## 2. 核心API与原理

在 Python 中，我们通常通过 **SQLite**（内置 `sqlite3` 模块）或 **DuckDB**（`duckdb` 库）来执行 SQL 窗口函数。以下以 `sqlite3` 为例（SQLite 3.25+ 支持窗口函数）。

| API / 语法 | 签名 / 参数 | 返回值 | 说明 |
|---|---|---|---|
| `ROW_NUMBER()` | `ROW_NUMBER() OVER (PARTITION BY col1 ORDER BY col2)` | 整数（1 开始） | 为每个分区内按 `col2` 排序后的行分配连续唯一序号 |
| `RANK()` | `RANK() OVER (PARTITION BY col1 ORDER BY col2)` | 整数（1 开始） | 为每个分区内按 `col2` 排序后的行分配排名，并列时跳过后续名次 |
| `DENSE_RANK()` | `DENSE_RANK() OVER (PARTITION BY col1 ORDER BY col2)` | 整数（1 开始） | 与 `RANK()` 类似，但并列时不跳过名次（1, 1, 2） |
| `OVER()` 子句 | `OVER ([PARTITION BY 列] [ORDER BY 列])` | 窗口定义 | 定义分区和排序规则；省略 `PARTITION BY` 则整个表为一个窗口 |
| `sqlite3.connect()` | `connect(database)` | `Connection` 对象 | 连接 SQLite 数据库（可用 `":memory:"` 创建内存库） |

**原理说明**：窗口函数在 SQL 查询的 **`WHERE`、`GROUP BY`、`HAVING` 之后**，**`ORDER BY` 之前**执行。`OVER()` 子句定义了"窗口"的范围：`PARTITION BY` 将数据分组（类似分组但保留所有行），`ORDER BY` 决定组内行的计算顺序。

---

## 3. 代码示例

### 示例 1：基础排名——ROW_NUMBER 与 RANK 对比

```python
import sqlite3

# 创建内存数据库和表
conn = sqlite3.connect(":memory:")
cur = conn.cursor()
cur.execute("CREATE TABLE scores (student TEXT, subject TEXT, score INT)")
cur.executemany(
    "INSERT INTO scores VALUES (?, ?, ?)",
    [("Alice", "Math", 90), ("Bob", "Math", 85), ("Carol", "Math", 90),
     ("Alice", "English", 88), ("Bob", "English", 92), ("Carol", "English", 88)]
)
conn.commit()

# 使用 ROW_NUMBER 和 RANK 按分数排名（不分区）
cur.execute("""
    SELECT student, subject, score,
           ROW_NUMBER() OVER (ORDER BY score DESC) AS row_num,
           RANK() OVER (ORDER BY score DESC) AS rank_num
    FROM scores
    ORDER BY score DESC
""")
for row in cur.fetchall():
    print(row)
# 输出:
# ('Bob', 'English', 92, 1, 1)
# ('Alice', 'Math', 90, 2, 2)
# ('Carol', 'Math', 90, 3, 2)   ← ROW_NUMBER 强制区分，RANK 并列
# ('Alice', 'English', 88, 4, 4) ← RANK 跳过第3名
# ('Bob', 'Math', 85, 5, 5)
# ('Carol', 'English', 88, 6, 4)
conn.close()
```

### 示例 2：分组 Top-N——每科最高分学生

```python
import sqlite3

conn = sqlite3.connect(":memory:")
cur = conn.cursor()
cur.execute("CREATE TABLE scores (student TEXT, subject TEXT, score INT)")
cur.executemany(
    "INSERT INTO scores VALUES (?, ?, ?)",
    [("Alice", "Math", 90), ("Bob", "Math", 85), ("Carol", "Math", 95),
     ("Alice", "English", 88), ("Bob", "English", 92), ("Carol", "English", 85)]
)
conn.commit()

# 按科目分区，取每科第一名（使用 ROW_NUMBER，若有并列会取其中一条）
cur.execute("""
    SELECT subject, student, score FROM (
        SELECT subject, student, score,
               ROW_NUMBER() OVER (PARTITION BY subject ORDER BY score DESC) AS rn
        FROM scores
    ) WHERE rn = 1
    ORDER BY subject
""")
for row in cur.fetchall():
    print(row)
# 输出:
# ('English', 'Bob', 92)
# ('Math', 'Carol', 95)
conn.close()
```

### 示例 3：进阶——使用 DuckDB 实现并列排名与数据去重

```python
# 需要先安装: pip install duckdb
import duckdb

# 创建内存连接
conn = duckdb.connect()

# 创建并插入数据
conn.execute("CREATE TABLE orders (order_id INT, customer TEXT, amount DECIMAL(10,2))")
conn.executemany(
    "INSERT INTO orders VALUES (?, ?, ?)",
    [(1, "Alice", 100.0), (2, "Bob", 250.5), (3, "Alice", 80.0),
     (4, "Carol", 120.0), (5, "Bob", 250.5), (6, "Alice", 300.0)]
)

# 需求1：每个客户按金额排名（并列用 RANK）
print("=== 客户金额排名（RANK） ===")
result = conn.execute("""
    SELECT customer, amount,
           RANK() OVER (PARTITION BY customer ORDER BY amount DESC) AS rk
    FROM orders
    ORDER BY customer, rk
""").fetchall()
for row in result:
    print(row)
# 输出:
# ('Alice', 300.0, 1)
# ('Alice', 100.0, 2)
# ('Alice', 80.0, 3)
# ('Bob', 250.5, 1)
# ('Bob', 250.5, 1)   ← 并列第1
# ('Carol', 120.0, 1)

# 需求2：数据去重——保留每个客户金额最高的订单（ROW_NUMBER）
print("\n=== 每个客户最高金额订单（去重） ===")
result = conn.execute("""
    SELECT order_id, customer, amount FROM (
        SELECT order_id, customer, amount,
               ROW_NUMBER() OVER (PARTITION BY customer ORDER BY amount DESC) AS rn
        FROM orders
    ) WHERE rn = 1
    ORDER BY customer
""").fetchall()
for row in result:
    print(row)
# 输出:
# (6, 'Alice', 300.0)
# (2, 'Bob', 250.5)
# (4, 'Carol', 120.0)

conn.close()
```

---

## 4. 常见错误

### 错误 1：忘记 `OVER()` 子句

```sql
-- 错误写法
SELECT student, ROW_NUMBER() FROM scores;

-- 错误原因：ROW_NUMBER 是窗口函数，必须配合 OVER() 使用，否则 SQLite 报错
-- "wrong number of arguments to function row_number()"

-- 正确写法
SELECT student, ROW_NUMBER() OVER (ORDER BY score DESC) FROM scores;
```

### 错误 2：在 `WHERE` 子句中使用窗口函数

```sql
-- 错误写法
SELECT * FROM scores
WHERE ROW_NUMBER() OVER (ORDER BY score DESC) = 1;

-- 错误原因：窗口函数在 WHERE 之后执行，不能直接在 WHERE 中引用
-- 正确写法：使用子查询或 CTE 包裹
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (ORDER BY score DESC) AS rn
    FROM scores
) WHERE rn = 1;
```

### 错误 3：混淆 `RANK()` 和 `DENSE_RANK()` 的跳过行为

```sql
-- 假设分数为 90, 90, 85
-- RANK() 结果: 1, 1, 3    （跳过2）
-- DENSE_RANK() 结果: 1, 1, 2  （不跳过）

-- 错误原因：误以为 RANK 和 DENSE_RANK 相同
-- 正确做法：需要连续排名（1,1,2）时用 DENSE_RANK；需要标准竞赛排名（1,1,3）时用 RANK
```

---

## 5. 练习

### 练习 1：找出每个部门薪资最高的员工（允许并列）

**题目**：有一张员工表 `employees(id, name, dept, salary)`，请用 `RANK()` 找出每个部门薪资最高的员工。若有多人并列最高，都要输出。

**答案提示**：
```sql
SELECT dept, name, salary FROM (
    SELECT dept, name, salary,
           RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS rk
    FROM employees
) WHERE rk = 1;
```

### 练习 2：去除重复订单记录

**题目**：订单表 `orders(order_id, customer, order_date)` 中存在同一客户同一天下的多笔重复订单（`order_id` 不同但内容相同）。请用 `ROW_NUMBER()` 为每个客户每天的订单按 `order_id` 排序，保留第一条，删除其余重复项。

**答案提示**：
```sql
-- 先标记重复项
SELECT order_id, customer, order_date,
       ROW_NUMBER() OVER (PARTITION BY customer, order_date ORDER BY order_id) AS rn
FROM orders;

-- 然后删除 rn > 1 的记录（在支持 DELETE 的数据库中）
-- 或使用 CTE + DELETE 语法
```

---

> **小结**：`ROW_NUMBER()` 和 `RANK()` 是 SQL 窗口函数中最基础也最实用的两个。掌握它们的关键在于理解 `OVER()` 子句的分区与排序逻辑，以及区分"唯一序号"与"并列排名"的语义差异。在 Python 中通过 `sqlite3` 或 `duckdb` 即可零成本实践这些功能。