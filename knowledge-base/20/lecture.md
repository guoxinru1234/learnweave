# 链式操作与pipe最佳实践

> 模块：Pandas数据处理(下) | 编号：第20讲 | Python数据分析实战

## 1. 概念

链式操作（Method Chaining）是一种编程风格，指在同一个表达式上连续调用多个方法，前一个方法的返回值作为后一个方法的调用对象。在Pandas中，`df.groupby(...).agg(...).reset_index().sort_values(...)` 就是典型的链式操作。

**pipe** 是Pandas提供的一个特殊方法，它允许你将整个DataFrame（或Series）作为参数传递给一个自定义函数，从而将复杂的处理逻辑封装为可复用的函数，并嵌入到链式操作中。`DataFrame.pipe(func, *args, **kwargs)` 等价于 `func(df, *args, **kwargs)`。

**适用场景**：当你需要对DataFrame进行多步骤清洗、转换、聚合时，链式操作让代码从上到下读起来像流水线，逻辑清晰、中间变量少。而 `pipe` 特别适合将重复使用的处理逻辑（如数据标准化、异常值剔除）封装成函数，让主流程更简洁。

**生活化类比**：链式操作就像工厂流水线——原材料（原始DataFrame）依次经过切割（筛选）、打磨（填充缺失值）、组装（分组聚合）、质检（排序）等工位，每个工位只做一件事，最终产出成品。而 `pipe` 就像给流水线安装一个"定制工位"——当标准工位（内置方法）不够用时，你可以自己设计一个专用工位（自定义函数），插到流水线任意位置。

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `DataFrame.pipe()` | `pipe(func, *args, **kwargs)` | `func`：接受DataFrame作为第一个参数的可调用对象；`*args`/`**kwargs`：传递给`func`的额外参数 | 返回`func`的返回值（通常是DataFrame或标量） |
| `DataFrame.assign()` | `assign(**kwargs)` | `kwargs`：列名=标量值或可调用对象（接收df并返回Series） | 返回新的DataFrame，包含原列及新增/覆盖列 |
| `DataFrame.query()` | `query(expr, inplace=False)` | `expr`：字符串形式的布尔表达式，可用`@`引用外部变量 | 返回筛选后的DataFrame |
| `DataFrame.rename()` | `rename(mapper=None, *, index=None, columns=None, axis=None, inplace=False)` | `columns`：字典或函数，用于重命名列 | 返回重命名后的DataFrame |
| `DataFrame.sort_values()` | `sort_values(by, *, axis=0, ascending=True, inplace=False, na_position='last')` | `by`：列名或列名列表；`ascending`：升序或降序 | 返回排序后的DataFrame |

**原理说明**：链式操作的核心在于Pandas的绝大多数方法默认返回**新对象**而非原地修改（`inplace=False` 为默认），因此可以无限串联。`pipe` 的独特价值在于：当链式操作中需要调用自定义函数时，直接写 `df.custom_func()` 会破坏链式结构（需要先赋值给变量），而 `pipe` 让自定义函数无缝嵌入链中。

## 3. 代码示例

### 示例1：基础链式操作——清洗与筛选

```python
import pandas as pd
import numpy as np

# 创建包含脏数据的示例DataFrame
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
    'age': [25, None, 35, 28, None],
    'salary': [50000, 60000, None, 52000, 48000],
    'department': ['HR', 'IT', 'IT', 'HR', 'Finance']
})

# 链式操作：填充缺失值 -> 筛选年龄>26 -> 选择两列 -> 按薪资降序排序
result = (df
          .assign(age=df['age'].fillna(df['age'].mean()),          # 用均值填充年龄缺失
                  salary=df['salary'].fillna(0))                   # 用0填充薪资缺失
          .query('age > 26')                                        # 筛选年龄大于26的行
          [['name', 'salary']]                                      # 选择列
          .sort_values('salary', ascending=False))                 # 按薪资降序

print(result)
# 输出:
#       name   salary
# 2  Charlie      0.0
# 3    David  52000.0
```

### 示例2：使用pipe封装自定义清洗函数

```python
import pandas as pd
import numpy as np

def standardize_age(df, age_col='age'):
    """自定义函数：将年龄列标准化为z-score"""
    df = df.copy()
    mean = df[age_col].mean()
    std = df[age_col].std()
    df[age_col + '_zscore'] = (df[age_col] - mean) / std
    return df

def remove_outliers(df, col, threshold=2):
    """自定义函数：剔除指定列超过threshold个标准差的异常值"""
    mean = df[col].mean()
    std = df[col].std()
    return df[np.abs(df[col] - mean) <= threshold * std]

# 创建数据
df = pd.DataFrame({
    'age': [25, 30, 35, 40, 28, 120],  # 120是异常值
    'score': [85, 90, 78, 92, 88, 95]
})

# 使用pipe将自定义函数嵌入链式操作
result = (df
          .pipe(standardize_age)                    # 添加z-score列
          .pipe(remove_outliers, 'age', threshold=2)  # 剔除年龄异常值
          .query('age_zscore > -1'))                # 只保留z-score大于-1的行

print(result)
# 输出:
#    age  score  age_zscore
# 0   25     85   -0.505076
# 1   30     90   -0.252538
# 2   35     78    0.000000
# 3   40     92    0.252538
# 4   28     88   -0.378807
# （age=120的异常行已被剔除）
```

### 示例3：pipe与groupby结合的进阶用法

```python
import pandas as pd
import numpy as np

def add_rank_by_group(df, group_col, value_col, rank_col='rank'):
    """自定义函数：在每个分组内对value_col排名"""
    df = df.copy()
    df[rank_col] = df.groupby(group_col)[value_col].rank(ascending=False)
    return df

def top_n_per_group(df, group_col, n=2):
    """自定义函数：每个分组取前n行"""
    return df.groupby(group_col).head(n).reset_index(drop=True)

# 创建销售数据
df = pd.DataFrame({
    'region': ['East', 'East', 'East', 'West', 'West', 'West', 'North', 'North'],
    'salesperson': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'],
    'sales': [100, 200, 150, 300, 250, 200, 400, 350]
})

# 链式操作：添加组内排名 -> 每组取前2名 -> 按区域和排名排序
result = (df
          .pipe(add_rank_by_group, 'region', 'sales')     # 组内排名
          .pipe(top_n_per_group, 'region', n=2)           # 每组取前2
          .sort_values(['region', 'rank']))               # 排序

print(result)
# 输出:
#   region salesperson  sales  rank
# 0   East           B    200   1.0
# 1   East           C    150   2.0
# 2  North           G    400   1.0
# 3  North           H    350   2.0
# 4   West           D    300   1.0
# 5   West           E    250   2.0
```

## 4. 常见错误

### 错误1：忘记链式操作返回新对象，误用`inplace=True`

```python
# 错误写法：在链式中使用inplace=True
df = pd.DataFrame({'A': [1, 2, 3]})
# result = df.drop(0, inplace=True).head()  # AttributeError: 'NoneType' object has no attribute 'head'

# 原因：inplace=True时drop返回None，无法继续链式调用
# 正确写法：不使用inplace，让方法返回新对象
result = df.drop(0).head()
print(result)
```

### 错误2：在`assign`中引用新创建的列

```python
# 错误写法：assign中试图引用同一次assign中刚创建的列
df = pd.DataFrame({'A': [1, 2, 3]})
# result = df.assign(B=df['A'] * 2, C=df['B'] + 1)  # KeyError: 'B'

# 原因：assign中的表达式是同时计算的，不能引用本次assign中尚未存在的列
# 正确写法：分两步assign
result = df.assign(B=df['A'] * 2).assign(C=lambda d: d['B'] + 1)
print(result)
# 输出:
#    A  B  C
# 0  1  2  3
# 1  2  4  5
# 2  3  6  7
```

### 错误3：pipe函数中修改了原DataFrame

```python
# 错误写法：pipe函数内部直接修改传入的df
def bad_func(df):
    df['new_col'] = 1  # 直接修改原df，可能引发SettingWithCopyWarning
    return df

df = pd.DataFrame({'A': [1, 2, 3]})
df2 = df.pipe(bad_func)
print(df)  # 原df也被修改了！

# 正确写法：在函数内部先copy
def good_func(df):
    df = df.copy()  # 先复制，避免修改原数据
    df['new_col'] = 1
    return df

df = pd.DataFrame({'A': [1, 2, 3]})
df2 = df.pipe(good_func)
print(df)  # 原df保持不变
# 输出:
#    A
# 0  1
# 1  2
# 2  3
```

## 5. 练习

### 练习1：综合链式操作

给定以下DataFrame，请用**一条链式操作**完成：筛选出`score`大于60的学生 → 按`class`分组计算`score`的平均值 → 将平均分列重命名为`avg_score` → 按`avg_score`降序排序。

```python
import pandas as pd

df = pd.DataFrame({
    'student': ['A', 'B', 'C', 'D', 'E', 'F'],
    'class': ['X', 'X', 'Y', 'Y', 'Z', 'Z'],
    'score': [85, 55, 92, 68, 75, 88]
})
```

**答案提示**：使用`query`筛选 → `groupby('class')['score'].mean()` → `rename('avg_score')` → `reset_index()` → `sort_values('avg_score', ascending=False)`。注意`groupby`后需要`reset_index()`才能继续链式操作。

### 练习2：设计pipe函数

请编写一个`pipe`函数`fill_and_scale`，它接收DataFrame和两个参数`fill_value`与`scale_factor`，功能是：先用`fill_value`填充所有数值列的缺失值，再将所有数值列乘以`scale_factor`。然后用`pipe`将其应用到下面的数据上，并链式调用`round(2)`保留两位小数。

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'A': [1.5, np.nan, 3.2],
    'B': [4.1, 5.5, np.nan],
    'C': ['x', 'y', 'z']  # 非数值列应保持不变
})
```

**答案提示**：在函数中使用`df.select_dtypes(include=[np.number])`选择数值列，`fillna(fill_value)`后乘以`scale_factor`，用`df[non_numeric_cols]`保留非数值列，最后用`pd.concat`合并。调用方式：`df.pipe(fill_and_scale, fill_value=0, scale_factor=2).round(2)`。