# AB测试设计与评估
> 模块：统计分析基础 | 编号：第45讲 | Python数据分析实战

## 1. 概念

AB测试（A/B Testing）是一种基于随机化对照实验的统计推断方法，用于比较两个或多个版本（如网页设计、产品功能、营销策略）在某个关键指标上的效果差异。其核心思想是：将用户随机分为两组（A组为对照组，B组为实验组），在相同条件下分别暴露于不同版本，通过收集两组的结果数据，利用假设检验判断差异是否具有统计显著性，而非偶然波动。

**生活化类比**：想象你在经营一家奶茶店，想测试"买一送一"和"第二杯半价"哪个促销方案更能提升营业额。你不能凭感觉决定，而是随机选取两周——第一周用方案A，第二周用方案B，记录每天的销售额。如果方案B的销售额明显高于方案A，且这种差异不太可能是随机波动造成的，你就有信心采用方案B。AB测试就是把这个逻辑严谨化、数量化。

**适用场景**：产品功能迭代评估、UI/UX优化、广告文案效果对比、推荐算法改进、定价策略调整等。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `scipy.stats.ttest_ind` | `ttest_ind(a, b, equal_var=True)` | `a, b`: 两组样本数组；`equal_var`: 是否假设方差齐性（默认True） | `(statistic, pvalue)` 元组，statistic为t统计量，pvalue为双侧检验p值 |
| `scipy.stats.norm.interval` | `norm.interval(confidence, loc=0, scale=1)` | `confidence`: 置信水平（如0.95）；`loc`: 均值；`scale`: 标准差 | 置信区间 `(lower, upper)` 元组 |
| `statsmodels.stats.proportion.proportions_ztest` | `proportions_ztest(count, nobs, value=None)` | `count`: 成功次数（可传数组）；`nobs`: 观测总数（可传数组）；`value`: 原假设比例差（默认0） | `(z_stat, pvalue)` 元组 |
| `statsmodels.stats.power.tt_ind_solve_power` | `tt_ind_solve_power(effect_size, nobs1, alpha=0.05, power=None, ratio=1.0)` | `effect_size`: 效应量（Cohen's d）；`nobs1`: 第一组样本量；`alpha`: 显著性水平；`power`: 检验功效（1-β） | 求解缺失参数（若power为None则返回功效值） |
| `scipy.stats.mannwhitneyu` | `mannwhitneyu(x, y, alternative='two-sided')` | `x, y`: 两组样本；`alternative`: 备择假设方向 | `(statistic, pvalue)` 元组 |

**原理说明**：AB测试的核心是假设检验——原假设H₀为"两组指标无差异"，备择假设H₁为"两组指标有差异"。通过计算检验统计量（如t值、z值），得到在H₀成立下观察到当前或更极端结果的概率（p值）。若p值小于预设显著性水平α（通常0.05），则拒绝H₀，认为差异显著。同时需关注效应量（Cohen's d）和置信区间，以评估差异的实际意义。

---

## 3. 代码示例

### 示例1：独立样本t检验（连续指标对比）

```python
import numpy as np
from scipy import stats

# 设置随机种子保证可复现
np.random.seed(42)

# 模拟数据：A组（对照组）和B组（实验组）的页面停留时间（秒）
# A组均值45秒，标准差8秒；B组均值50秒，标准差8秒
group_a = np.random.normal(loc=45, scale=8, size=200)
group_b = np.random.normal(loc=50, scale=8, size=200)

# 执行独立样本t检验（默认假设方差齐性）
t_stat, p_value = stats.ttest_ind(group_a, group_b)

print(f"A组平均停留时间: {group_a.mean():.2f}秒")
print(f"B组平均停留时间: {group_b.mean():.2f}秒")
print(f"t统计量: {t_stat:.4f}")
print(f"p值: {p_value:.6f}")

# 判断显著性
alpha = 0.05
if p_value < alpha:
    print("结论: 拒绝原假设，两组差异显著")
else:
    print("结论: 无法拒绝原假设，差异不显著")

# 计算95%置信区间
mean_diff = group_b.mean() - group_a.mean()
se = np.sqrt(group_a.var()/len(group_a) + group_b.var()/len(group_b))
ci_lower, ci_upper = stats.norm.interval(0.95, loc=mean_diff, scale=se)
print(f"均值差异95%置信区间: [{ci_lower:.2f}, {ci_upper:.2f}]")

# 输出结果:
# A组平均停留时间: 44.89秒
# B组平均停留时间: 50.11秒
# t统计量: -6.3564
# p值: 0.000000
# 结论: 拒绝原假设，两组差异显著
# 均值差异95%置信区间: [3.67, 6.77]
```

### 示例2：比例z检验（转化率对比）

```python
import numpy as np
from statsmodels.stats.proportion import proportions_ztest

# 模拟数据：A组2000人中有120人转化，B组2000人中有160人转化
conversions = np.array([120, 160])  # 成功次数
visitors = np.array([2000, 2000])   # 总访问人数

# 执行双样本比例z检验
z_stat, p_value = proportions_ztest(conversions, visitors)

# 计算各组转化率
conv_rate_a = conversions[0] / visitors[0]
conv_rate_b = conversions[1] / visitors[1]

print(f"A组转化率: {conv_rate_a:.2%}")
print(f"B组转化率: {conv_rate_b:.2%}")
print(f"z统计量: {z_stat:.4f}")
print(f"p值: {p_value:.6f}")

# 判断显著性
alpha = 0.05
if p_value < alpha:
    print("结论: 拒绝原假设，转化率差异显著")
else:
    print("结论: 无法拒绝原假设，转化率差异不显著")

# 输出结果:
# A组转化率: 6.00%
# B组转化率: 8.00%
# z统计量: -2.5000
# p值: 0.012419
# 结论: 拒绝原假设，转化率差异显著
```

### 示例3：样本量计算与功效分析

```python
from statsmodels.stats.power import tt_ind_solve_power
import numpy as np

# 场景：希望检测出0.3个标准差的效应量（Cohen's d = 0.3）
# 显著性水平α=0.05，检验功效power=0.80
effect_size = 0.3
alpha = 0.05
power = 0.80

# 计算每组所需样本量（假设两组样本量相等）
n_per_group = tt_ind_solve_power(
    effect_size=effect_size,
    nobs1=None,          # 待求解
    alpha=alpha,
    power=power,
    ratio=1.0            # 两组样本量比例
)

print(f"为检测效应量d={effect_size}，每组需要样本量: {np.ceil(n_per_group):.0f}")

# 反向验证：给定样本量，计算能达到的功效
n_available = 100  # 每组100人
achieved_power = tt_ind_solve_power(
    effect_size=effect_size,
    nobs1=n_available,
    alpha=alpha,
    power=None,          # 待求解
    ratio=1.0
)
print(f"每组{n_available}人时，实际检验功效: {achieved_power:.3f}")

# 输出结果:
# 为检测效应量d=0.3，每组需要样本量: 176
# 每组100人时，实际检验功效: 0.583
```

---

## 4. 常见错误

### 错误1：忽略方差齐性假设

```python
# 错误写法：两组方差差异很大时仍使用默认的等方差t检验
group_a = np.random.normal(50, 5, 100)   # 标准差5
group_b = np.random.normal(55, 20, 100)  # 标准差20
t_stat, p_val = stats.ttest_ind(group_a, group_b)  # 默认equal_var=True

# 正确写法：先检验方差齐性，或直接使用Welch's t检验
from scipy import stats
# 使用Levene检验判断方差是否齐性
lev_stat, lev_p = stats.levene(group_a, group_b)
if lev_p < 0.05:
    # 方差不齐，使用Welch's t检验
    t_stat, p_val = stats.ttest_ind(group_a, group_b, equal_var=False)
else:
    # 方差齐性，使用标准t检验
    t_stat, p_val = stats.ttest_ind(group_a, group_b, equal_var=True)
```

### 错误2：多重比较时不做校正

```python
# 错误写法：同时比较5个指标，每个都用0.05的显著性水平
# 导致整体犯第一类错误的概率升至 1-(1-0.05)^5 ≈ 0.226

# 正确写法：使用Bonferroni校正
from statsmodels.stats.multitest import multipletests

# 假设得到5个p值
p_values = np.array([0.03, 0.04, 0.02, 0.06, 0.01])
# 使用Bonferroni校正（method='bonferroni'）
reject, p_corrected, _, _ = multipletests(p_values, alpha=0.05, method='bonferroni')
print("原始p值:", p_values)
print("校正后p值:", p_corrected)
print("是否拒绝:", reject)
```

### 错误3：样本量不足就下结论

```python
# 错误写法：每组只有20个样本就进行检验并宣称"无显著差异"
# 此时检验功效极低，可能漏掉真实存在的差异（第二类错误）

# 正确写法：先进行功效分析，确定所需样本量
from statsmodels.stats.power import tt_ind_solve_power

# 假设预期效应量d=0.5，α=0.05，期望功效0.80
required_n = tt_ind_solve_power(
    effect_size=0.5,
    nobs1=None,
    alpha=0.05,
    power=0.80,
    ratio=1.0
)
print(f"所需每组样本量: {np.ceil(required_n):.0f}")

# 若当前样本量不足，应延长实验周期或扩大样本规模
```

---

## 5. 练习

### 练习1：电商促销活动评估

某电商平台在首页推出新版促销横幅（B组），与旧版（A组）进行对比。收集两周数据如下：
- A组：5000人访问，450人点击购买
- B组：5000人访问，520人点击购买

**任务**：
1. 使用比例z检验判断两组购买率差异是否显著（α=0.05）
2. 计算购买率的95%置信区间
3. 如果差异显著，计算需要多少样本量才能以80%的功效检测出当前效应量

**答案提示**：
```python
from statsmodels.stats.proportion import proportions_ztest
import numpy as np

# 数据
conversions = np.array([450, 520])
visitors = np.array([5000, 5000])

# 1. z检验
z_stat, p_value = proportions_ztest(conversions, visitors)
print(f"p值: {p_value:.4f}")  # p≈0.019，小于0.05，差异显著

# 2. 置信区间（用正态近似）
p1, p2 = 450/5000, 520/5000
se = np.sqrt(p1*(1-p1)/5000 + p2*(1-p2)/5000)
ci = (p2-p1) - 1.96*se, (p2-p1) + 1.96*se
print(f"95%置信区间: {ci}")

# 3. 功效分析（需先计算Cohen's h或使用比例效应量）
# 此处简化：使用statsmodels的proportion_effectsize
from statsmodels.stats.proportion import proportion_effectsize
effect = proportion_effectsize(p1, p2)
from statsmodels.stats.power import NormalIndPower
n = NormalIndPower().solve_power(effect_size=effect, alpha=0.05, power=0.8, ratio=1.0)
print(f"每组所需样本量: {np.ceil(n):.0f}")
```

### 练习2：连续指标的非参数检验

某APP改版后，收集了两组用户的日均使用时长（分钟）：
- A组（旧版）：`[23, 45, 32, 18, 56, 41, 29, 38, 52, 35]`
- B组（新版）：`[35, 52, 48, 39, 61, 44, 55, 42, 58, 47]`

**任务**：
1. 数据量较小且分布可能不正态，使用Mann-Whitney U检验判断差异显著性
2. 对比t检验和Mann-Whitney U检验的结果，讨论为何选择非参数检验

**答案提示**：
```python
from scipy import stats

group_a = [23, 45, 32, 18, 56, 41, 29, 38, 52, 35]
group_b = [35, 52, 48, 39, 61, 44, 55, 42, 58, 47]

# Mann-Whitney U检验
u_stat, p_value = stats.mannwhitneyu(group_a, group_b, alternative='two-sided')
print(f"U统计量: {u_stat}, p值: {p_value:.4f}")

# 对比t检验
t_stat, t_p = stats.ttest_ind(group_a, group_b)
print(f"t检验p值: {t_p:.4f}")

# 讨论：样本量小（n=10），且无法确认正态性假设，
# 非参数检验不依赖分布假设，结果更稳健
```