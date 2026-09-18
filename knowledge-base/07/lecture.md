# 广播机制与向量化
> 模块：NumPy数值计算 | 编号：第7讲 | Python数据分析实战

---

## 1. 概念

**广播（Broadcasting）** 是指 NumPy 在不同形状（shape）的数组之间进行算术运算时，自动将较小数组"扩展"到与较大数组形状匹配的机制。**向量化（Vectorization）** 则是指利用 NumPy 数组的底层 C 语言循环替代 Python 显式 for 循环，从而大幅提升计算性能的编程范式。

**适用场景**：对数组进行逐元素运算（如加减乘除、比较、逻辑运算）、标准化（减去均值除以标准差）、给矩阵每一行加偏置、外积计算、网格生成等。

**生活化类比**：想象一个班级点名册（二维数组，行=学生，列=科目）。老师想给每个学生的所有科目都加上 5 分平时分（一维数组 `[5, 5, 5]`）。广播机制就像老师把这张"加分条"自动复印并贴到每一行上，无需手动为每个学生单独操作。向量化则像是用一台复印机批量处理，而不是一张一张手写。

**核心原则**：NumPy 从尾部（最后一个维度）开始比较两个数组的维度。当维度相等或其中一个为 1 时，该维度可以广播；若其中一个数组没有该维度，则视为 1。

---

## 2. 核心API与原理

| API / 方法 | 签名 | 参数说明 | 返回值 | 说明 |
|---|---|---|---|---|
| `np.broadcast_to` | `np.broadcast_to(array, shape, subok=False)` | `array`: 输入数组；`shape`: 目标形状；`subok`: 是否允许子类 | 返回只读视图（无实际复制） | 显式将数组广播到指定形状，常用于调试广播规则 |
| `np.broadcast_arrays` | `np.broadcast_arrays(*args)` | `*args`: 多个数组 | 返回广播后数组的列表（只读视图） | 同时将多个数组广播到相同形状 |
| `np.vectorize` | `np.vectorize(pyfunc, otypes=None)` | `pyfunc`: Python 函数；`otypes`: 输出类型字符串 | 返回向量化函数 | 将普通 Python 函数包装为支持广播的 ufunc 风格函数（性能低于原生 ufunc） |
| `np.newaxis` | 属性（`None` 的别名） | 无 | 用于切片时增加新维度 | 常配合广播使用，如 `arr[:, np.newaxis]` 将一维数组转为列向量 |
| `np.add` / `np.multiply` 等 ufunc | `np.add(x1, x2, out=None)` | `x1, x2`: 输入数组；`out`: 可选输出数组 | 返回运算结果数组 | 所有 ufunc 均支持广播机制 |

**广播规则（官方文档）**：
1. 从尾部维度开始比较。
2. 若维度相等或其中一个为 1，则继续比较下一个维度。
3. 若所有维度均满足条件，则结果形状为各维度最大值；否则抛出 `ValueError`。

---

## 3. 代码示例

### 示例 1：一维数组与标量运算（最基础的广播）

```python
import numpy as np

# 一维数组与标量相加：标量被广播到数组的每个元素
arr = np.array([1, 2, 3, 4])
result = arr + 10
print(result)  # 输出: [11 12 13 14]

# 二维数组每一列减去该列的均值（利用 axis=0 的广播）
matrix = np.array([[1, 2, 3],
                   [4, 5, 6],
                   [7, 8, 9]])
col_mean = matrix.mean(axis=0)  # 形状 (3,)
centered = matrix - col_mean
print(centered)
# 输出:
# [[-3. -3. -3.]
#  [ 0.  0.  0.]
#  [ 3.  3.  3.]]
```

### 示例 2：行向量与列向量相加（二维广播 + newaxis）

```python
import numpy as np

# 行向量 (1, 3) 与列向量 (3, 1) 相加 -> 结果 (3, 3)
row_vec = np.array([10, 20, 30])       # 形状 (3,)
col_vec = np.array([1, 2, 3])          # 形状 (3,)

# 利用 np.newaxis 显式调整形状
result = row_vec[np.newaxis, :] + col_vec[:, np.newaxis]
print(result)
# 输出:
# [[11 21 31]
#  [12 22 32]
#  [13 23 33]]

# 等价写法：直接使用 reshape
result2 = row_vec.reshape(1, 3) + col_vec.reshape(3, 1)
print(np.array_equal(result, result2))  # 输出: True

# 实际应用：计算外积（无需显式循环）
outer = row_vec[:, np.newaxis] * col_vec[np.newaxis, :]
print(outer)
# 输出:
# [[10 20 30]
#  [20 40 60]
#  [30 60 90]]
```

### 示例 3：向量化 vs 显式循环的性能对比

```python
import numpy as np
import time

# 生成 100 万行、3 列的数据
data = np.random.randn(1_000_000, 3)
weights = np.array([0.5, 1.5, 2.0])  # 权重向量

# 方法1：显式 Python 循环（慢）
start = time.time()
result_loop = np.empty((data.shape[0],))
for i in range(data.shape[0]):
    result_loop[i] = np.dot(data[i], weights)
time_loop = time.time() - start

# 方法2：向量化矩阵乘法（快）
start = time.time()
result_vec = data @ weights  # 等价于 np.dot(data, weights)
time_vec = time.time() - start

print(f"循环耗时: {time_loop:.4f} 秒")
print(f"向量化耗时: {time_vec:.4f} 秒")
print(f"加速比: {time_loop / time_vec:.1f} 倍")
print(f"结果一致: {np.allclose(result_loop, result_vec)}")
# 输出示例（因机器而异）:
# 循环耗时: 0.5231 秒
# 向量化耗时: 0.0032 秒
# 加速比: 163.5 倍
# 结果一致: True
```

---

## 4. 常见错误

### 错误 1：形状不兼容导致 `ValueError`

```python
import numpy as np

a = np.ones((3, 2))
b = np.ones((2, 3))

# 错误写法：直接相加
# result = a + b  # ValueError: operands could not be broadcast together

# 错误原因：尾部维度 2 与 3 不相等，且均不为 1，无法广播

# 正确写法：若想得到 (3, 3) 的结果，需先转置 b
result = a @ b.T  # 矩阵乘法，形状 (3, 3)
print(result.shape)  # 输出: (3, 3)
```

### 错误 2：忘记 `np.newaxis` 导致意外广播

```python
import numpy as np

arr = np.array([1, 2, 3])        # 形状 (3,)
col = np.array([4, 5, 6])        # 形状 (3,)

# 错误写法：意图做外积，但实际做逐元素相加
# result = arr + col  # 结果 [5, 7, 9]，形状 (3,)

# 错误原因：两个一维数组形状相同，广播退化为逐元素运算

# 正确写法：显式添加维度
result = arr[:, np.newaxis] + col[np.newaxis, :]
print(result.shape)  # 输出: (3, 3)
```

### 错误 3：`np.vectorize` 误以为能提升性能

```python
import numpy as np

def slow_func(x):
    return x * 2 + 1

# 错误认知：认为 np.vectorize 能像 ufunc 一样快
vectorized = np.vectorize(slow_func)
arr = np.arange(1000)

# 实际上 np.vectorize 内部仍是 Python 循环，仅提供语法便利
# 正确做法：直接用 NumPy 内置 ufunc
result_fast = arr * 2 + 1  # 推荐
result_slow = vectorized(arr)
print(np.array_equal(result_fast, result_slow))  # 输出: True
# 性能对比：result_fast 通常比 result_slow 快 10-50 倍
```

---

## 5. 练习

### 练习 1：标准化（Z-score）实现

**题目**：给定一个形状为 `(n_samples, n_features)` 的二维数组 `X`，请使用广播机制，在不使用 `for` 循环的前提下，对每个特征（列）进行标准化：`(x - mean) / std`。要求输出标准化后的数组，并验证每列均值约为 0、标准差约为 1。

**答案提示**：

```python
import numpy as np

X = np.random.randn(100, 5) * 10 + 5  # 模拟数据

# 核心代码（仅两行）
mean = X.mean(axis=0)   # 形状 (5,)
std = X.std(axis=0)     # 形状 (5,)
X_std = (X - mean) / std  # 广播：X (100,5) 与 (5,) 运算

# 验证
print(f"均值近似: {np.abs(X_std.mean(axis=0)).max():.2e}")  # 接近 0
print(f"标准差近似: {X_std.std(axis=0)}")  # 接近 1
```

### 练习 2：距离矩阵计算

**题目**：给定两个点集 `A`（形状 `(m, d)`）和 `B`（形状 `(n, d)`），请使用广播机制计算所有点对之间的欧氏距离，生成形状为 `(m, n)` 的距离矩阵。禁止使用 `scipy.spatial.distance` 或显式双重循环。

**答案提示**：

```python
import numpy as np

A = np.random.randn(50, 3)
B = np.random.randn(30, 3)

# 核心思路：利用广播计算差平方和
# A[:, np.newaxis, :] 形状 (50, 1, 3)
# B[np.newaxis, :, :] 形状 (1, 30, 3)
# 相减后形状 (50, 30, 3)，沿最后一维求和再开方
diff = A[:, np.newaxis, :] - B[np.newaxis, :, :]
dist_matrix = np.sqrt((diff ** 2).sum(axis=2))

print(dist_matrix.shape)  # 输出: (50, 30)

# 等价写法（利用 np.linalg.norm 的 axis 参数）
dist_matrix2 = np.linalg.norm(A[:, np.newaxis] - B, axis=2)
print(np.allclose(dist_matrix, dist_matrix2))  # 输出: True
```

---

**本讲小结**：广播机制是 NumPy 高效处理不同形状数组的核心武器，配合向量化编程可让代码既简洁又高效。掌握广播三原则（尾部对齐、维度匹配或为 1、结果取最大），并善用 `np.newaxis` 显式控制维度，即可避免绝大多数广播陷阱。