# 概率分布(正态/二项/泊松)
> 模块：统计分析基础 | 编号：第42讲 | Python数据分析实战

---

## 1. 概念

概率分布是描述随机变量所有可能取值及其对应概率的数学函数，是统计推断的基石。本讲聚焦三类最常用的离散与连续分布：

- **二项分布(Binomial)**：描述在固定次数独立试验中，成功事件发生次数的分布。适用场景：掷硬币10次出现正面的次数、产品抽检中次品数量。
- **泊松分布(Poisson)**：描述在固定时间或空间区间内，稀有事件发生次数的分布。适用场景：客服每小时接到的电话数、一页书中的印刷错误数。
- **正态分布(Normal)**：描述连续型随机变量的对称钟形分布，由均值μ和标准差σ决定。适用场景：人群身高、测量误差、考试成绩。

**生活化类比**：把概率分布想象成"抽奖转盘"。二项分布是"转10次，每次只有中/不中"；泊松分布是"看1小时内中奖铃声响几次"；正态分布则是"转盘指针停留的位置——大多数时候在中间，偶尔偏到两边"。

---

## 2. 核心API与原理

本讲主要使用 `scipy.stats` 模块，它提供了完整的概率分布对象。核心API如下：

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `scipy.stats.norm` | `norm(loc=0, scale=1)` | `loc`: 均值μ；`scale`: 标准差σ | 正态分布对象，可调用 `.pdf()`, `.cdf()`, `.ppf()`, `.rvs()` |
| `scipy.stats.binom` | `binom(n, p)` | `n`: 试验次数；`p`: 单次成功概率 | 二项分布对象 |
| `scipy.stats.poisson` | `poisson(mu)` | `mu`: 平均发生率λ | 泊松分布对象 |
| `.pdf(x)` / `.pmf(k)` | 分布对象的方法 | `x`/`k`: 取值点 | 概率密度值(连续)或概率质量值(离散) |
| `.cdf(x)` | 分布对象的方法 | `x`: 取值点 | 累积概率 P(X ≤ x) |
| `.rvs(size)` | 分布对象的方法 | `size`: 生成随机数的个数 | NumPy 数组，服从该分布的随机样本 |

**原理说明**：
- 二项分布概率质量函数：P(X=k) = C(n,k) · pᵏ · (1-p)ⁿ⁻ᵏ
- 泊松分布概率质量函数：P(X=k) = e⁻λ · λᵏ / k!
- 正态分布概率密度函数：f(x) = (1/(σ√(2π))) · e^(-(x-μ)²/(2σ²))

---

## 3. 代码示例

### 示例1：二项分布——掷硬币模拟（入门）

```python
import numpy as np
from scipy.stats import binom
import matplotlib.pyplot as plt

# 设置中文字体（避免乱码）
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 掷10次硬币，正面概率0.5
n, p = 10, 0.5

# 计算恰好出现k次正面的概率（k=0到10）
k_values = np.arange(0, n+1)
probabilities = binom.pmf(k_values, n, p)

# 打印前3个概率值
for k in range(3):
    print(f"P(X={k}) = {probabilities[k]:.4f}")
# 输出:
# P(X=0) = 0.0010
# P(X=1) = 0.0098
# P(X=2) = 0.0439

# 计算累积概率 P(X ≤ 3)
cum_prob = binom.cdf(3, n, p)
print(f"P(X≤3) = {cum_prob:.4f}")
# 输出: P(X≤3) = 0.1719

# 生成1000个随机样本并绘制直方图
samples = binom.rvs(n, p, size=1000)
plt.hist(samples, bins=range(0, n+2), density=True, alpha=0.7, label='模拟样本')
plt.plot(k_values, probabilities, 'ro-', label='理论概率')
plt.xlabel('正面次数')
plt.ylabel('概率')
plt.title('二项分布 (n=10, p=0.5)')
plt.legend()
plt.show()
```

### 示例2：泊松分布——客服电话量预测（进阶）

```python
import numpy as np
from scipy.stats import poisson

# 某客服中心平均每小时接到5个电话
lambda_val = 5

# 计算1小时内接到0~10个电话的概率
k_values = np.arange(0, 11)
probs = poisson.pmf(k_values, lambda_val)

# 找出最可能的来电数
most_likely = k_values[np.argmax(probs)]
print(f"最可能的来电数: {most_likely}，概率: {probs.max():.4f}")
# 输出: 最可能的来电数: 5，概率: 0.1755

# 计算1小时内接到超过8个电话的概率
over_8 = 1 - poisson.cdf(8, lambda_val)
print(f"P(X>8) = {over_8:.4f}")
# 输出: P(X>8) = 0.0681

# 生成30天的模拟数据（每天按8小时计算）
daily_calls = poisson.rvs(lambda_val * 8, size=30)
print(f"30天模拟电话量均值: {daily_calls.mean():.1f}")
# 输出示例: 30天模拟电话量均值: 40.2
```

### 示例3：正态分布——质量控制与置信区间（综合应用）

```python
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt

# 某工厂生产的零件长度服从正态分布，均值50mm，标准差2mm
mu, sigma = 50, 2

# 绘制概率密度曲线
x = np.linspace(mu - 4*sigma, mu + 4*sigma, 200)
pdf_values = norm.pdf(x, mu, sigma)

plt.plot(x, pdf_values, 'b-', label='概率密度函数')
plt.axvline(mu, color='red', linestyle='--', label=f'均值 μ={mu}')

# 标注 μ±σ 区间
plt.axvline(mu - sigma, color='green', linestyle=':', alpha=0.7)
plt.axvline(mu + sigma, color='green', linestyle=':', alpha=0.7, label='μ±σ')
plt.xlabel('零件长度 (mm)')
plt.ylabel('概率密度')
plt.title('正态分布 N(50, 2²)')
plt.legend()
plt.show()

# 计算关键分位数
z_975 = norm.ppf(0.975, mu, sigma)
print(f"95%置信区间: [{mu - 1.96*sigma:.2f}, {mu + 1.96*sigma:.2f}]")
# 输出: 95%置信区间: [46.08, 53.92]

# 计算长度在48~52mm之间的概率
prob_between = norm.cdf(52, mu, sigma) - norm.cdf(48, mu, sigma)
print(f"P(48 ≤ X ≤ 52) = {prob_between:.4f}")
# 输出: P(48 ≤ X ≤ 52) = 0.6827

# 生成样本并验证
samples = norm.rvs(mu, sigma, size=1000)
print(f"样本均值: {samples.mean():.2f}, 样本标准差: {samples.std():.2f}")
# 输出示例: 样本均值: 50.03, 样本标准差: 2.01
```

---

## 4. 常见错误

### 错误1：混淆离散分布的 `.pdf()` 和 `.pmf()`
**错误代码**：
```python
from scipy.stats import binom
# 错误：二项分布是离散分布，没有pdf方法
prob = binom.pdf(3, n=10, p=0.5)
```
**错误原因**：`pdf`(概率密度函数)仅适用于连续分布(如正态)，离散分布应使用 `pmf`(概率质量函数)。
**正确写法**：
```python
prob = binom.pmf(3, n=10, p=0.5)  # 正确
```

### 错误2：忘记标准化直接查正态分布表
**错误代码**：
```python
from scipy.stats import norm
# 错误：直接用原始值计算，未考虑均值和标准差
prob = norm.cdf(60, loc=50, scale=2)  # 这其实是正确的
# 但常见错误是手算时忘记标准化：
# z = (60 - 50) / 2 = 5，然后查表
```
**错误原因**：手算时容易忘记将原始值转换为z分数。使用 `scipy` 时，直接传入 `loc` 和 `scale` 参数即可，但理解标准化原理仍很重要。
**正确写法**：
```python
z_score = (60 - 50) / 2  # 标准化
prob = norm.cdf(z_score)  # 标准正态分布，loc=0, scale=1
```

### 错误3：泊松分布参数理解错误
**错误代码**：
```python
from scipy.stats import poisson
# 错误：把"平均每小时5个"直接当作总参数，但样本量是10小时
total_calls = poisson.rvs(5, size=10)  # 这生成的是10个独立小时的数据
# 但若要模拟10小时总电话量，应该是：
# total_calls_10h = poisson.rvs(5*10, size=1)
```
**错误原因**：泊松分布具有可加性——若X~Poisson(λ₁)，Y~Poisson(λ₂)，则X+Y~Poisson(λ₁+λ₂)。模拟总时长时应将λ乘以时长。
**正确写法**：
```python
# 模拟10小时的总电话量（1个样本）
total_10h = poisson.rvs(5 * 10, size=1)
# 或模拟10个独立小时（10个样本）
hourly = poisson.rvs(5, size=10)
```

---

## 5. 练习

### 练习1：二项分布应用（思考题）
某电商平台商品好评率为90%。随机抽取20个用户评价，求：
1. 恰好18个好评的概率是多少？
2. 至少18个好评的概率是多少？
3. 用Python模拟10000次抽样，验证理论概率。

**答案提示**：
```python
from scipy.stats import binom
import numpy as np

# 理论概率
p_exact_18 = binom.pmf(18, n=20, p=0.9)
p_at_least_18 = 1 - binom.cdf(17, n=20, p=0.9)  # 或 sum(binom.pmf([18,19,20], 20, 0.9))

# 模拟验证
samples = binom.rvs(20, 0.9, size=10000)
sim_prob = np.mean(samples >= 18)
print(f"理论概率: {p_at_least_18:.4f}, 模拟概率: {sim_prob:.4f}")
```

### 练习2：正态分布与泊松分布综合（动手题）
某医院急诊室平均每小时接诊12个病人（服从泊松分布），病人等待时间服从均值15分钟、标准差5分钟的正态分布。
1. 计算1小时内接诊超过15个病人的概率。
2. 计算病人等待时间在10~20分钟之间的概率。
3. 绘制两个分布的图像，观察它们的形状差异。

**答案提示**：
```python
from scipy.stats import poisson, norm

# 问题1：泊松分布
p_over_15 = 1 - poisson.cdf(15, mu=12)
print(f"P(X>15) = {p_over_15:.4f}")

# 问题2：正态分布
p_wait = norm.cdf(20, loc=15, scale=5) - norm.cdf(10, loc=15, scale=5)
print(f"P(10≤X≤20) = {p_wait:.4f}")

# 问题3：绘制对比图
import matplotlib.pyplot as plt
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
k = np.arange(0, 25)
ax1.bar(k, poisson.pmf(k, 12), alpha=0.7)
ax1.set_title('泊松分布 λ=12')
x = np.linspace(0, 30, 200)
ax2.plot(x, norm.pdf(x, 15, 5))
ax2.set_title('正态分布 μ=15, σ=5')
plt.show()
```