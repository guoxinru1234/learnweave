# 线性代数运算
> 模块：NumPy数值计算 | 编号：第8讲 | Python数据分析实战

## 1. 概念

线性代数运算是数值计算的核心基石，它处理的是向量、矩阵以及它们之间的运算关系。在 NumPy 中，线性代数模块 `numpy.linalg` 提供了一系列高效的矩阵运算函数，包括矩阵乘法、矩阵求逆、行列式计算、特征值分解、奇异值分解（SVD）等。这些运算在数据分析中无处不在：从多元线性回归中求解系数（`np.linalg.lstsq`），到主成分分析（PCA）中计算协方差矩阵的特征向量，再到图像压缩中使用的 SVD 分解。

**生活化类比**：可以把矩阵想象成一台"变形机器"。矩阵乘法就像把原料（向量）送入多台串联的机器流水线，每台机器按照自己的规则改变原料的形状和方向；矩阵求逆则是找到一条"逆流水线"，能把成品完美还原回原料；而特征值分解则像是找到这台机器的主轴方向——无论原料如何变化，沿这些主轴方向的伸缩比例（特征值）是固定不变的。

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 | 底层原理 |
|-----|------|----------|--------|----------|
| `np.dot(a, b)` | `dot(a, b, out=None)` | `a`, `b`: 数组（1-D或2-D） | 数组或标量 | 1-D 数组做内积，2-D 数组做矩阵乘法（`a @ b` 等价） |
| `np.linalg.inv(a)` | `inv(a)` | `a`: 方阵（M×M） | 逆矩阵（M×M） | 通过 LU 分解求解 `Ax = I`，要求矩阵非奇异（行列式≠0） |
| `np.linalg.det(a)` | `det(a)` | `a`: 方阵 | 标量（行列式值） | 基于 LU 分解计算，符号表示矩阵是否可逆及伸缩比例 |
| `np.linalg.eig(a)` | `eig(a)` | `a`: 方阵 | 返回元组 `(w, v)`，`w` 为特征值数组，`v` 为特征向量矩阵（列向量） | 求解 `Av = λv`，使用 LAPACK 的 `dgeev` 例程 |
| `np.linalg.svd(a)` | `svd(a, full_matrices=True)` | `a`: (M,N) 数组；`full_matrices`: 是否返回完整 U, Vh | 返回元组 `(u, s, vh)`，`s` 为奇异值数组（降序） | 分解 `A = U Σ V^T`，用于降维和压缩 |

## 3. 代码示例

### 示例 1：基础矩阵乘法与内积（简单）

```python
import numpy as np

# 创建两个 2x2 矩阵
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

# 矩阵乘法（两种写法等价）
C = np.dot(A, B)
C_alt = A @ B
print("A @ B =")
print(C)
# 输出:
# A @ B =
# [[19 22]
#  [43 50]]

# 一维数组内积（点积）
v1 = np.array([1, 2, 3])
v2 = np.array([4, 5, 6])
dot_product = np.dot(v1, v2)
print(f"v1 · v2 = {dot_product}")  # 输出: v1 · v2 = 32
```

### 示例 2：求解线性方程组（进阶）

```python
import numpy as np

# 求解方程组:
# 3x + y = 9
# x + 2y = 8
# 即 Ax = b
A = np.array([[3, 1], [1, 2]])
b = np.array([9, 8])

# 方法一：使用逆矩阵
A_inv = np.linalg.inv(A)
x1 = np.dot(A_inv, b)
print(f"使用逆矩阵求解: x = {x1[0]:.2f}, y = {x1[1]:.2f}")
# 输出: 使用逆矩阵求解: x = 2.00, y = 3.00

# 方法二：使用 np.linalg.solve（数值更稳定，推荐）
x2 = np.linalg.solve(A, b)
print(f"使用 solve 求解: x = {x2[0]:.2f}, y = {x2[1]:.2f}")
# 输出: 使用 solve 求解: x = 2.00, y = 3.00

# 验证行列式（判断是否可逆）
det_A = np.linalg.det(A)
print(f"A 的行列式 = {det_A:.2f}")  # 输出: A 的行列式 = 5.00
```

### 示例 3：特征值分解与 SVD 在图像压缩中的应用（进阶）

```python
import numpy as np
import matplotlib.pyplot as plt

# 创建一个简单的模拟图像（8x8 灰度矩阵）
np.random.seed(42)
img = np.random.randint(0, 256, size=(8, 8)).astype(float)
print("原始图像矩阵（8x8）:")
print(img.astype(int))

# 特征值分解（对称矩阵示例）
# 构造对称矩阵（协方差矩阵风格）
M = np.array([[2.0, 0.5], [0.5, 1.0]])
w, v = np.linalg.eig(M)
print(f"\n特征值: {w}")
print(f"特征向量（列）:\n{v}")
# 输出示例:
# 特征值: [2.20710678 0.79289322]
# 特征向量（列）:
# [[ 0.85065081 -0.52573111]
#  [ 0.52573111  0.85065081]]

# SVD 分解与低秩近似（图像压缩原理）
U, s, Vh = np.linalg.svd(img)
print(f"\n奇异值（降序）: {s}")

# 保留前 4 个奇异值进行重建（压缩到 50% 信息）
k = 4
img_approx = U[:, :k] @ np.diag(s[:k]) @ Vh[:k, :]
print(f"\n压缩重建后的矩阵（保留 {k} 个奇异值）:")
print(img_approx.astype(int))
# 输出: 压缩重建后的矩阵与原始矩阵近似，但存在一定误差
# 误差计算
error = np.linalg.norm(img - img_approx)
print(f"重建误差 (Frobenius 范数): {error:.2f}")
```

## 4. 常见错误

### 错误 1：对非方阵求逆

```python
import numpy as np

# 错误写法
A = np.array([[1, 2, 3], [4, 5, 6]])  # 2x3 矩阵
# np.linalg.inv(A)  # 抛出 LinAlgError: Last 2 dimensions of the array must be square

# 正确写法：使用伪逆（Moore-Penrose）
A_pinv = np.linalg.pinv(A)
print(f"伪逆矩阵形状: {A_pinv.shape}")  # 输出: 伪逆矩阵形状: (3, 2)
```

### 错误 2：矩阵乘法维度不匹配

```python
import numpy as np

A = np.array([[1, 2], [3, 4]])  # 2x2
B = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])  # 3x3

# 错误写法
# C = np.dot(A, B)  # ValueError: shapes (2,2) and (3,3) not aligned: 2 (dim 1) != 3 (dim 0)

# 正确写法：先检查维度，A 的列数必须等于 B 的行数
print(f"A 的列数: {A.shape[1]}, B 的行数: {B.shape[0]}")
# 输出: A 的列数: 2, B 的行数: 3
# 若需相乘，需调整维度，例如转置 B 或使用 B[:2, :2]
C = np.dot(A, B[:2, :2])  # 取 B 的前两行两列
print(f"调整后相乘结果:\n{C}")
```

### 错误 3：混淆 `np.dot` 与 `np.multiply`（元素级乘法）

```python
import numpy as np

A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

# 错误理解：以为 np.dot 是逐元素相乘
# 实际 np.dot 是矩阵乘法
C_dot = np.dot(A, B)
print("np.dot (矩阵乘法):")
print(C_dot)
# 输出:
# np.dot (矩阵乘法):
# [[19 22]
#  [43 50]]

# 正确写法：逐元素相乘用 np.multiply 或 *
C_element = np.multiply(A, B)
print("\nnp.multiply (逐元素乘法):")
print(C_element)
# 输出:
# np.multiply (逐元素乘法):
# [[ 5 12]
#  [21 32]]
```

## 5. 练习

### 练习 1：多元线性回归系数求解

给定一个数据集，特征矩阵 `X`（100 个样本，3 个特征）和目标向量 `y`，请使用 `np.linalg.lstsq` 求解线性回归系数 `β`，使得 `||Xβ - y||²` 最小。然后计算预测值与真实值的均方误差（MSE）。

**答案提示**：
```python
import numpy as np

# 生成模拟数据
np.random.seed(0)
X = np.random.randn(100, 3)
true_beta = np.array([1.5, -2.0, 0.5])
y = X @ true_beta + np.random.randn(100) * 0.1  # 加噪声

# 使用最小二乘法求解（lstsq 返回 (解, 残差, 秩, 奇异值)）
beta, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
print(f"求解的系数: {beta}")

# 计算 MSE
y_pred = X @ beta
mse = np.mean((y - y_pred) ** 2)
print(f"均方误差 MSE: {mse:.4f}")
```

### 练习 2：PCA 降维实现

给定一个 50×10 的数据矩阵 `data`（50 个样本，10 个特征），请使用 `np.linalg.eig` 实现 PCA 降维到 2 维。步骤：(1) 对数据按列中心化；(2) 计算协方差矩阵；(3) 求特征值和特征向量；(4) 取前 2 个最大特征值对应的特征向量进行投影。

**答案提示**：
```python
import numpy as np

# 生成模拟数据
np.random.seed(42)
data = np.random.randn(50, 10)

# 1. 中心化（每列减去均值）
data_centered = data - np.mean(data, axis=0)

# 2. 计算协方差矩阵（10x10）
cov_matrix = np.cov(data_centered, rowvar=False)

# 3. 特征值分解
eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)

# 4. 按特征值降序排列，取前 2 个
idx = np.argsort(eigenvalues)[::-1]  # 降序索引
top2_eigenvectors = eigenvectors[:, idx[:2]]  # 取前 2 列

# 5. 投影到 2 维
data_pca = data_centered @ top2_eigenvectors
print(f"降维后数据形状: {data_pca.shape}")  # 输出: (50, 2)

# 验证：检查投影后方差是否递减（第一维方差 > 第二维方差）
variances = np.var(data_pca, axis=0)
print(f"各主成分方差: {variances}")
```