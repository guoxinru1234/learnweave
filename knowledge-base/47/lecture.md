# 多源数据采集与整合

> 模块：实战：销售数据分析 | 编号：第47讲 | Python数据分析实战

---

## 1. 概念

多源数据采集与整合，是指从多个不同来源（如CSV文件、Excel表格、SQL数据库、API接口等）获取数据，并将其合并为一份统一、干净、可供分析的数据集的过程。在真实的销售分析场景中，数据往往散落在各处：线上订单存在数据库中，线下门店销售记录在Excel里，客户信息可能来自CRM系统导出的CSV。数据分析师的首要任务，就是把这些“各自为政”的数据汇聚到一起。

**生活化类比**：想象你是一位厨师，要为顾客做一道“什锦炒饭”。米饭（订单数据）在电饭煲里，鸡蛋（客户数据）在冰箱，蔬菜（门店数据）在菜篮里。你不可能直接把电饭煲、冰箱和菜篮端上桌——你需要把食材从各自的“容器”中取出，清洗（清洗数据）、切丁（统一格式），然后倒进同一个炒锅（合并数据集）里翻炒均匀，才能端出一盘完整的炒饭。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `pandas.read_csv()` | `read_csv(filepath_or_buffer, sep=',', encoding=None, ...)` | `filepath_or_buffer`：文件路径或URL；`sep`：分隔符，默认逗号；`encoding`：文件编码（如`'utf-8'`、`'gbk'`） | `DataFrame`：解析后的表格数据 |
| `pandas.read_excel()` | `read_excel(io, sheet_name=0, header=0, ...)` | `io`：Excel文件路径；`sheet_name`：工作表名称或索引，默认第一个工作表；`header`：表头所在行 | `DataFrame`：解析后的表格数据 |
| `pandas.read_sql()` | `read_sql(sql, con, params=None)` | `sql`：SQL查询字符串；`con`：数据库连接对象（如SQLAlchemy engine）；`params`：查询参数 | `DataFrame`：查询结果 |
| `DataFrame.merge()` | `merge(right, how='inner', on=None, left_on=None, right_on=None)` | `right`：要合并的另一个DataFrame；`how`：合并方式（`'inner'`/`'outer'`/`'left'`/`'right'`）；`on`：合并键列名；`left_on`/`right_on`：左右两侧键列名（不同名时使用） | `DataFrame`：合并后的新DataFrame |
| `pandas.concat()` | `concat(objs, axis=0, join='outer', ignore_index=False)` | `objs`：DataFrame的列表或字典；`axis`：合并轴，0为纵向堆叠，1为横向拼接；`join`：`'outer'`并集或`'inner'`交集 | `DataFrame`：拼接后的新DataFrame |

---

## 3. 代码示例

### 示例1：从CSV和Excel读取数据并纵向合并（基础）

```python
import pandas as pd

# 模拟：线上订单数据（CSV格式）
df_online = pd.DataFrame({
    'order_id': [1001, 1002, 1003],
    'amount': [299, 159, 499],
    'channel': ['online', 'online', 'online']
})

# 模拟：线下门店订单数据（Excel格式，这里用DataFrame模拟）
df_store = pd.DataFrame({
    'order_id': [2001, 2002],
    'amount': [399, 199],
    'channel': ['store', 'store']
})

# 真实场景中：
# df_online = pd.read_csv('online_orders.csv')
# df_store = pd.read_excel('store_orders.xlsx', sheet_name='Sheet1')

# 纵向堆叠两份数据（行方向合并）
df_all = pd.concat([df_online, df_store], axis=0, ignore_index=True)
print(df_all)
# 输出:
#    order_id  amount channel
# 0      1001     299  online
# 1      1002     159  online
# 2      1003     499  online
# 3      2001     399   store
# 4      2002     199   store

print(f"合并后总行数: {len(df_all)}")
# 输出: 合并后总行数: 5
```

### 示例2：通过公共键横向合并不同来源的数据（进阶）

```python
import pandas as pd

# 数据源1：订单明细（来自CSV）
orders = pd.DataFrame({
    'order_id': [1001, 1002, 1003, 1004],
    'product': ['手机', '耳机', '充电器', '手机壳'],
    'quantity': [1, 2, 3, 5]
})

# 数据源2：客户信息（来自Excel）
customers = pd.DataFrame({
    'order_id': [1001, 1002, 1004],
    'customer_name': ['张三', '李四', '王五'],
    'city': ['北京', '上海', '广州']
})

# 数据源3：产品单价（来自SQL查询，这里用DataFrame模拟）
prices = pd.DataFrame({
    'product': ['手机', '耳机', '充电器', '手机壳'],
    'unit_price': [3999, 299, 49, 19]
})

# 第一步：订单与客户信息按 order_id 左连接（保留所有订单）
df_step1 = orders.merge(customers, on='order_id', how='left')
print("第一步合并结果：")
print(df_step1)
# 输出:
#    order_id product  quantity customer_name   city
# 0      1001     手机         1          张三    北京
# 1      1002     耳机         2          李四    上海
# 2      1003   充电器         3          NaN   NaN
# 3      1004   手机壳         5          王五    广州

# 第二步：与产品单价按 product 合并
df_final = df_step1.merge(prices, on='product', how='left')

# 计算销售额
df_final['sales_amount'] = df_final['quantity'] * df_final['unit_price']
print("\n最终整合结果：")
print(df_final)
# 输出:
#    order_id product  quantity customer_name   city  unit_price  sales_amount
# 0      1001     手机         1          张三    北京        3999          3999
# 1      1002     耳机         2          李四    上海         299           598
# 2      1003   充电器         3          NaN   NaN          49           147
# 3      1004   手机壳         5          王五    广州          19            95

# 汇总分析：各城市销售额
city_sales = df_final.groupby('city')['sales_amount'].sum()
print("\n各城市销售额：")
print(city_sales)
# 输出:
# city
# 上海     598
# 北京    3999
# 广州      95
# NaN     147
# Name: sales_amount, dtype: int64
```

### 示例3：从SQL数据库读取并与文件数据整合（综合）

```python
import pandas as pd
import sqlite3  # 使用Python内置的SQLite数据库演示

# 创建内存数据库并写入模拟数据
conn = sqlite3.connect(':memory:')
conn.execute("CREATE TABLE payment (order_id INT, pay_method TEXT, pay_amount REAL)")
conn.executemany(
    "INSERT INTO payment VALUES (?, ?, ?)",
    [(1001, '支付宝', 3999), (1002, '微信', 598), (1003, '现金', 147)]
)
conn.commit()

# 从SQL数据库读取支付信息
df_payment = pd.read_sql("SELECT * FROM payment", conn)
print("从数据库读取的支付数据：")
print(df_payment)
# 输出:
#    order_id pay_method  pay_amount
# 0      1001       支付宝      3999.0
# 1      1002        微信       598.0
# 2      1003        现金       147.0

# 已有的订单文件数据
df_orders = pd.DataFrame({
    'order_id': [1001, 1002, 1003, 1004],
    'product': ['手机', '耳机', '充电器', '手机壳'],
    'quantity': [1, 2, 3, 5]
})

# 整合：订单数据与支付数据按 order_id 内连接
df_integrated = df_orders.merge(df_payment, on='order_id', how='inner')
print("\n整合后的完整数据：")
print(df_integrated)
# 输出:
#    order_id product  quantity pay_method  pay_amount
# 0      1001     手机         1       支付宝      3999.0
# 1      1002     耳机         2        微信       598.0
# 2      1003   充电器         3        现金       147.0

# 关闭数据库连接
conn.close()
```

---

## 4. 常见错误

### 错误1：合并键名称不一致导致报错或错误结果

**错误原因**：两个DataFrame中表示同一含义的列名不同（如一个叫`order_id`，另一个叫`orderId`），直接使用`on`参数会报`KeyError`，或者因未指定键而产生笛卡尔积。

```python
# 错误写法
df1 = pd.DataFrame({'order_id': [1, 2], 'amount': [100, 200]})
df2 = pd.DataFrame({'orderId': [1, 2], 'customer': ['A', 'B']})
# result = df1.merge(df2, on='order_id')  # KeyError: 'orderId' 不存在

# 正确写法：使用 left_on 和 right_on 分别指定
result = df1.merge(df2, left_on='order_id', right_on='orderId')
print(result)
# 输出:
#    order_id  amount  orderId customer
# 0         1     100        1       A
# 1         2     200        2       B
```

### 错误2：编码问题导致读取文件失败

**错误原因**：CSV文件可能是GBK编码（中文Windows系统常见），而`read_csv`默认使用UTF-8编码，导致`UnicodeDecodeError`。

```python
# 错误写法
# df = pd.read_csv('sales_gbk.csv')  # UnicodeDecodeError: 'utf-8' codec can't decode byte

# 正确写法：指定编码为 gbk
df = pd.read_csv('sales_gbk.csv', encoding='gbk')
# 如果仍失败，可尝试 encoding='gb18030'（更全面的GBK超集）
```

### 错误3：合并后出现重复列名导致数据混乱

**错误原因**：两个DataFrame除了合并键外还有其他相同列名（如都有`amount`列），合并后Pandas会自动添加`_x`和`_y`后缀，新手容易取错列。

```python
# 错误场景
df_a = pd.DataFrame({'order_id': [1, 2], 'amount': [100, 200]})
df_b = pd.DataFrame({'order_id': [1, 2], 'amount': [90, 180]})

# 直接合并
result = df_a.merge(df_b, on='order_id')
print(result)
# 输出:
#    order_id  amount_x  amount_y
# 0         1       100        90
# 1         2       200       180

# 正确做法：合并前重命名列，明确语义
df_b = df_b.rename(columns={'amount': 'discount_amount'})
result = df_a.merge(df_b, on='order_id')
print(result)
# 输出:
#    order_id  amount  discount_amount
# 0         1     100               90
# 1         2     200              180
```

---

## 5. 练习

### 练习1：多文件批量读取与合并（动手题）

**题目**：假设你的销售数据按月份拆分为12个CSV文件（`sales_2024_01.csv` 到 `sales_2024_12.csv`），每个文件包含列：`order_id`, `date`, `amount`, `region`。请编写代码，使用循环和`pd.concat()`将所有文件读取并合并为一个DataFrame，并计算全年总销售额。

**答案提示**：

```python
import pandas as pd

frames = []
for month in range(1, 13):
    filename = f'sales_2024_{month:02d}.csv'
    df_month = pd.read_csv(filename)
    frames.append(df_month)

df_year = pd.concat(frames, axis=0, ignore_index=True)
total_sales = df_year['amount'].sum()
print(f'全年总销售额: {total_sales}')
```

### 练习2：多源数据整合分析（思考题）

**题目**：你手头有三份数据：①`orders.csv`（订单号、产品ID、数量）；②`products.xlsx`（产品ID、产品名、单价）；③`customers`表（在MySQL数据库中，含客户ID、客户名、城市）。订单表中有`customer_id`字段关联客户表。请描述你的整合步骤，并思考：如果订单表中的某些`customer_id`在客户表中不存在，应该使用哪种`how`参数？为什么？

**答案提示**：步骤为：①分别用`read_csv`、`read_excel`、`read_sql`读取三份数据；②先将`orders`与`products`按`产品ID`合并（`how='left'`保证所有订单保留）；③再将结果与`customers`按`customer_id`合并。应使用`how='left'`，因为订单是分析主体，即使客户信息缺失（如已注销客户），订单记录仍应保留在分析结果中，缺失的客户信息显示为`NaN`。