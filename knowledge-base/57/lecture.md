# 内存优化与数据类型选择

> 模块：性能优化与部署 | 编号：第57讲 | Python数据分析实战

---

## 1. 概念

内存优化与数据类型选择，是指在数据分析流程中，通过合理选择数据存储结构（如 Pandas 的 `dtype`）和数据处理方式，来降低数据在内存中的占用空间，从而提升计算速度、降低硬件成本，并避免因内存不足导致的程序崩溃。

在 Pandas 中，每一列数据都有对应的数据类型（`dtype`），例如 `int64`、`float64`、`object` 等。默认情况下，Pandas 会以较为宽泛的类型（如 `int64`、`float64`）存储数据，这在数据量较小时无伤大雅，但当数据量达到数百万行甚至更多时，内存占用会急剧膨胀，导致性能下降。

**生活化类比**：想象你有一个大型仓库（内存），里面存放着许多箱子（数据）。每个箱子都按最大尺寸（`int64`/`float64`）定制，即使里面只装一个小物件（如 0 或 1），也占用同样的空间。内存优化的思路，就是根据实际物品大小，换用更合适的箱子（如 `int8`、`float32`），从而在同样的仓库面积里存放更多货物。

**适用场景**：处理大规模数据集（如日志数据、传感器数据）、内存受限的服务器环境、需要反复迭代计算的机器学习任务。

---

## 2. 核心API与原理

| API / 方法 | 签名 | 参数说明 | 返回值 | 原理简述 |
|------------|------|----------|--------|----------|
| `pd.DataFrame.astype()` | `df.astype(dtype, copy=True)` | `dtype`: 目标类型（如 `'int8'`、`'float32'`）；`copy`: 是否复制数据 | 返回转换后的新 DataFrame | 将指定列转换为更紧凑的数据类型，减少内存占用 |
| `pd.to_numeric()` | `pd.to_numeric(arg, errors='raise', downcast=None)` | `arg`: Series 或数组；`errors`: 错误处理方式（`'raise'`/`'coerce'`/`'ignore'`）；`downcast`: 向下转换类型（如 `'integer'`、`'float'`） | 返回转换后的 Series | 将字符串或对象类型转换为数值类型，并支持自动降级 |
| `pd.DataFrame.info()` | `df.info(verbose=True, memory_usage=True)` | `verbose`: 是否显示全部列；`memory_usage`: 是否显示内存使用情况 | 无（打印信息到控制台） | 显示每列 dtype 及总内存占用，用于诊断 |
| `pd.DataFrame.memory_usage()` | `df.memory_usage(index=True, deep=False)` | `index`: 是否包含索引；`deep`: 是否深入计算 object 列的实际内存 | 返回 Series，每列内存字节数 | 精确计算每列占用内存，`deep=True` 时对 `object` 列逐元素计算 |
| `pd.api.types.CategoricalDtype()` | `pd.CategoricalDtype(categories=None, ordered=False)` | `categories`: 类别列表；`ordered`: 是否有序 | 返回 CategoricalDtype 对象 | 将重复度高的字符串列转为类别类型，大幅节省内存 |

---

## 3. 代码示例

### 示例 1：基础——查看内存占用并转换数值类型

```python
import pandas as pd
import numpy as np

# 创建一个包含 100 万行的 DataFrame
n = 1_000_000
df = pd.DataFrame({
    'id': np.arange(n),                     # 默认 int64
    'score': np.random.randn(n),            # 默认 float64
    'age': np.random.randint(18, 80, n)     # 默认 int64
})

print("=== 转换前内存占用 ===")
print(df.info(memory_usage='deep'))
# 输出示例:
# <class 'pandas.core.frame.DataFrame'>
# RangeIndex: 1000000 entries, 0 to 999999
# Data columns (total 3 columns):
#  #   Column  Non-Null Count  Dtype  
# ---  ------  --------------  -----  
#  0   id      1000000 non-null  int64  
#  1   score   1000000 non-null  float64
#  2   age     1000000 non-null  int64  
# dtypes: float64(1), int64(2)
# memory usage: 24.0 MB

# 转换数据类型：id 和 age 用 int32，score 用 float32
df['id'] = df['id'].astype('int32')
df['age'] = df['age'].astype('int8')       # 年龄范围 18-80，int8 足够
df['score'] = df['score'].astype('float32')

print("\n=== 转换后内存占用 ===")
print(df.info(memory_usage='deep'))
# 输出示例:
# memory usage: 12.0 MB
# 内存占用从 24MB 降至 12MB，减少 50%
```

### 示例 2：进阶——使用 `pd.to_numeric` 与 `downcast` 自动优化

```python
import pandas as pd

# 模拟从 CSV 读取的数据，所有列都是字符串类型
data = {
    'user_id': ['1001', '1002', '1003', '1004'],
    'revenue': ['12.5', '99.9', '45.0', '78.2'],
    'visits': ['3', '15', '7', '22']
}
df = pd.DataFrame(data)

print("=== 原始类型 ===")
print(df.dtypes)
# 输出:
# user_id    object
# revenue    object
# visits     object
# dtype: object

# 使用 to_numeric 批量转换，并自动向下转型
df['user_id'] = pd.to_numeric(df['user_id'], downcast='integer')
df['revenue'] = pd.to_numeric(df['revenue'], downcast='float')
df['visits'] = pd.to_numeric(df['visits'], downcast='integer')

print("\n=== 转换后类型 ===")
print(df.dtypes)
# 输出:
# user_id    int16
# revenue    float32
# visits     int8
# dtype: object

print("\n=== 转换后数据 ===")
print(df)
# 输出:
#    user_id  revenue  visits
# 0     1001     12.5       3
# 1     1002     99.9      15
# 2     1003     45.0       7
# 3     1004     78.2      22
```

### 示例 3：进阶——使用 `CategoricalDtype` 优化高重复字符串列

```python
import pandas as pd
import numpy as np

# 创建包含高重复城市名的 DataFrame
n = 500_000
cities = ['北京', '上海', '广州', '深圳', '杭州']
df = pd.DataFrame({
    'city': np.random.choice(cities, n),
    'value': np.random.randn(n)
})

print("=== 转换前内存占用 ===")
print(df.memory_usage(deep=True))
# 输出:
# Index         128
# city     30000000   # 每个字符串约 60 字节
# value     4000000
# dtype: int64

# 转换为 Categorical 类型
df['city'] = df['city'].astype('category')

print("\n=== 转换后内存占用 ===")
print(df.memory_usage(deep=True))
# 输出:
# Index      128
# city     500040     # 大幅下降，仅存储类别编码
# value    4000000
# dtype: int64

# 查看类别信息
print("\n=== 类别信息 ===")
print(df['city'].cat.categories)
# 输出:
# Index(['上海', '北京', '广州', '杭州', '深圳'], dtype='object')
```

---

## 4. 常见错误

### 错误 1：盲目将所有列转换为 `category` 类型

**错误原因**：`category` 类型适合**重复度高**的列（如性别、国家代码）。如果列中每个值都几乎唯一（如用户 ID、时间戳），转换为 `category` 不仅不会节省内存，反而会因维护类别映射而增加开销。

```python
# 错误写法
df = pd.DataFrame({'unique_id': range(1_000_000)})
df['unique_id'] = df['unique_id'].astype('category')  # 内存反而增大

# 正确写法
# 先检查唯一值比例
unique_ratio = df['unique_id'].nunique() / len(df)
# 若 unique_ratio > 0.5，则不适合用 category
df['unique_id'] = df['unique_id'].astype('int32')  # 用更窄的数值类型
```

### 错误 2：使用 `astype` 时忽略数据范围导致溢出

**错误原因**：`int8` 的范围是 -128 到 127。如果数据中存在超出范围的值，转换会抛出 `OverflowError` 或产生错误结果。

```python
# 错误写法
s = pd.Series([100, 200, 300])
s.astype('int8')
# 报错: OverflowError: Python int too large to convert to C long

# 正确写法
# 先检查数据的 min 和 max
print(s.min(), s.max())  # 100 300
# 选择足够大的类型
s.astype('int16')  # 范围 -32768 到 32767，安全
```

### 错误 3：忽略 `object` 列中的混合类型

**错误原因**：`object` 列可能包含数字、字符串、`None` 等混合类型。直接使用 `astype('float')` 会抛出 `ValueError`。

```python
# 错误写法
s = pd.Series(['1.5', '2.0', None, 'abc'])
s.astype('float')
# 报错: ValueError: could not convert string to float: 'abc'

# 正确写法
# 使用 to_numeric 并指定 errors='coerce'，将无法转换的值设为 NaN
s = pd.to_numeric(s, errors='coerce')
print(s)
# 输出:
# 0    1.5
# 1    2.0
# 2    NaN
# 3    NaN
# dtype: float64
```

---

## 5. 练习

### 练习 1：动手题——优化一个真实数据集的内存占用

**题目**：给定一个包含 200 万行、5 列的数据集（列分别为：`user_id`（整数）、`age`（整数 0-100）、`salary`（浮点数）、`city`（字符串，10 个城市循环）、`signup_date`（日期字符串 `'2023-01-15'` 格式））。请编写代码完成以下优化：
1. 将所有整数列转换为最窄的安全类型；
2. 将 `salary` 转换为 `float32`；
3. 将 `city` 转换为 `category` 类型；
4. 将 `signup_date` 转换为 `datetime64` 类型；
5. 使用 `memory_usage(deep=True)` 对比优化前后的内存差异。

**答案提示**：
```python
# 伪代码思路（完整代码请自行实现）
# 1. 生成模拟数据
# 2. 用 .info() 查看初始内存
# 3. 对整数列检查 min/max 后选择 int8/int16/int32
# 4. df['salary'] = df['salary'].astype('float32')
# 5. df['city'] = df['city'].astype('category')
# 6. df['signup_date'] = pd.to_datetime(df['signup_date'])
# 7. 再次用 .info() 对比
```

### 练习 2：思考题——内存优化与性能的权衡

**题目**：在什么情况下，内存优化反而会导致性能下降？请结合 `category` 类型和 `float32` 类型各举一个例子，并说明如何权衡。

**答案提示**：
- **`category` 类型**：当类别数量非常多（如接近行数）时，每次分组或筛选操作都需要在类别编码和实际值之间转换，增加 CPU 开销。此时应改用原始字符串或数值类型。
- **`float32` 类型**：在某些需要高精度的计算（如金融计算、科学计算）中，`float32` 的精度损失（约 7 位有效数字）可能导致结果偏差。此时应保留 `float64`，或仅在中间计算时降精度、输出时恢复。
- **权衡原则**：内存优化应优先用于**存储型操作**（如保存到磁盘、缓存），而在**计算密集型操作**中，应优先保证精度和速度，必要时在计算前后临时转换类型。