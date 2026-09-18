# 数据选择loc/iloc/query

> 模块：Pandas数据处理(上) | 编号：第13讲 | Python数据分析实战

---

## 1. 概念

在 Pandas 中，**数据选择** 是指从 DataFrame 或 Series 中按行、列或条件提取子集的操作。`loc`、`iloc` 和 `query` 是三种最核心的索引器（Indexer），它们分别基于 **标签（label）**、**整数位置（integer position）** 和 **表达式（expression）** 进行数据筛选。

- **`loc`**：基于行/列标签（索引名）进行选择，支持切片（含终点）、布尔数组和可调用函数。
- **`iloc`**：基于整数位置（从 0 开始）进行选择，支持切片（不含终点）、整数列表和布尔数组。
- **`query`**：使用字符串表达式（类似 SQL 的 WHERE 子句）对 DataFrame 进行筛选，语法简洁，适合复杂条件组合。

**生活化类比**：把 DataFrame 想象成一本纸质通讯录。`loc` 就像按姓名（标签）查找联系人；`iloc` 就像按页码和行号（位置）翻找；`query` 则像用一句自然语言描述条件（如"找出所有住在北京且年龄大于30岁的人"）来筛选。

**适用场景**：数据清洗时按条件剔除异常值、特征工程中提取特定样本、数据可视化前按分组切片等。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `DataFrame.loc[]` | `df.loc[row_selector, col_selector]` | `row_selector`: 标签、标签列表、切片（含终点）、布尔Series/数组、可调用函数；`col_selector`: 同上（列标签） | 新的 DataFrame/Series（视图或副本，取决于操作） |
| `DataFrame.iloc[]` | `df.iloc[row_selector, col_selector]` | `row_selector`: 整数、整数列表、切片（不含终点）、布尔Series/数组；`col_selector`: 同上（整数位置） | 新的 DataFrame/Series |
| `DataFrame.query()` | `df.query(expr, inplace=False)` | `expr`: 字符串表达式，可用列名、比较运算符、逻辑运算符（`&`、`\|`、`~`）、变量（用 `@` 前缀引用外部变量）；`inplace`: 是否原地修改 | 筛选后的 DataFrame（若 `inplace=True` 则返回 `None`） |
| `Series.loc[]` / `Series.iloc[]` | `s.loc[selector]` / `s.iloc[selector]` | 与 DataFrame 类似，但仅支持行选择 | 新的 Series 或标量 |

**原理说明**：
- `loc` 和 `iloc` 都是 Pandas 的索引器（`_LocIndexer` / `_iLocIndexer`），它们重写了 `__getitem__` 方法，支持多维选择。
- `query` 底层使用 `numexpr` 库（若已安装）加速计算，否则回退到 Python 求值器。它只能用于列名比较，不能引用索引名（除非先 `reset_index()`）。
- 布尔数组选择时，数组长度必须与轴长度一致，否则会引发 `IndexingError`。

---

## 3. 代码示例

### 示例1：基础选择——loc与iloc的对比

```python
import pandas as pd

# 创建示例数据
df = pd.DataFrame(
    {'姓名': ['张三', '李四', '王五', '赵六'],
     '年龄': [25, 30, 35, 40],
     '城市': ['北京', '上海', '广州', '深圳']},
    index=['a', 'b', 'c', 'd']  # 自定义索引
)
print("原始数据：")
print(df)

# 使用 loc 按标签选择：取 'b' 到 'c' 行，'姓名' 和 '年龄' 列
result_loc = df.loc['b':'c', ['姓名', '年龄']]
print("\nloc 选择结果（标签切片含终点）：")
print(result_loc)

# 使用 iloc 按位置选择：取第 1 行到第 2 行（不含第 3 行），第 0 列和第 2 列
result_iloc = df.iloc[1:3, [0, 2]]
print("\niloc 选择结果（位置切片不含终点）：")
print(result_iloc)

# 输出结果：
# 原始数据：
#    姓名  年龄  城市
# a  张三   25   北京
# b  李四   30   上海
# c  王五   35   广州
# d  赵六   40   深圳
#
# loc 选择结果（标签切片含终点）：
#    姓名  年龄
# b  李四   30
# c  王五   35
#
# iloc 选择结果（位置切片不含终点）：
#    姓名  城市
# 1  李四   上海
# 2  王五   广州
```

### 示例2：条件筛选——query与布尔索引

```python
import pandas as pd

# 创建销售数据
sales = pd.DataFrame({
    '产品': ['A', 'B', 'C', 'D', 'E'],
    '销量': [120, 85, 200, 150, 90],
    '单价': [10, 20, 15, 30, 25],
    '地区': ['华东', '华北', '华东', '华南', '华北']
})

# 使用 query 筛选：销量大于100 且 单价小于等于20
filtered = sales.query('销量 > 100 & 单价 <= 20')
print("query 筛选结果（销量>100 且 单价<=20）：")
print(filtered)

# 使用外部变量（需加 @ 前缀）
min_sales = 100
filtered2 = sales.query('销量 >= @min_sales & 地区 == "华东"')
print("\nquery 使用外部变量筛选（销量>=100 且 地区=华东）：")
print(filtered2)

# 等价写法：用 loc + 布尔Series
mask = (sales['销量'] > 100) & (sales['单价'] <= 20)
filtered3 = sales.loc[mask]
print("\nloc + 布尔索引等价结果：")
print(filtered3)

# 输出结果：
# query 筛选结果（销量>100 且 单价<=20）：
#   产品  销量  单价  地区
# 0   A  120   10  华东
# 2   C  200   15  华东
#
# query 使用外部变量筛选（销量>=100 且 地区=华东）：
#   产品  销量  单价  地区
# 0   A  120   10  华东
# 2   C  200   15  华东
#
# loc + 布尔索引等价结果：
#   产品  销量  单价  地区
# 0   A  120   10  华东
# 2   C  200   15  华东
```

### 示例3：进阶用法——组合选择与函数

```python
import pandas as pd
import numpy as np

# 生成随机数据
np.random.seed(42)
df = pd.DataFrame(
    np.random.randint(0, 100, size=(6, 4)),
    columns=['A', 'B', 'C', 'D'],
    index=pd.date_range('2024-01-01', periods=6)
)
print("随机数据：")
print(df)

# 1. loc 配合可调用函数：选择所有 A 列大于中位数的行
df_selected = df.loc[lambda x: x['A'] > x['A'].median(), :]
print("\nloc 配合 lambda 筛选 A 列大于中位数的行：")
print(df_selected)

# 2. iloc 配合布尔数组：选择 B 列大于 50 的行（布尔数组长度需一致）
bool_arr = df['B'] > 50
df_bool = df.iloc[bool_arr.values, :]  # 注意 iloc 需要 numpy 数组
print("\niloc 配合布尔数组筛选 B 列大于 50 的行：")
print(df_bool)

# 3. query 中引用列计算（注意：query 不支持所有 Pandas 函数，但支持算术运算）
df['总额'] = df['A'] * df['B']  # 先创建新列
df_query = df.query('总额 > 2000')
print("\nquery 筛选总额大于 2000 的行：")
print(df_query)

# 输出结果（部分）：
# 随机数据：
#              A   B   C   D
# 2024-01-01  52  93  15  72
# 2024-01-02  61  21  83  87
# 2024-01-03  75  48  75  12
# 2024-01-04  22  15  55  51
# 2024-01-05  14  77  76  32
# 2024-01-06  91  21  49  55
#
# loc 配合 lambda 筛选 A 列大于中位数的行：
#              A   B   C   D
# 2024-01-01  52  93  15  72
# 2024-01-02  61  21  83  87
# 2024-01-03  75  48  75  12
# 2024-01-06  91  21  49  55
```

---

## 4. 常见错误

### 错误1：混淆 loc 和 iloc 的切片边界

**错误示例**：
```python
df = pd.DataFrame({'A': [1, 2, 3]}, index=['x', 'y', 'z'])
# 错误：使用 iloc 却用了标签切片
result = df.iloc['x':'y']  # TypeError: cannot do slice indexing on <class 'pandas.core.indexes.base.Index'> with these indexers [x] of <class 'str'>
```

**错误原因**：`iloc` 只接受整数位置，不接受标签。`loc` 的切片包含终点，而 `iloc` 的切片不包含终点。

**正确写法**：
```python
# 使用 iloc 按位置切片（不含终点）
result = df.iloc[0:2]   # 取第 0、1 行
# 使用 loc 按标签切片（含终点）
result = df.loc['x':'y']  # 取 'x' 和 'y' 行
```

---

### 错误2：query 中引用外部变量时忘记加 @ 前缀

**错误示例**：
```python
threshold = 50
df = pd.DataFrame({'A': [10, 60, 30]})
# 错误：直接使用变量名
result = df.query('A > threshold')  # NameError: name 'threshold' is not defined
```

**错误原因**：`query` 的表达式在独立命名空间中求值，无法直接访问外部 Python 变量。

**正确写法**：
```python
result = df.query('A > @threshold')  # 加 @ 前缀引用外部变量
print(result)  # 输出 A 列大于 50 的行
```

---

### 错误3：布尔数组长度与 DataFrame 行数不匹配

**错误示例**：
```python
df = pd.DataFrame({'A': [1, 2, 3, 4]})
mask = [True, False, True]  # 长度只有 3
# 错误：布尔数组长度不一致
result = df.loc[mask]  # IndexingError: Unalignable boolean Series provided as indexer
```

**错误原因**：布尔索引要求数组长度与轴长度完全一致（此处应为 4）。

**正确写法**：
```python
mask = [True, False, True, False]  # 长度与行数一致
result = df.loc[mask]
print(result)  # 输出第 0、2 行
# 或者使用条件表达式生成布尔 Series
mask = df['A'] > 2
result = df.loc[mask]
```

---

## 5. 练习

### 练习1：综合筛选（动手题）

给定以下 `df`，请用 `query` 筛选出 **"华东" 地区、销量大于 100 且单价小于 20** 的记录；再用 `iloc` 取出该结果的前 2 行。

```python
import pandas as pd
df = pd.DataFrame({
    '产品': ['A', 'B', 'C', 'D', 'E', 'F'],
    '销量': [120, 85, 200, 150, 90, 110],
    '单价': [10, 20, 15, 30, 25, 18],
    '地区': ['华东', '华北', '华东', '华南', '华北', '华东']
})
```

**答案提示**：
```python
# 第一步：query 筛选
filtered = df.query('地区 == "华东" & 销量 > 100 & 单价 < 20')
# 第二步：iloc 取前 2 行
result = filtered.iloc[:2, :]
print(result)
# 输出应为：产品 A 和 C 的记录
```

---

### 练习2：思考题——loc 与 iloc 的边界行为

创建一个 5 行 3 列的 DataFrame，索引为 `['a','b','c','d','e']`。请回答：
1. `df.loc['b':'d']` 会返回几行？`df.iloc[1:4]` 呢？两者结果是否相同？
2. 如果使用 `df.loc[['a','c']]` 和 `df.iloc[[0,2]]`，结果是否一致？为什么？

**答案提示**：
1. `df.loc['b':'d']` 返回 3 行（b、c、d），因为 `loc` 切片含终点；`df.iloc[1:4]` 也返回 3 行（位置 1、2、3），结果相同。两者行为一致。
2. 结果一致。`df.loc[['a','c']]` 按标签选择第 0 和第 2 行；`df.iloc[[0,2]]` 按位置选择第 0 和第 2 行。只要标签顺序与位置顺序一致，结果就相同。但若索引标签乱序，`loc` 会按标签顺序输出，而 `iloc` 按位置顺序输出，此时结果可能不同。

---

> **学习建议**：`loc` 和 `iloc` 是 Pandas 数据操作的基石，务必通过大量练习熟悉它们的边界差异；`query` 则适合快速编写可读性高的筛选逻辑。三者结合使用，可以应对绝大多数数据选择场景。