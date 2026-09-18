# 向量化替代循环操作

> 模块：性能优化与部署 | 编号：第56讲 | Python数据分析实战

---

## 1. 概念

**向量化（Vectorization）** 是指利用 NumPy 等库底层的 C 语言实现，将原本需要 Python 循环逐元素处理的操作，转换为对整个数组（或 DataFrame 列）进行批量运算的技术。其核心思想是**避免 Python 解释器的逐行逐元素开销**，将计算下沉到经过高度优化的预编译二进制代码中执行。

**适用场景**：需要对数值型数组、矩阵或 DataFrame 的列进行逐元素运算、条件筛选、聚合统计、数学函数变换等操作时，优先考虑向量化方案。尤其在处理百万级以上的数据时，向量化带来的性能提升可达数十倍甚至上百倍。

**生活化类比**：想象你要给 1000 个苹果贴标签。循环方式就像你一个一个地拿起苹果、贴标签、放下；而向量化方式则像把苹果倒进一台自动贴标机，机器一次性处理完所有苹果。前者灵活但缓慢，后者高效但要求苹果规格统一（即数据类型一致）。

---

## 2. 核心API与原理

| API / 方法 | 签名 | 参数说明 | 返回值 | 原理说明 |
|------------|------|----------|--------|----------|
| `numpy.array` | `np.array(object, dtype=None)` | `object`: 可迭代对象；`dtype`: 指定数据类型 | `ndarray` 数组 | 将 Python 列表转换为底层连续内存的 C 数组，为后续向量化运算奠定基础 |
| `numpy.where` | `np.where(condition, x, y)` | `condition`: 布尔数组；`x`, `y`: 数组或标量 | 根据条件从 x/y 中选择元素组成的新数组 | 替代 `for` + `if-else` 的条件赋值，底层用 C 实现逐元素判断 |
| `pandas.Series.apply` | `s.apply(func, axis=0)` | `func`: 自定义函数；`axis`: 应用方向 | Series 或 DataFrame | 虽仍为 Python 级循环，但配合 `np.vectorize` 或内置函数可部分提速；**注意**：并非真正的向量化 |
| `numpy.vectorize` | `np.vectorize(pyfunc, otypes=None)` | `pyfunc`: Python 函数；`otypes`: 输出类型列表 | 向量化函数对象 | 将 Python 函数包装为可接受数组输入的函数，底层仍循环但省去 Python 层索引开销 |
| `pandas.DataFrame.applymap` | `df.applymap(func)` | `func`: 作用于每个元素的函数 | DataFrame | 对 DataFrame 每个元素应用函数，适用于元素级转换，但性能低于纯 NumPy 向量化 |

> **核心原则**：优先使用 NumPy 内置的通用函数（ufunc），如 `np.add`、`np.multiply`、`np.sqrt`、`np.log` 等，它们本身就是向量化实现。

---

## 3. 代码示例

### 示例 1：基础运算——计算数组平方根

```python
import numpy as np
import time

# 生成 100 万个随机数
data = np.random.rand(1_000_000)

# 方法一：Python 循环（慢）
start = time.time()
result_loop = [np.sqrt(x) for x in data]
loop_time = time.time() - start

# 方法二：向量化（快）
start = time.time()
result_vec = np.sqrt(data)
vec_time = time.time() - start

print(f"循环耗时: {loop_time:.4f} 秒")
print(f"向量化耗时: {vec_time:.4f} 秒")
print(f"加速比: {loop_time / vec_time:.1f} 倍")
print(f"结果一致: {np.allclose(result_loop, result_vec)}")

# 输出示例:
# 循环耗时: 0.3120 秒
# 向量化耗时: 0.0031 秒
# 加速比: 100.6 倍
# 结果一致: True
```

### 示例 2：条件筛选——使用 `np.where` 替代循环

```python
import numpy as np
import pandas as pd

# 创建模拟销售数据
sales = pd.DataFrame({
    'product': ['A', 'B', 'C', 'D', 'E'],
    'revenue': [1200, 800, 1500, 300, 950],
    'cost': [700, 900, 1000, 200, 600]
})

# 需求：计算利润，若利润为负则标记为'亏损'，否则标记为'盈利'
# 方法一：循环 + 条件判断（不推荐）
def classify_loop(row):
    profit = row['revenue'] - row['cost']
    if profit > 0:
        return '盈利'
    else:
        return '亏损'

start = time.time()
sales['status_loop'] = sales.apply(classify_loop, axis=1)
loop_time = time.time() - start

# 方法二：向量化（推荐）
start = time.time()
profit = sales['revenue'] - sales['cost']  # 向量化减法
sales['status_vec'] = np.where(profit > 0, '盈利', '亏损')
vec_time = time.time() - start

print(sales[['product', 'revenue', 'cost', 'status_loop', 'status_vec']])
print(f"\n循环耗时: {loop_time:.6f} 秒, 向量化耗时: {vec_time:.6f} 秒")

# 输出示例:
#   product  revenue  cost status_loop status_vec
# 0       A     1200   700         盈利         盈利
# 1       B      800   900         亏损         亏损
# 2       C     1500  1000         盈利         盈利
# 3       D      300   200         盈利         盈利
# 4       E      950   600         盈利         盈利
# 
# 循环耗时: 0.001200 秒, 向量化耗时: 0.000300 秒
```

### 示例 3：进阶——自定义函数的向量化包装

```python
import numpy as np
import pandas as pd

# 自定义复杂函数：根据数值区间返回等级
def score_to_grade(score):
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return 'F'

# 生成 10 万条学生成绩
scores = np.random.randint(30, 101, size=100_000)
df = pd.DataFrame({'score': scores})

# 方法一：apply（Python 级循环）
start = time.time()
df['grade_apply'] = df['score'].apply(score_to_grade)
apply_time = time.time() - start

# 方法二：np.vectorize 包装
vec_func = np.vectorize(score_to_grade, otypes=['<U1'])  # 指定输出为单字符字符串
start = time.time()
df['grade_vec'] = vec_func(df['score'])
vec_time = time.time() - start

# 方法三：纯向量化（使用 pd.cut，推荐）
bins = [0, 60, 70, 80, 90, 100]
labels = ['F', 'D', 'C', 'B', 'A']
start = time.time()
df['grade_cut'] = pd.cut(df['score'], bins=bins, labels=labels)
cut_time = time.time() - start

print(df.head(10))
print(f"\napply耗时: {apply_time:.4f} 秒")
print(f"vectorize耗时: {vec_time:.4f} 秒")
print(f"pd.cut耗时: {cut_time:.4f} 秒")
print(f"结果一致: {(df['grade_apply'] == df['grade_cut']).all()}")

# 输出示例:
#    score grade_apply grade_vec grade_cut
# 0     75           C         C         C
# 1     92           A         A         A
# 2     58           F         F         F
# 3     83           B         B         B
# 4     71           C         C         C
# ...
# apply耗时: 0.0281 秒
# vectorize耗时: 0.0052 秒
# pd.cut耗时: 0.0018 秒
```

---

## 4. 常见错误

### 错误 1：在 Pandas 中逐行循环而不是使用列运算

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})

# ❌ 错误写法：逐行循环
for i in range(len(df)):
    df.loc[i, 'sum'] = df.loc[i, 'a'] + df.loc[i, 'b']

# ✅ 正确写法：向量化列运算
df['sum'] = df['a'] + df['b']
```

**错误原因**：`df.loc[i]` 每次访问都会触发索引查找和类型检查，开销巨大。正确做法是利用 Pandas 的列级运算，底层自动调用 NumPy 向量化。

---

### 错误 2：误用 `apply` 且传入非向量化函数

```python
import numpy as np
import pandas as pd

s = pd.Series(np.random.rand(1000))

# ❌ 错误写法：apply 中调用 np.sqrt（本身就是向量化函数）
result = s.apply(np.sqrt)  # 多此一举，且性能差

# ✅ 正确写法：直接调用向量化函数
result = np.sqrt(s)
```

**错误原因**：`apply` 本质是 Python 循环，即使函数本身是向量化的，也会被逐元素调用，丧失性能优势。应直接对整个 Series 调用 NumPy 的 ufunc。

---

### 错误 3：忘记 `np.where` 的参数顺序

```python
import numpy as np

arr = np.array([1, 5, 3, 8, 2])

# ❌ 错误写法：参数顺序颠倒
result_wrong = np.where(arr > 3, arr, arr * 2)  # 条件为真时返回 arr，为假时返回 arr*2
# 这实际上是"大于3的保留原值，否则乘以2"，与预期可能相反

# ✅ 正确写法：条件为真时返回第一个值，为假时返回第二个值
result_correct = np.where(arr > 3, arr * 2, arr)  # 大于3的乘以2，否则保留原值

print(f"错误结果: {result_wrong}")  # [1 5 3 8 2]  -> 小于等于3的乘了2，但5和8没变
print(f"正确结果: {result_correct}")  # [1 10 3 16 2]

# 输出示例:
# 错误结果: [1 5 3 8 2]
# 正确结果: [ 1 10  3 16  2]
```

**错误原因**：`np.where(condition, x, y)` 的语义是"条件为真取 x，为假取 y"。新手常混淆 x 和 y 的位置，导致逻辑反转。

---

## 5. 练习

### 练习 1：动手题——温度转换优化

给定一个包含 500 万条温度记录的 NumPy 数组（单位：华氏度），要求转换为摄氏度（公式：`C = (F - 32) * 5/9`），并统计转换后温度高于 30°C 的记录数量。

**要求**：
1. 先用 Python 列表推导式实现，记录耗时；
2. 再用 NumPy 向量化实现，记录耗时；
3. 比较两种方式的耗时和结果是否一致。

<details>
<summary>答案提示</summary>

```python
import numpy as np
import time

# 生成 500 万条华氏温度数据
fahrenheit = np.random.uniform(32, 212, size=5_000_000)

# 方法一：列表推导式
start = time.time()
celsius_list = [(f - 32) * 5/9 for f in fahrenheit]
count_list = sum(1 for c in celsius_list if c > 30)
list_time = time.time() - start

# 方法二：向量化
start = time.time()
celsius_vec = (fahrenheit - 32) * 5/9
count_vec = np.sum(celsius_vec > 30)
vec_time = time.time() - start

print(f"列表推导耗时: {list_time:.3f} 秒, 计数: {count_list}")
print(f"向量化耗时: {vec_time:.3f} 秒, 计数: {count_vec}")
print(f"加速比: {list_time / vec_time:.1f} 倍")
```

</details>

---

### 练习 2：思考题——`apply` 与向量化的性能边界

思考以下问题：既然向量化性能远优于 `apply`，为什么 Pandas 仍然保留 `apply` 方法？在什么场景下 `apply` 反而是更合适的选择？

<details>
<summary>答案提示</summary>

**答案要点**：
1. **复杂逻辑**：当处理逻辑无法用 NumPy 内置函数或 `np.where` 表达时（如涉及字符串操作、正则匹配、多列交叉判断且无法拆分为简单向量化运算），`apply` 是唯一选择。
2. **可读性**：对于业务逻辑复杂但数据量较小（如 < 1 万行）的场景，`apply` 配合 lambda 或自定义函数可读性更好。
3. **兼容性**：某些第三方库函数只接受标量输入，需要 `apply` 逐行调用。
4. **性能边界**：当数据量很小（如几百行）时，向量化的启动开销可能超过循环本身，此时 `apply` 差异可忽略。

**最佳实践**：优先尝试向量化 → 若无法实现则考虑 `np.vectorize` → 最后才用 `apply`，且尽量使用内置函数而非自定义 Python 函数。

</details>