# Series与DataFrame核心

> 模块：Pandas数据处理(上) | 编号：第11讲 | Python数据分析实战

---

## 1. 概念

Series 和 DataFrame 是 Pandas 库中两种最核心的数据结构。**Series** 是一维带标签的数组，可以存储任意数据类型（整数、浮点数、字符串、Python 对象等），其轴标签统称为索引（index）。**DataFrame** 是二维带标签的表格结构，可以看作是由多个 Series 按列方向拼接而成，每列可以是不同的数据类型，同时拥有行索引和列索引。

**适用场景**：Series 适合处理单列数据（如某一特征的时间序列、一维数组的统计分析）；DataFrame 适合处理结构化表格数据（如 Excel 表、CSV 文件、数据库查询结果），是数据分析中最常用的数据载体。

**生活化类比**：可以把 Series 想象成一张带标签的购物清单——每一项物品（值）都对应一个名称（索引），你可以通过名称直接找到物品。而 DataFrame 则像一份 Excel 电子表格——有行号（行索引）和列名（列索引），每一列可以记录不同类型的信息（如姓名、年龄、价格），你可以通过行号和列名快速定位到任意单元格。

---

## 2. 核心API与原理

| API / 方法 | 签名 | 参数说明 | 返回值 | 核心用途 |
|---|---|---|---|---|
| `pd.Series()` | `pd.Series(data=None, index=None, dtype=None, name=None)` | `data`: 可迭代对象、字典或标量；`index`: 索引标签列表，长度须与数据一致；`dtype`: 数据类型；`name`: Series 的名称 | `Series` 对象 | 创建一维带标签数组 |
| `pd.DataFrame()` | `pd.DataFrame(data=None, index=None, columns=None, dtype=None)` | `data`: 字典、二维数组或 Series 等；`index`: 行索引；`columns`: 列索引 | `DataFrame` 对象 | 创建二维表格结构 |
| `df.head()` / `df.tail()` | `df.head(n=5)` / `df.tail(n=5)` | `n`: 返回前/后 n 行，默认 5 | `DataFrame` | 快速预览数据 |
| `df.info()` | `df.info(verbose=None, null_counts=None)` | 无必填参数 | 无（打印到控制台） | 查看列名、非空计数、数据类型和内存占用 |
| `df.describe()` | `df.describe(percentiles=None, include=None, exclude=None)` | `percentiles`: 自定义分位数列表；`include`/`exclude`: 筛选数据类型 | `DataFrame` | 生成数值列的统计摘要（计数、均值、标准差、最小值、四分位数、最大值） |

**原理说明**：Pandas 底层基于 NumPy 数组构建，但在此基础上增加了轴标签（索引）机制。Series 的索引和值分别存储在 `index` 和 `values` 属性中；DataFrame 的每一列本质上是共享同一行索引的 Series 对象。这种设计使得数据对齐、缺失值处理和分组聚合等操作变得高效且直观。

---

## 3. 代码示例

### 示例 1：创建 Series 与基础操作（入门）

```python
import pandas as pd

# 从列表创建 Series，指定索引和名称
s = pd.Series([85, 92, 78, 96], index=['张三', '李四', '王五', '赵六'], name='Python成绩')
print(s)
print('---')
print('索引列表：', list(s.index))
print('数值数组：', s.values)
print('平均值：', s.mean())
print('最高分学生：', s.idxmax())
```

**输出结果**：
```
张三    85
李四    92
王五    78
赵六    96
Name: Python成绩, dtype: int64
---
索引列表：['张三', '李四', '王五', '赵六']
数值数组：[85 92 78 96]
平均值：87.75
最高分学生：李四
```

### 示例 2：创建 DataFrame 与数据预览（进阶）

```python
import pandas as pd

# 用字典创建 DataFrame，字典的键成为列名
data = {
    '姓名': ['张三', '李四', '王五', '赵六'],
    '年龄': [23, 25, 22, 24],
    '城市': ['北京', '上海', '广州', '深圳'],
    '薪资': [12000, 15000, 9800, 13500]
}
df = pd.DataFrame(data)
print('前 2 行：')
print(df.head(2))
print('---')
print('数据概览：')
df.info()
print('---')
print('数值统计摘要：')
print(df.describe())
```

**输出结果**：
```
前 2 行：
   姓名  年龄  城市     薪资
0  张三  23  北京  12000
1  李四  25  上海  15000
---
数据概览：
<class 'pandas.core.frame.DataFrame'>
RangeIndex: 4 entries, 0 to 3
Data columns (total 4 columns):
 #   Column  Non-Null Count  Dtype 
---  ------  --------------  ----- 
 0   姓名      4 non-null      object
 1   年龄      4 non-null      int64 
 2   城市      4 non-null      object
 3   薪资      4 non-null      int64 
dtypes: int64(2), object(2)
memory usage: 256.0+ bytes
---
数值统计摘要：
             年龄          薪资
count   4.000000      4.000000
mean   23.500000  12575.000000
std     1.290994   2181.392979
min    22.000000   9800.000000
25%    22.750000  10850.000000
50%    23.500000  12750.000000
75%    24.250000  14125.000000
max    25.000000  15000.000000
```

### 示例 3：Series 与 DataFrame 的协同操作（进阶）

```python
import pandas as pd

# 创建 DataFrame
df = pd.DataFrame({
    '产品': ['A', 'B', 'C', 'D'],
    '单价': [10, 20, 15, 30],
    '销量': [100, 80, 120, 60]
})

# 提取"单价"列（返回 Series）
prices = df['单价']
print('单价列数据类型：', type(prices))

# 用 Series 进行向量化运算：计算总销售额
df['销售额'] = df['单价'] * df['销量']
print('添加销售额列后的 DataFrame：')
print(df)
print('---')

# 从 DataFrame 中筛选出销售额超过 1500 的行
high_sales = df[df['销售额'] > 1500]
print('高销售额记录：')
print(high_sales)
print('---')

# 按产品列设置索引，并提取特定行
df_indexed = df.set_index('产品')
print('按产品提取 B 产品数据：')
print(df_indexed.loc['B'])
```

**输出结果**：
```
单价列数据类型： <class 'pandas.core.series.Series'>
添加销售额列后的 DataFrame：
  产品  单价  销量   销售额
0  A  10  100  1000
1  B  20   80  1600
2  C  15  120  1800
3  D  30   60  1800
---
高销售额记录：
  产品  单价  销量   销售额
1  B  20   80  1600
2  C  15  120  1800
3  D  30   60  1800
---
按产品提取 B 产品数据：
单价      20
销量      80
销售额    1600
Name: B, dtype: int64
```

---

## 4. 常见错误

### 错误 1：索引长度与数据长度不匹配

```python
import pandas as pd

# 错误写法：3 个数据却给了 4 个索引
# s = pd.Series([1, 2, 3], index=['a', 'b', 'c', 'd'])

# 正确写法：确保索引长度与数据长度一致
s = pd.Series([1, 2, 3], index=['a', 'b', 'c'])
print(s)
```

**错误原因**：`pd.Series()` 要求 `data` 和 `index` 的长度严格相等，否则抛出 `ValueError: Length of values (3) does not match length of index (4)`。

### 错误 2：混淆 `loc` 和 `iloc` 的用法

```python
import pandas as pd

df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]}, index=['x', 'y', 'z'])

# 错误写法：iloc 使用标签索引会报错
# print(df.iloc['x'])

# 正确写法：loc 按标签索引，iloc 按整数位置索引
print(df.loc['x'])   # 按行标签取
print(df.iloc[0])    # 按行位置取
```

**错误原因**：`loc` 是基于标签的索引器，`iloc` 是基于整数位置的索引器。新手常将两者混用，导致 `KeyError` 或 `IndexError`。

### 错误 3：直接对 DataFrame 做布尔索引时忘记加列名

```python
import pandas as pd

df = pd.DataFrame({'年龄': [23, 25, 22], '薪资': [12000, 15000, 9800]})

# 错误写法：直接写列名会报 NameError
# filtered = df[年龄 > 24]

# 正确写法：必须通过 df['列名'] 或 df.列名 引用列
filtered = df[df['年龄'] > 24]
print(filtered)
```

**错误原因**：在 Pandas 的布尔索引中，条件表达式必须完整引用 DataFrame 的列（如 `df['年龄']`），不能像在 SQL 中那样直接写列名。

---

## 5. 练习

### 练习 1（动手题）
创建一个包含 5 名学生信息的 DataFrame，列包括：`姓名`、`数学`、`英语`、`语文`（成绩为 0-100 的整数）。完成以下任务：
1. 添加一列 `总分`，计算三门成绩之和；
2. 筛选出总分大于 250 的学生；
3. 按 `总分` 降序排序，并显示前三名。

**答案提示**：
```python
import pandas as pd

df = pd.DataFrame({
    '姓名': ['张三', '李四', '王五', '赵六', '孙七'],
    '数学': [85, 92, 78, 96, 88],
    '英语': [90, 85, 88, 92, 79],
    '语文': [88, 90, 82, 95, 85]
})
df['总分'] = df['数学'] + df['英语'] + df['语文']
top_students = df[df['总分'] > 250].sort_values('总分', ascending=False)
print(top_students.head(3))
```

### 练习 2（思考题）
Series 和 DataFrame 在索引对齐方面有什么特性？如果两个 Series 的索引不完全一致，进行算术运算时会发生什么？请写出代码验证你的猜想。

**答案提示**：Pandas 在进行算术运算时会自动按索引对齐数据。索引不匹配的位置结果为 `NaN`（缺失值）。例如：
```python
s1 = pd.Series([1, 2, 3], index=['a', 'b', 'c'])
s2 = pd.Series([10, 20, 30], index=['b', 'c', 'd'])
print(s1 + s2)
# 输出：a NaN, b 22.0, c 33.0, d NaN
```
这正是 Pandas 区别于 NumPy 数组的重要特性——数据对齐机制。