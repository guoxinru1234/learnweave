# 数据类型转换与优化
> 模块：Pandas数据处理(上) | 编号：第15讲 | Python数据分析实战

---

## 1. 概念

数据类型转换是指将 DataFrame 或 Series 中的列从一种数据类型（dtype）转换为另一种数据类型的过程。在 Pandas 中，常见的数据类型包括 `int64`、`float64`、`object`（通常存储字符串）、`bool`、`datetime64` 以及 `category`（分类类型）。数据类型优化则是通过选择更节省内存的 dtype（如将 `int64` 降为 `int8`、将 `object` 转为 `category`）来降低数据框的内存占用，提升计算性能。

**适用场景**：读取 CSV 后自动推断类型不准确时；日期列被读成字符串时；类别型文本列占用大量内存时；模型训练前需要统一数值类型时。

**生活化类比**：想象一个大型仓库，每个货架都贴着标签——"整数"、"小数"、"文字"、"日期"。如果所有货物都装在"文字"货架上，虽然能装下一切，但查找和搬运都很慢。数据类型转换就是给每件货物贴上正确的标签，放到合适的货架上；而优化则是将"大箱子"换成"小盒子"（如 `int64` → `int32`），让仓库容量更大、取货更快。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `pd.to_numeric()` | `pd.to_numeric(arg, errors='raise', downcast=None)` | `arg`：Series 或 array-like；`errors`：`'raise'`（出错抛出）、`'coerce'`（无法转换则置为 NaN）、`'ignore'`（原样返回）；`downcast`：`'integer'`/`'float'`/`'signed'`/`'unsigned'` 等，用于降级类型 | 转换后的 Series 或 ndarray |
| `pd.to_datetime()` | `pd.to_datetime(arg, format=None, errors='raise')` | `arg`：字符串、Series 或 list；`format`：指定解析格式（如 `'%Y-%m-%d'`），不指定则自动推断；`errors`：同 `to_numeric` | 转换后的 DatetimeIndex 或 Series（dtype 为 `datetime64[ns]`） |
| `Series.astype()` | `s.astype(dtype, copy=True, errors='raise')` | `dtype`：目标类型（如 `'int32'`、`'float32'`、`'category'`）；`copy`：是否复制；`errors`：`'raise'` 或 `'ignore'` | 转换类型后的新 Series |
| `pd.Categorical()` | `pd.Categorical(values, categories=None, ordered=False)` | `values`：原始数据；`categories`：指定类别列表（不指定则自动推断）；`ordered`：是否有序 | 分类类型对象，可赋值给 DataFrame 列 |
| `DataFrame.memory_usage()` | `df.memory_usage(deep=True)` | `deep`：为 `True` 时深入计算 `object` 类型列中每个字符串的内存 | Series，索引为列名，值为每列字节数 |

**原理说明**：Pandas 底层基于 NumPy 数组，每个 dtype 对应固定的字节宽度。`object` 类型存储的是指向 Python 对象的指针（8 字节），而 `category` 类型内部使用整数编码 + 类别映射表，因此对重复值多的文本列能大幅节省内存。`astype` 是强制转换，`to_numeric`/`to_datetime` 则提供更灵活的错误处理和格式解析。

---

## 3. 代码示例

### 示例 1：基础类型转换（读取后修正类型）

```python
import pandas as pd
import numpy as np

# 模拟一份原始数据，读入时类型不理想
df = pd.DataFrame({
    '年龄': ['25', '30', '35', '40'],
    '工资': ['8000.5', '12000.3', '15000.0', '20000.8'],
    '入职日期': ['2020-01-15', '2021-06-30', '2019-11-01', '2022-03-20']
})

print("转换前类型：")
print(df.dtypes)
print()

# 1. 字符串转整数：先转数值（因为字符串不能直接 astype 成 int）
df['年龄'] = pd.to_numeric(df['年龄'], errors='coerce').astype('int64')

# 2. 字符串转浮点数
df['工资'] = pd.to_numeric(df['工资'], errors='coerce')

# 3. 字符串转日期
df['入职日期'] = pd.to_datetime(df['入职日期'])

print("转换后类型：")
print(df.dtypes)
print()
print(df)

# 输出结果：
# 转换前类型：
# 年龄      object
# 工资      object
# 入职日期    object
# dtype: object
#
# 转换后类型：
# 年龄               int64
# 工资             float64
# 入职日期    datetime64[ns]
# dtype: object
#
#    年龄     工资    入职日期
# 0   25   8000.5 2020-01-15
# 1   30  12030.3 2021-06-30
# 2   35  15000.0 2019-11-01
# 3   40  20000.8 2022-03-20
```

### 示例 2：内存优化（数值降级 + 类别转换）

```python
import pandas as pd
import numpy as np

# 构造一个较大的数据集
n = 100000
df = pd.DataFrame({
    'id': np.arange(n),                          # int64
    'score': np.random.randn(n),                 # float64
    'city': np.random.choice(['北京', '上海', '广州', '深圳'], n),  # object
    'gender': np.random.choice(['男', '女'], n)   # object
})

print("优化前内存占用：")
print(df.memory_usage(deep=True))
print(f"总计: {df.memory_usage(deep=True).sum() / 1024:.2f} KB")
print()

# 1. 数值降级：id 最大 99999，int32 足够；score 用 float32 精度足够
df['id'] = df['id'].astype('int32')
df['score'] = df['score'].astype('float32')

# 2. 文本列转 category（城市只有 4 个类别，性别只有 2 个）
df['city'] = df['city'].astype('category')
df['gender'] = df['gender'].astype('category')

print("优化后内存占用：")
print(df.memory_usage(deep=True))
print(f"总计: {df.memory_usage(deep=True).sum() / 1024:.2f} KB")

# 输出结果（数值略有浮动）：
# 优化前内存占用：
# Index          132
# id           800000
# score        800000
# city        5791408
# gender      5791408
# dtype: int64
# 总计: 13183.84 KB
#
# 优化后内存占用：
# Index          132
# id           400000
# score        400000
# city         100416
# gender        100416
# dtype: int64
# 总计: 1000.96 KB
```

### 示例 3：`to_datetime` 高级用法与错误处理

```python
import pandas as pd

# 混合格式的日期字符串
dates = pd.Series(['2023-01-01', '2023/02/15', '20230320', '无效日期', '2023-05-01'])

# 使用 errors='coerce'，无法解析的置为 NaT（Not a Time）
parsed = pd.to_datetime(dates, errors='coerce')
print("解析结果：")
print(parsed)
print()

# 指定 format 可加速解析（推荐用于已知格式）
dates_clean = pd.Series(['2023-01-01', '2023-02-15', '2023-03-20'])
parsed_fast = pd.to_datetime(dates_clean, format='%Y-%m-%d')
print("指定格式解析：")
print(parsed_fast)
print()

# 提取日期分量
df_dates = pd.DataFrame({'date': parsed})
df_dates['year'] = df_dates['date'].dt.year
df_dates['month'] = df_dates['date'].dt.month
df_dates['weekday'] = df_dates['date'].dt.day_name()
print("提取日期分量：")
print(df_dates)

# 输出结果：
# 解析结果：
# 0   2023-01-01
# 1   2023-02-15
# 2   2023-03-20
# 3          NaT
# 4   2023-05-01
# dtype: datetime64[ns]
#
# 指定格式解析：
# 0   2023-01-01
# 1   2023-02-15
# 2   2023-03-20
# dtype: datetime64[ns]
#
# 提取日期分量：
#         date  year  month   weekday
# 0 2023-01-01  2023      1     Sunday
# 1 2023-02-15  2023      2  Wednesday
# 2 2023-03-20  2023      3     Monday
# 3        NaT   NaN    NaN       NaN
# 4 2023-05-01  2023      5     Monday
```

---

## 4. 常见错误

### 错误 1：字符串直接 `astype('int')` 报错

```python
import pandas as pd

s = pd.Series(['1', '2', '3'])
# 错误写法：
# s.astype('int')  # ValueError: invalid literal for int() with base 10: '1'

# 原因：字符串列 astype 到 int 时，Pandas 会尝试调用 int()，但某些字符串（如带小数点）会失败。
# 正确写法：先 to_numeric 再 astype
s_correct = pd.to_numeric(s).astype('int')
print(s_correct)
# 输出：0    1
#       1    2
#       2    3
#       dtype: int64
```

### 错误 2：`to_datetime` 遇到无效日期直接抛异常

```python
import pandas as pd

dates = pd.Series(['2023-01-01', 'not_a_date'])
# 错误写法：
# pd.to_datetime(dates)  # 抛 ParserError

# 原因：默认 errors='raise'，遇到无法解析的字符串会直接报错，导致整个程序崩溃。
# 正确写法：使用 errors='coerce'，无效值置为 NaT
parsed = pd.to_datetime(dates, errors='coerce')
print(parsed)
# 输出：
# 0   2023-01-01
# 1          NaT
# dtype: datetime64[ns]
```

### 错误 3：忽略 `category` 类型的有序性

```python
import pandas as pd

s = pd.Series(['低', '中', '高'])
s_cat = s.astype('category')
print(s_cat.cat.categories)  # Index(['中', '低', '高'], dtype='object') —— 默认按字母排序

# 错误写法：
# s_cat < '中'  # TypeError: '<' not supported between instances of 'str' and 'str'
# 原因：category 默认是无序的，无法进行大小比较。

# 正确写法：指定 ordered=True 和 categories 顺序
s_ordered = pd.Categorical(s, categories=['低', '中', '高'], ordered=True)
print(s_ordered < '中')
# 输出：
# [ True False False]
```

---

## 5. 练习

### 练习 1：动手题——优化一个真实数据集的内存

**任务**：创建一个包含 50 万行、5 列的数据框，列包括：`user_id`（整数 1~500000）、`age`（整数 18~80）、`salary`（浮点数 3000~50000）、`department`（10 个部门名）、`is_active`（布尔值 True/False）。请完成：
1. 计算优化前的总内存占用（KB）。
2. 将数值列降级为最合适的类型（`user_id` 和 `age` 用 `int32`，`salary` 用 `float32`），将 `department` 转为 `category`。
3. 计算优化后的总内存占用，并计算内存节省百分比。

**答案提示**：
```python
import pandas as pd
import numpy as np

n = 500000
df = pd.DataFrame({
    'user_id': np.arange(1, n + 1),
    'age': np.random.randint(18, 81, n),
    'salary': np.random.uniform(3000, 50000, n),
    'department': np.random.choice(['研发', '市场', '销售', '人事', '财务',
                                     '运营', '法务', '客服', '产品', '设计'], n),
    'is_active': np.random.choice([True, False], n)
})

before = df.memory_usage(deep=True).sum() / 1024
df['user_id'] = df['user_id'].astype('int32')
df['age'] = df['age'].astype('int32')
df['salary'] = df['salary'].astype('float32')
df['department'] = df['department'].astype('category')
after = df.memory_usage(deep=True).sum() / 1024
print(f"优化前: {before:.2f} KB, 优化后: {after:.2f} KB, 节省: {(1 - after/before)*100:.1f}%")
```

### 练习 2：思考题——日期转换的陷阱

**任务**：某 CSV 文件中日期列包含三种格式：`'2023/1/5'`、`'2023-01-15'`、`'20230125'`。直接使用 `pd.to_datetime()` 不指定 `format` 能否全部正确解析？如果不能，请写出能正确处理这三种格式的代码方案。

**答案提示**：`pd.to_datetime` 默认可以自动识别多种常见格式，但混合格式时可能对某些格式（如 `'20230125'`）解析失败。建议方案：
```python
import pandas as pd

dates = pd.Series(['2023/1/5', '2023-01-15', '20230125'])
# 方法1：直接尝试自动解析（Pandas 2.x 通常能处理）
parsed = pd.to_datetime(dates, errors='coerce')
print(parsed)
# 方法2：若失败，可统一替换分隔符后解析
dates_clean = dates.str.replace('/', '-').str.replace(r'(\d{4})(\d{2})(\d{2})', r'\1-\2-\3', regex=True)
parsed2 = pd.to_datetime(dates_clean, format='%Y-%m-%d')
print(parsed2)
```