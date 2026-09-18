# groupby分组聚合
> 模块：Pandas数据处理(下) | 编号：第16讲 | Python数据分析实战

## 1. 概念

**groupby分组聚合**是 Pandas 中最强大的数据处理模式之一，其核心思想是“**拆分-应用-合并**”（Split-Apply-Combine）：首先按照一个或多个键将 DataFrame 拆分成若干组，然后对每组独立地应用某个函数（如求和、均值、计数等），最后将各组的结果合并成一个新的 DataFrame 或 Series。

**生活化类比**：想象你是一个班级的班主任，手里有一张全班成绩表。你想知道每个小组的平均分——你先把全班同学按小组分好（拆分），然后算出每个小组的平均分（应用），最后把各小组的平均分汇总成一张新表（合并）。这就是 groupby 做的事。

**适用场景**：按类别统计销售额、按用户计算平均消费、按时间段聚合流量、对比不同分组的分布差异等。它是数据透视、统计分析和特征工程的基础操作。

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `DataFrame.groupby()` | `df.groupby(by, axis=0, as_index=True, sort=True)` | `by`：分组键（列名、Series或列表）；`as_index`：是否以分组键作为索引；`sort`：是否对分组键排序 | `DataFrameGroupBy` 对象（惰性，不立即计算） |
| `GroupBy.agg()` | `grouped.agg(func)` | `func`：函数、函数列表或字典（列名→函数），如 `'sum'`、`'mean'`、`np.sum` | `DataFrame` 或 `Series` |
| `GroupBy.transform()` | `grouped.transform(func)` | `func`：逐组应用的函数，返回与原始行数相同的值 | 与原始 DataFrame 形状相同的 `DataFrame` |
| `GroupBy.apply()` | `grouped.apply(func)` | `func`：接收每个分组 DataFrame 作为参数的函数 | `DataFrame` 或 `Series`，形状取决于函数返回值 |
| `GroupBy.size()` | `grouped.size()` | 无参数 | `Series`，每组行数 |

**核心原理**：`groupby()` 本身是惰性操作，它只定义分组规则，不执行计算。只有当你调用 `agg()`、`sum()`、`mean()`、`size()` 等聚合方法时，数据才会真正被分组并计算。

## 3. 代码示例

### 示例1：基础分组聚合（按单列分组）

```python
import pandas as pd

# 创建示例数据：各门店的销售记录
df = pd.DataFrame({
    '门店': ['北京', '上海', '北京', '广州', '上海', '北京'],
    '季度': ['Q1', 'Q1', 'Q2', 'Q2', 'Q3', 'Q3'],
    '销售额': [120, 150, 130, 110, 160, 145]
})

# 按"门店"分组，计算各门店的总销售额
result = df.groupby('门店')['销售额'].sum()
print(result)
# 输出：
# 门店
# 北京    395
# 上海    310
# 广州    110
# Name: 销售额, dtype: int64

# 按"门店"和"季度"两列分组，计算平均销售额
result2 = df.groupby(['门店', '季度'])['销售额'].mean()
print(result2)
# 输出：
# 门店  季度
# 北京  Q1    120.0
#       Q2    130.0
#       Q3    145.0
# 上海  Q1    150.0
#       Q3    160.0
# 广州  Q2    110.0
# Name: 销售额, dtype: float64
```

### 示例2：多列聚合与agg()方法

```python
import pandas as pd
import numpy as np

# 创建订单数据
orders = pd.DataFrame({
    '客户': ['A', 'B', 'A', 'C', 'B', 'A'],
    '金额': [100, 200, 150, 300, 250, 120],
    '数量': [2, 3, 1, 4, 2, 3]
})

# 按客户分组，同时计算金额总和、金额均值、数量总和
grouped = orders.groupby('客户')
result = grouped.agg({
    '金额': ['sum', 'mean'],
    '数量': 'sum'
})
print(result)
# 输出：
#         金额        数量
#         sum   mean  sum
# 客户                  
# A      370  123.33    6
# B      450  225.00    5
# C      300  300.00    4

# 使用transform()为每行添加"该客户订单金额占比"
orders['金额占比'] = orders.groupby('客户')['金额'].transform(lambda x: x / x.sum())
print(orders)
# 输出：
#   客户  金额  数量   金额占比
# 0  A  100    2  0.270270
# 1  B  200    3  0.444444
# 2  A  150    1  0.405405
# 3  C  300    4  1.000000
# 4  B  250    2  0.555556
# 5  A  120    3  0.324324
```

### 示例3：进阶——apply()自定义分组计算

```python
import pandas as pd

# 学生成绩数据
scores = pd.DataFrame({
    '班级': ['一班', '一班', '二班', '二班', '三班'],
    '姓名': ['小明', '小红', '小刚', '小丽', '小华'],
    '分数': [85, 92, 78, 95, 88]
})

# 自定义函数：返回每班的最高分与最低分之差（极差）
def score_range(group):
    return pd.Series({
        '极差': group['分数'].max() - group['分数'].min(),
        '人数': len(group)
    })

result = scores.groupby('班级').apply(score_range)
print(result)
# 输出：
#       极差  人数
# 班级          
# 一班    7    2
# 二班   17    2
# 三班    0    1

# 使用size()统计各班级人数
counts = scores.groupby('班级').size()
print(counts)
# 输出：
# 班级
# 一班    2
# 二班    2
# 三班    1
# dtype: int64
```

## 4. 常见错误

### 错误1：忘记调用聚合方法，直接打印 groupby 对象

```python
# 错误写法
df = pd.DataFrame({'A': [1, 2, 1], 'B': [10, 20, 30]})
print(df.groupby('A'))  # 输出的是内存地址，不是结果

# 正确写法
print(df.groupby('A').sum())  # 必须调用聚合方法
```

**原因**：`groupby()` 返回的是惰性的 `DataFrameGroupBy` 对象，必须通过 `sum()`、`mean()`、`agg()` 等方法触发计算。

### 错误2：对分组后的结果直接取列名出错

```python
# 错误写法
df = pd.DataFrame({'组': ['x', 'y', 'x'], '值': [1, 2, 3]})
grouped = df.groupby('组')
# grouped['组']  # 报错：分组键不再是普通列

# 正确写法：分组后直接对数值列操作
print(grouped['值'].sum())
# 输出：
# 组
# x    4
# y    2
# Name: 值, dtype: int64
```

**原因**：分组键 `'组'` 已成为索引的一部分，不再是普通列。若想保留为列，需设置 `as_index=False`。

### 错误3：在 agg() 中混用字符串和函数时格式错误

```python
# 错误写法
df = pd.DataFrame({'组': ['a', 'a', 'b'], '值': [1, 2, 3]})
# df.groupby('组')['值'].agg(['sum', np.mean, 'count'])
# 这样写可以，但如果想对多列用不同函数，字典值必须是列表

# 正确写法
result = df.groupby('组').agg({'值': ['sum', 'mean']})
print(result)
# 输出：
#     值      
#    sum mean
# 组          
# a    3  1.5
# b    3  3.0
```

**原因**：`agg()` 的字典语法中，每个列名对应的值必须是函数或函数列表，不能是混合格式。

## 5. 练习

### 练习1：销售数据分析

给定以下销售数据，请计算每个**产品类别**在**每个季度**的总销售额，并找出销售额最高的类别。

```python
import pandas as pd

sales = pd.DataFrame({
    '类别': ['电子', '服装', '电子', '食品', '服装', '食品', '电子', '服装'],
    '季度': ['Q1', 'Q1', 'Q2', 'Q1', 'Q2', 'Q2', 'Q1', 'Q1'],
    '销售额': [500, 300, 450, 200, 350, 250, 600, 400]
})
```

**答案提示**：
```python
# 按类别和季度分组，计算销售额总和
result = sales.groupby(['类别', '季度'])['销售额'].sum()
print(result)

# 找出总销售额最高的类别
total_by_cat = sales.groupby('类别')['销售额'].sum()
print(total_by_cat.idxmax())  # 输出：电子
```

### 练习2：员工绩效分析

使用 `transform()` 为每位员工计算其**所在部门的平均工资**，并新建一列 `工资差额` 表示个人工资与部门平均工资的差值。

```python
import pandas as pd

employees = pd.DataFrame({
    '部门': ['技术', '技术', '市场', '市场', '市场'],
    '姓名': ['张三', '李四', '王五', '赵六', '孙七'],
    '工资': [12000, 15000, 9000, 11000, 10000]
})
```

**答案提示**：
```python
# 计算各部门平均工资
dept_mean = employees.groupby('部门')['工资'].transform('mean')

# 计算工资差额
employees['工资差额'] = employees['工资'] - dept_mean
print(employees)
# 输出：
#    部门  姓名     工资    工资差额
# 0  技术  张三  12000 -1500.0
# 1  技术  李四  15000  1500.0
# 2  市场  王五   9000 -1000.0
# 3  市场  赵六  11000  1000.0
# 4  市场  孙七  10000    0.0
```

---

**学习提示**：groupby 是 Pandas 数据处理的基石，掌握 `agg()` 的字典语法和 `transform()` 的逐行映射逻辑，能解决 80% 以上的分组统计需求。建议在真实数据集上多练习多列分组、多重聚合和自定义函数组合。