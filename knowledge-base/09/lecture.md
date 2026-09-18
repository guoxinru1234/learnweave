# 随机数生成与统计函数

> 模块：NumPy数值计算 | 编号：第9讲 | Python数据分析实战

---

## 1. 概念

随机数生成与统计函数是 NumPy 中用于模拟随机现象和描述数据分布特征的两类核心工具。随机数生成基于伪随机数生成器（PRNG），通过确定性算法产生看似随机的数列，常用于蒙特卡洛模拟、抽样、数据增强和模型初始化等场景。统计函数则用于对数据集进行描述性统计分析，包括均值、方差、分位数、相关性等指标，帮助我们从数值上理解数据的集中趋势、离散程度和分布形态。

**生活化类比**：随机数生成就像掷骰子——虽然每次结果不可预测，但骰子的材质和形状决定了结果遵循的规律（均匀分布）。统计函数则像一位裁判记录多次掷骰子的结果，计算平均值、出现频率，从而判断这颗骰子是否"公平"。NumPy 的随机数生成器允许我们设定"骰子"的规则（分布类型）和"种子"（初始状态），确保实验可复现。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `numpy.random.default_rng()` | `default_rng(seed=None)` | `seed`：随机种子，整数或 None | `Generator` 对象，推荐使用的随机数生成器 |
| `Generator.normal()` | `rng.normal(loc=0.0, scale=1.0, size=None)` | `loc`：均值；`scale`：标准差；`size`：输出形状 | 符合正态分布的随机数数组 |
| `Generator.integers()` | `rng.integers(low, high=None, size=None, dtype=np.int64)` | `low`：下界（含）；`high`：上界（不含）；`size`：形状 | 均匀分布的随机整数数组 |
| `numpy.mean()` | `np.mean(a, axis=None, dtype=None)` | `a`：输入数组；`axis`：沿指定轴计算 | 算术平均值，标量或数组 |
| `numpy.percentile()` | `np.percentile(a, q, axis=None)` | `a`：输入数组；`q`：分位数（0-100） | 指定分位数的值 |

**原理说明**：NumPy 2.0 起推荐使用 `Generator` 类（通过 `default_rng` 创建），它基于 PCG64 算法，比旧版 `np.random.seed()` + 全局随机函数更快、更灵活。统计函数则基于数值算法直接计算，不依赖随机状态。

---

## 3. 代码示例

### 示例1：生成随机数并计算基本统计量（入门）

```python
import numpy as np

# 创建随机数生成器，设定种子保证可复现
rng = np.random.default_rng(seed=42)

# 生成 1000 个服从标准正态分布的随机数
data = rng.normal(loc=0.0, scale=1.0, size=1000)

# 计算基本统计量
mean_val = np.mean(data)          # 均值
std_val = np.std(data)            # 标准差
median_val = np.median(data)      # 中位数

print(f"均值: {mean_val:.4f}")      # 输出: 均值: 0.0193
print(f"标准差: {std_val:.4f}")     # 输出: 标准差: 0.9975
print(f"中位数: {median_val:.4f}")  # 输出: 中位数: 0.0208
```

### 示例2：多维随机数生成与轴向统计（进阶）

```python
import numpy as np

rng = np.random.default_rng(seed=7)

# 生成 3行4列 的均匀分布随机整数（范围 1~100）
matrix = rng.integers(low=1, high=101, size=(3, 4))
print("随机矩阵:\n", matrix)
# 输出示例:
# 随机矩阵:
#  [[57 83 22 95]
#  [ 7 44 36 18]
#  [77 40 88  6]]

# 沿行方向（axis=0）计算每列均值
col_means = np.mean(matrix, axis=0)
print("每列均值:", col_means)
# 输出: 每列均值: [47.         55.66666667 48.66666667 39.66666667]

# 沿列方向（axis=1）计算每行标准差
row_stds = np.std(matrix, axis=1)
print("每行标准差:", row_stds)
# 输出: 每行标准差: [28.22561878 14.61602567 32.45703045]

# 计算 25% 和 75% 分位数（四分位数）
q25, q75 = np.percentile(matrix, [25, 75])
print(f"25%分位数: {q25}, 75%分位数: {q75}")
# 输出: 25%分位数: 19.5, 75%分位数: 74.0
```

### 示例3：蒙特卡洛模拟——估算圆周率（综合应用）

```python
import numpy as np

def estimate_pi(n_points=100000, seed=123):
    """通过蒙特卡洛方法估算圆周率"""
    rng = np.random.default_rng(seed=seed)
    
    # 在 [0,1)x[0,1) 正方形内生成随机点
    x = rng.random(n_points)
    y = rng.random(n_points)
    
    # 判断点是否在单位圆内（圆心在原点，半径为1）
    inside = x**2 + y**2 <= 1.0
    n_inside = np.sum(inside)  # 圆内点数
    
    # 面积比 = 圆面积/正方形面积 = π/4
    pi_estimate = 4 * n_inside / n_points
    return pi_estimate

# 运行模拟
pi_est = estimate_pi()
print(f"估算的π值: {pi_est:.6f}")
# 输出: 估算的π值: 3.141520
print(f"真实π值: {np.pi:.6f}")
# 输出: 真实π值: 3.141593

# 增加样本量提高精度
pi_est_large = estimate_pi(n_points=1_000_000, seed=123)
print(f"百万样本估算π值: {pi_est_large:.6f}")
# 输出: 百万样本估算π值: 3.141612
```

---

## 4. 常见错误

### 错误1：混用新旧随机数生成 API

```python
# 错误写法：先创建 Generator，又调用全局 np.random 函数
rng = np.random.default_rng(42)
data = np.random.normal(0, 1, 100)   # 未使用 rng，种子无效

# 正确写法：统一使用 Generator 对象
rng = np.random.default_rng(42)
data = rng.normal(0, 1, 100)         # 使用 rng 生成
```

**原因**：`np.random.normal()` 使用全局随机状态，不受 `default_rng` 创建的独立 Generator 影响，导致种子设置失效。

### 错误2：`integers` 的上界理解错误

```python
# 错误写法：想要生成 1~10 的整数，误以为 high 包含上界
rng = np.random.default_rng(1)
data = rng.integers(1, 10, size=5)
print(data)  # 可能输出 9，但永远不会输出 10

# 正确写法：high 应为期望最大值 + 1
rng = np.random.default_rng(1)
data = rng.integers(1, 11, size=5)   # 生成 1~10
```

**原因**：`integers(low, high)` 的区间是 `[low, high)`，即包含 low 但不包含 high，与 Python 的 `range()` 行为一致。

### 错误3：忽略 `axis` 参数导致统计结果维度错误

```python
import numpy as np

matrix = np.array([[1, 2, 3], [4, 5, 6]])

# 错误写法：未指定 axis，对整个数组求均值
total_mean = np.mean(matrix)
print(total_mean)  # 输出 3.5（所有元素的均值）

# 正确写法：按需求指定 axis
col_mean = np.mean(matrix, axis=0)   # 每列均值
row_mean = np.mean(matrix, axis=1)   # 每行均值
print(col_mean)  # 输出 [2.5 3.5 4.5]
print(row_mean)  # 输出 [2. 5.]
```

**原因**：`axis=None` 时默认对全部元素计算统计量，返回标量；需要按维度分析时必须显式指定 `axis`。

---

## 5. 练习

### 练习1：偏态分布的数据生成与分位数分析

使用 `rng.standard_t(df=5, size=1000)` 生成 1000 个服从 t 分布（自由度为5）的随机数。计算并输出：
- 均值、中位数、标准差
- 5% 和 95% 分位数
- 与标准正态分布（`rng.normal(0, 1, 1000)`）的 95% 分位数对比，说明 t 分布的尾部特征

**答案提示**：
```python
rng = np.random.default_rng(42)
t_data = rng.standard_t(df=5, size=1000)
norm_data = rng.normal(0, 1, 1000)

print(f"t分布 95%分位数: {np.percentile(t_data, 95):.3f}")
print(f"正态分布 95%分位数: {np.percentile(norm_data, 95):.3f}")
# 预期 t 分布的 95% 分位数更大（约1.7 vs 1.65），体现厚尾特征
```

### 练习2：随机抽样与总体参数估计

从一个均值为 50、标准差为 10 的正态总体中：
1. 生成 10000 个样本作为"总体"
2. 不放回地随机抽取 500 个样本（使用 `rng.choice`）
3. 计算样本均值和总体均值，计算两者差异
4. 重复上述抽样 1000 次，绘制样本均值的直方图（使用 Matplotlib），观察抽样分布的形状

**答案提示**：
```python
import matplotlib.pyplot as plt

rng = np.random.default_rng(2024)
population = rng.normal(50, 10, 10000)
pop_mean = np.mean(population)

sample_means = []
for _ in range(1000):
    sample = rng.choice(population, size=500, replace=False)
    sample_means.append(np.mean(sample))

print(f"总体均值: {pop_mean:.3f}")
print(f"抽样分布均值: {np.mean(sample_means):.3f}")

plt.hist(sample_means, bins=30, edgecolor='black')
plt.axvline(pop_mean, color='red', linestyle='--', label='总体均值')
plt.xlabel('样本均值')
plt.ylabel('频数')
plt.title('样本均值的抽样分布')
plt.legend()
plt.show()
# 预期：抽样分布近似正态，中心接近总体均值 50
```

---

**本讲总结**：随机数生成是模拟和抽样的基础，统计函数是数据描述的利器。掌握 `Generator` 的用法、理解 `axis` 参数、注意区间边界，是避免常见错误的关键。建议在实践中结合可视化工具（如 Matplotlib）验证统计结论，加深对分布特征的理解。