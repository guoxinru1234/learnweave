# 数据透视表pivot_table

> 模块：Pandas数据处理(下) | 编号：第17讲 | Python数据分析实战

---

## 1. 概念

数据透视表（Pivot Table）是一种用于**对数据进行分组聚合、重塑和汇总**的强大工具。它允许你指定一个或多个列作为“行索引”（index），一个或多个列作为“列索引”（columns），并对剩余的值列（values）执行聚合运算（如求和、均值、计数等），最终生成一个**二维表格**来展示数据的多维关系。

**生活化类比**：想象你有一堆乐高积木（原始数据），每个积木有不同的颜色、形状和大小。数据透视表就像是一个**整理盒**——你可以决定按“颜色”分行、按“形状”分列，然后在每个格子里放上该颜色和形状组合的积木总数（聚合值）。这样，原本杂乱的数据就变成了一张清晰易懂的二维汇总表。

**适用场景**：销售数据分析（按地区×产品统计销售额）、用户行为分析（按渠道×月份统计活跃用户数）、市场调研（按年龄段×性别统计平均消费金额）等。

---

## 2. 核心API与原理

Pandas 中与数据透视表相关的核心 API 如下：

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `DataFrame.pivot_table()` | `df.pivot_table(values=None, index=None, columns=None, aggfunc='mean', fill_value=None, margins=False, dropna=True, observed=False)` | `values`: 需要聚合的列名或列名列表；`index`: 作为行索引的列名或列表；`columns`: 作为列索引的列名或列表；`aggfunc`: 聚合函数（字符串或函数，如 `'sum'`, `'mean'`, `'count'`, `np.sum`），默认为 `'mean'`；`fill_value`: 填充缺失值的标量；`margins`: 是否添加行/列总计（`True`/`False`）；`dropna`: 是否排除全为 NaN 的行/列；`observed`: 仅用于分类数据，是否只显示实际出现的类别 | 返回一个新的 `DataFrame`，即透视表结果 |
| `pandas.pivot_table()` | `pd.pivot_table(data, values=None, index=None, columns=None, aggfunc='mean', fill_value=None, margins=False, dropna=True, observed=False)` | 与 `DataFrame.pivot_table()` 相同，只是第一个参数传入 DataFrame | 返回一个新的 `DataFrame` |
| `DataFrame.pivot()` | `df.pivot(index=None, columns=None, values=None)` | 与 `pivot_table` 类似，但**不允许聚合**（要求索引/列组合唯一），适用于数据重塑而非汇总 | 返回重塑后的 `DataFrame` |

**原理说明**：`pivot_table` 本质上结合了 `groupby` 和 `unstack` 的功能。它先根据 `index` 和 `columns` 指定的列对数据进行分组，然后对 `values` 指定的列应用 `aggfunc` 聚合函数，最后将分组结果重塑为二维表格形式。如果指定多个聚合函数，结果将生成多层列索引。

---

## 3. 代码示例

### 示例 1：基础用法——单索引、单值、单聚合

```python
import pandas as pd

# 创建示例销售数据
df = pd.DataFrame({
    '地区': ['华东', '华南', '华东', '华北', '华南', '华东'],
    '产品': ['A', 'A', 'B', 'A', 'B', 'A'],
    '销售额': [100, 150, 200, 120, 180, 130],
    '数量': [10, 15, 20, 12, 18, 13]
})
print("原始数据：")
print(df)

# 按地区汇总销售额（默认聚合方式为均值）
pivot1 = df.pivot_table(values='销售额', index='地区', aggfunc='sum')
print("\n按地区汇总销售额（求和）：")
print(pivot1)

# 输出结果：
# 原始数据：
#    地区 产品  销售额  数量
# 0  华东  A   100   10
# 1  华南  A   150   15
# 2  华东  B   200   20
# 3  华北  A   120   12
# 4  华南  B   180   18
# 5  华东  A   130   13
#
# 按地区汇总销售额（求和）：
# 销售额
# 地区
# 华东     430
# 华北     120
# 华南     330
```

### 示例 2：进阶用法——多索引、多列、多聚合

```python
import pandas as pd
import numpy as np

# 使用相同数据，创建更复杂的透视表
df = pd.DataFrame({
    '地区': ['华东', '华南', '华东', '华北', '华南', '华东'],
    '产品': ['A', 'A', 'B', 'A', 'B', 'A'],
    '销售额': [100, 150, 200, 120, 180, 130],
    '数量': [10, 15, 20, 12, 18, 13]
})

# 行索引为地区，列索引为产品，同时统计销售额总和与数量均值
pivot2 = df.pivot_table(
    values=['销售额', '数量'],
    index='地区',
    columns='产品',
    aggfunc={'销售额': 'sum', '数量': 'mean'},
    fill_value=0  # 将缺失值填充为0
)
print("多值、多聚合透视表：")
print(pivot2)

# 输出结果：
# 多值、多聚合透视表：
#         销售额      数量
# 产品        A    B    A    B
# 地区
# 华东     230  200  11.5  20
# 华北     120    0  12.0   0
# 华南     150  180  15.0  18
```

### 示例 3：高级用法——添加总计行列（margins）

```python
import pandas as pd

# 创建订单数据
orders = pd.DataFrame({
    '城市': ['北京', '上海', '广州', '北京', '上海', '广州'],
    '季度': ['Q1', 'Q1', 'Q1', 'Q2', 'Q2', 'Q2'],
    '订单额': [500, 600, 450, 700, 550, 800]
})

# 添加总计行和总计列
pivot3 = orders.pivot_table(
    values='订单额',
    index='城市',
    columns='季度',
    aggfunc='sum',
    margins=True,          # 添加总计
    margins_name='总计'     # 自定义总计名称
)
print("带总计的透视表：")
print(pivot3)

# 输出结果：
# 带总计的透视表：
# 季度     Q1    Q2   总计
# 城市
# 北京    500   700  1200
# 上海    600   550  1150
# 广州    450   800  1250
# 总计   1550  2050  3600
```

---

## 4. 常见错误

### 错误 1：混淆 `pivot()` 和 `pivot_table()`

**错误原因**：`pivot()` 不允许重复的索引-列组合，如果数据中存在重复组合会抛出 `ValueError: Index contains duplicate entries, cannot reshape`。新手常将两者混用。

```python
# 错误示例
import pandas as pd

df = pd.DataFrame({
    '地区': ['华东', '华东'],  # 有重复
    '产品': ['A', 'A'],
    '销售额': [100, 200]
})

# 这行会报错
# df.pivot(index='地区', columns='产品', values='销售额')

# 正确写法：使用 pivot_table 允许聚合
correct = df.pivot_table(index='地区', columns='产品', values='销售额', aggfunc='sum')
print(correct)
```

### 错误 2：忘记指定 `aggfunc` 导致结果不符合预期

**错误原因**：`pivot_table` 默认的聚合函数是 `'mean'`（均值），而不是求和。很多新手期望得到总和，却得到平均值。

```python
# 错误示例
import pandas as pd

df = pd.DataFrame({
    '地区': ['华东', '华东', '华南'],
    '销售额': [100, 200, 150]
})

# 错误：默认是均值，不是总和
pivot_wrong = df.pivot_table(values='销售额', index='地区')
print(pivot_wrong)  # 华东显示 150（均值），而非 300

# 正确写法：明确指定 aggfunc='sum'
pivot_correct = df.pivot_table(values='销售额', index='地区', aggfunc='sum')
print(pivot_correct)  # 华东显示 300
```

### 错误 3：忽略缺失值处理

**错误原因**：当某些组合不存在数据时，透视表会生成 NaN。如果不处理，后续计算可能出错。

```python
# 错误示例
import pandas as pd

df = pd.DataFrame({
    '地区': ['华东', '华南'],
    '产品': ['A', 'B'],
    '销售额': [100, 150]
})

pivot = df.pivot_table(values='销售额', index='地区', columns='产品', aggfunc='sum')
print(pivot)
# 输出包含 NaN：
# 产品      A      B
# 地区
# 华东   100.0    NaN
# 华南    NaN    150.0

# 正确写法：使用 fill_value 参数填充
pivot_fixed = df.pivot_table(
    values='销售额', index='地区', columns='产品',
    aggfunc='sum', fill_value=0
)
print(pivot_fixed)
# 输出：
# 产品    A    B
# 地区
# 华东   100    0
# 华南     0  150
```

---

## 5. 练习

### 练习 1：多维度销售分析

给定以下数据，请生成一个透视表：行索引为 `'月份'`，列索引为 `'产品'`，值为 `'销售额'` 的总和，并添加总计行列。

```python
import pandas as pd

sales_data = pd.DataFrame({
    '月份': ['1月', '1月', '2月', '2月', '3月', '3月'],
    '产品': ['手机', '电脑', '手机', '电脑', '手机', '电脑'],
    '销售额': [5000, 8000, 6000, 7500, 5500, 9000]
})
```

**答案提示**：

```python
result = sales_data.pivot_table(
    values='销售额', index='月份', columns='产品',
    aggfunc='sum', margins=True, margins_name='总计'
)
print(result)
```

### 练习 2：多聚合函数对比

使用 `pivot_table` 同时计算每个地区每种产品的**销售额总和**和**订单数量均值**，要求使用字典形式的 `aggfunc` 参数。

```python
import pandas as pd

df = pd.DataFrame({
    '地区': ['华东', '华东', '华南', '华南', '华北'],
    '产品': ['A', 'B', 'A', 'B', 'A'],
    '销售额': [100, 200, 150, 180, 120],
    '订单数': [5, 8, 6, 9, 4]
})
```

**答案提示**：

```python
result = df.pivot_table(
    values=['销售额', '订单数'],
    index='地区',
    columns='产品',
    aggfunc={'销售额': 'sum', '订单数': 'mean'},
    fill_value=0
)
print(result)
# 观察输出结果，思考为什么销售额显示为整数而订单数显示为小数
```