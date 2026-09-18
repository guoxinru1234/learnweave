# merge/join/concat合并

> 模块：Pandas数据处理(下) | 编号：第18讲 | Python数据分析实战

## 1. 概念

在数据分析中，我们经常需要将多个数据表合并为一个完整的表。Pandas 提供了三种主要的合并方式：`merge`、`join` 和 `concat`。`merge` 类似于 SQL 中的 JOIN 操作，根据一个或多个键（key）将两个 DataFrame 的行连接起来，适用于"列与列"之间的关联合并；`join` 是 `merge` 在索引上的便捷封装，专门用于按索引合并；`concat` 则是纯粹的拼接，沿轴方向（行或列）将数据堆叠在一起，不关心键的匹配关系。

**生活化类比**：想象你在整理班级通讯录。`merge` 就像把"学生姓名表"和"成绩表"按"学号"这一共同字段对齐，把同一个人在不同表格里的信息拼成一行；`join` 类似但必须用"座位号"（索引）来对齐；而 `concat` 则像把两个班的名单直接上下叠放（行拼接）或把"姓名列"和"电话列"左右并排（列拼接），不关心行与行之间的对应关系。

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `pd.merge()` | `pd.merge(left, right, how='inner', on=None, left_on=None, right_on=None, suffixes=('_x', '_y'))` | `left`/`right`：要合并的两个 DataFrame；`how`：连接方式（`'inner'`/`'outer'`/`'left'`/`'right'`）；`on`：共同列名；`left_on`/`right_on`：左右表不同的键列名；`suffixes`：重复列名的后缀 | 合并后的新 DataFrame |
| `DataFrame.join()` | `df1.join(df2, how='left', on=None, lsuffix='', rsuffix='')` | `df2`：要合并的另一个 DataFrame；`how`：连接方式；`on`：左表用于对齐的列名（默认用索引）；`lsuffix`/`rsuffix`：重复列名的后缀 | 合并后的新 DataFrame |
| `pd.concat()` | `pd.concat(objs, axis=0, join='outer', ignore_index=False, keys=None)` | `objs`：DataFrame 或 Series 的列表/字典；`axis`：拼接轴（0=行，1=列）；`join`：`'outer'`（并集）或 `'inner'`（交集）；`ignore_index`：是否重置索引；`keys`：用于分组标记的键 | 拼接后的新 DataFrame/Series |
| `DataFrame.append()`（已弃用） | 在 Pandas 1.4.0 后弃用，请使用 `pd.concat()` | — | — |

**原理说明**：`merge` 的核心是"键匹配"——通过比较键列的值来决定哪些行被连接在一起，`how` 参数控制匹配策略（内连接取交集、外连接取并集、左/右连接保留一侧全部行）。`join` 本质上是 `merge` 在索引上的特例，当 `on=None` 时按索引对齐。`concat` 不涉及键匹配，纯粹按轴方向堆叠，`join` 参数仅控制列（轴=0时）或行（轴=1时）的并集/交集取舍。

## 3. 代码示例

### 示例1：基础 merge —— 按共同列合并（内连接）

```python
import pandas as pd

# 创建两个 DataFrame
df_students = pd.DataFrame({
    '学号': ['S001', 'S002', 'S003', 'S004'],
    '姓名': ['张三', '李四', '王五', '赵六']
})

df_scores = pd.DataFrame({
    '学号': ['S001', 'S002', 'S004'],
    '成绩': [85, 92, 78]
})

# 内连接：只保留两边都有的学号
result = pd.merge(df_students, df_scores, on='学号', how='inner')
print(result)
# 输出：
#    学号  姓名  成绩
# 0  S001  张三   85
# 1  S002  李四   92
# 2  S004  赵六   78

# 左连接：保留左表全部行，右表无匹配则填 NaN
result_left = pd.merge(df_students, df_scores, on='学号', how='left')
print(result_left)
# 输出：
#    学号  姓名    成绩
# 0  S001  张三   85.0
# 1  S002  李四   92.0
# 2  S003  王五    NaN
# 3  S004  赵六   78.0
```

### 示例2：join 按索引合并 + concat 行拼接

```python
import pandas as pd

# 创建按索引对齐的数据
df_math = pd.DataFrame({'数学': [90, 85, 88]}, index=['A', 'B', 'C'])
df_english = pd.DataFrame({'英语': [80, 95, 70]}, index=['A', 'B', 'D'])

# join：默认按索引左连接
df_joined = df_math.join(df_english, how='outer')
print(df_joined)
# 输出：
#      数学    英语
# A  90.0   80.0
# B  85.0   95.0
# C  88.0    NaN
# D   NaN   70.0

# concat：行方向拼接（上下堆叠）
df_1 = pd.DataFrame({'科目': ['语文'], '分数': [88]})
df_2 = pd.DataFrame({'科目': ['数学'], '分数': [95]})
df_concat = pd.concat([df_1, df_2], axis=0, ignore_index=True)
print(df_concat)
# 输出：
#    科目  分数
# 0  语文   88
# 1  数学   95
```

### 示例3：进阶 —— 不同键列名合并 + concat 列拼接

```python
import pandas as pd

# 左右表键列名不同
df_orders = pd.DataFrame({
    '订单号': ['A001', 'A002', 'A003'],
    '客户ID': ['C1', 'C2', 'C3'],
    '金额': [100, 250, 180]
})

df_customers = pd.DataFrame({
    '客户编号': ['C1', 'C2', 'C3', 'C4'],
    '客户名': ['甲公司', '乙公司', '丙公司', '丁公司']
})

# 使用 left_on 和 right_on 指定不同的键列
merged = pd.merge(df_orders, df_customers, 
                  left_on='客户ID', right_on='客户编号', how='left')
print(merged)
# 输出：
#    订单号 客户ID  金额  客户编号  客户名
# 0  A001    C1  100     C1   甲公司
# 1  A002    C2  250     C2   乙公司
# 2  A003    C3  180     C3   丙公司

# concat 列方向拼接（左右并排）
df_sales_q1 = pd.DataFrame({'季度': ['Q1'], '销售额': [500]})
df_sales_q2 = pd.DataFrame({'季度': ['Q2'], '销售额': [650]})
df_sales = pd.concat([df_sales_q1, df_sales_q2], axis=1)
print(df_sales)
# 输出：
#   季度  销售额 季度  销售额
# 0  Q1    500  Q2    650
```

## 4. 常见错误

### 错误1：merge 时忘记指定 `on` 且两边没有共同列名

```python
import pandas as pd

df_a = pd.DataFrame({'ID': [1, 2], '值': [10, 20]})
df_b = pd.DataFrame({'编号': [1, 2], '备注': ['x', 'y']})

# 错误写法：会抛出 MergeError
# result = pd.merge(df_a, df_b)

# 正确写法：显式指定左右键列
result = pd.merge(df_a, df_b, left_on='ID', right_on='编号')
print(result)
# 输出：
#    ID  值  编号 备注
# 0   1  10    1   x
# 1   2  20    2   y
```

### 错误2：join 时两边索引有重复值导致笛卡尔积

```python
df_x = pd.DataFrame({'A': [1, 2]}, index=['K1', 'K1'])  # 索引重复
df_y = pd.DataFrame({'B': [3, 4]}, index=['K1', 'K2'])

# 错误写法：索引重复会导致意外的多行匹配
# result = df_x.join(df_y)  # 会产生 2x2=4 行

# 正确做法：先重置索引，用 merge 按列合并
df_x_reset = df_x.reset_index()
df_y_reset = df_y.reset_index()
result = pd.merge(df_x_reset, df_y_reset, on='index')
print(result)
# 输出：
#   index  A  B
# 0    K1  1  3
# 1    K1  2  4
```

### 错误3：concat 时索引不连续导致后续操作混乱

```python
df_p1 = pd.DataFrame({'成绩': [80, 90]}, index=[0, 1])
df_p2 = pd.DataFrame({'成绩': [70, 85]}, index=[0, 1])

# 错误写法：直接拼接后索引重复
# result = pd.concat([df_p1, df_p2])  # 索引为 0,1,0,1

# 正确写法：设置 ignore_index=True 重置索引
result = pd.concat([df_p1, df_p2], ignore_index=True)
print(result)
# 输出：
#    成绩
# 0   80
# 1   90
# 2   70
# 3   85
```

## 5. 练习

**练习1**：某公司有两个表：`员工表`（列：员工ID、姓名、部门）和 `工资表`（列：员工编号、月薪、奖金）。请写出代码，将两表按员工ID合并，要求保留所有员工（包括没有工资记录的），结果中重复列名用 `_员工` 和 `_工资` 区分。

<details>
<summary>答案提示</summary>

```python
result = pd.merge(员工表, 工资表, 
                  left_on='员工ID', right_on='员工编号', 
                  how='left', suffixes=('_员工', '_工资'))
```

</details>

**练习2**：有三个季度的销售数据 DataFrame（Q1、Q2、Q3），每个表有相同的列（月份、销售额）。请用 `pd.concat` 将它们拼接为一个总表，并重置索引。如果希望区分数据来自哪个季度，应该怎么做？

<details>
<summary>答案提示</summary>

```python
# 基础拼接
total = pd.concat([df_q1, df_q2, df_q3], ignore_index=True)

# 区分季度：使用 keys 参数
total_with_keys = pd.concat([df_q1, df_q2, df_q3], 
                            keys=['Q1', 'Q2', 'Q3'], 
                            ignore_index=False)
# 此时索引为 MultiIndex，第一层是季度标记
```

</details>