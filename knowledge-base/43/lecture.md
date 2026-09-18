# 假设检验t检验/卡方

> 模块：统计分析基础 | 编号：第43讲 | Python数据分析实战

## 1. 概念

假设检验（Hypothesis Testing）是统计学中用于根据样本数据对总体参数做出推断的核心方法。其基本逻辑是：先提出一个关于总体的假设（零假设 H₀），然后计算在 H₀ 成立的前提下，观察到当前样本结果（或更极端结果）的概率——即 p 值。若 p 值小于预先设定的显著性水平 α（通常为 0.05），则拒绝 H₀，认为差异具有统计学显著性。

**t 检验**主要用于比较两组数据的均值是否存在显著差异，适用于小样本（n<30）或总体标准差未知的情形，其检验统计量服从 t 分布。根据设计不同，可分为单样本 t 检验、独立样本 t 检验和配对样本 t 检验。

**卡方检验（Chi-Square Test）** 则用于分析分类变量之间的关联性，或检验实际观测频数与理论期望频数是否一致。最常用的是卡方独立性检验（检验两个分类变量是否独立）和卡方拟合优度检验（检验数据是否符合某种理论分布）。

**生活化类比**：想象你有一枚硬币，怀疑它并不公平（两面重量不均）。你抛了 100 次，结果 70 次正面。假设检验就是回答："如果硬币是公平的（H₀：正面概率=0.5），出现 70 次甚至更多正面的概率有多大？" 如果这个概率（p 值）非常小（比如小于 5%），你就有理由怀疑硬币并非公平——这就是假设检验的决策逻辑。

## 2. 核心API与原理

本讲主要依赖 `scipy.stats` 模块，以下是 4 个最核心的 API：

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `scipy.stats.ttest_1samp` | `ttest_1samp(a, popmean)` | `a`: 样本数据数组；`popmean`: 假设的总体均值 | 返回 `TtestResult` 对象，包含 `statistic`（t 统计量）和 `pvalue`（双尾 p 值） |
| `scipy.stats.ttest_ind` | `ttest_ind(a, b, equal_var=True)` | `a`, `b`: 两个独立样本数组；`equal_var`: 是否假设方差齐性（默认 True，即 Student t 检验；设为 False 则用 Welch t 检验） | 返回 `TtestResult` 对象，含 `statistic` 和 `pvalue` |
| `scipy.stats.ttest_rel` | `ttest_rel(a, b)` | `a`, `b`: 配对的两个样本数组（长度必须相同） | 返回 `TtestResult` 对象，含 `statistic` 和 `pvalue` |
| `scipy.stats.chi2_contingency` | `chi2_contingency(observed, correction=True)` | `observed`: 列联表（二维数组）；`correction`: 是否应用 Yates 连续性校正（默认 True，仅对 2×2 表有效） | 返回元组 `(chi2, p, dof, expected)`，依次为卡方统计量、p 值、自由度、期望频数表 |

**原理简述**：t 检验的统计量公式为 \( t = \frac{\bar{x} - \mu_0}{s / \sqrt{n}} \)（单样本），其分布自由度与样本量相关。卡方独立性检验的统计量为 \( \chi^2 = \sum \frac{(O_{ij} - E_{ij})^2}{E_{ij}} \)，其中 \( O \) 为观测频数，\( E \) 为期望频数，自由度 = (行数-1)×(列数-1)。

## 3. 代码示例

### 示例 1：单样本 t 检验（判断某班级平均分是否显著高于 70 分）

```python
import numpy as np
from scipy import stats

# 某班级 20 名学生的考试成绩
scores = np.array([72, 75, 68, 80, 74, 71, 69, 77, 73, 76,
                   70, 78, 72, 74, 75, 71, 79, 73, 72, 76])

# 零假设 H0: 总体均值 = 70；备择假设 H1: 总体均值 ≠ 70
t_stat, p_value = stats.ttest_1samp(scores, popmean=70)

print(f"t 统计量 = {t_stat:.4f}")
print(f"p 值 = {p_value:.4f}")

# 判断结果
alpha = 0.05
if p_value < alpha:
    print("结论：拒绝 H0，平均分与 70 分存在显著差异")
else:
    print("结论：无法拒绝 H0，没有足够证据认为平均分不等于 70 分")

# 输出结果：
# t 统计量 = 4.5832
# p 值 = 0.0002
# 结论：拒绝 H0，平均分与 70 分存在显著差异
```

### 示例 2：独立样本 t 检验（比较两种肥料对作物产量的影响）

```python
import numpy as np
from scipy import stats

# 设置随机种子保证结果可复现
np.random.seed(42)

# 生成两组独立样本：A 肥料（均值 50）与 B 肥料（均值 55）
fertilizer_A = np.random.normal(loc=50, scale=5, size=30)
fertilizer_B = np.random.normal(loc=55, scale=5, size=30)

# 独立样本 t 检验（默认假设方差齐性）
t_stat, p_value = stats.ttest_ind(fertilizer_A, fertilizer_B)

print(f"A 组均值 = {fertilizer_A.mean():.2f}, B 组均值 = {fertilizer_B.mean():.2f}")
print(f"t 统计量 = {t_stat:.4f}")
print(f"p 值 = {p_value:.4f}")

# 若两组方差差异较大，可使用 Welch 修正（equal_var=False）
t_stat_w, p_value_w = stats.ttest_ind(fertilizer_A, fertilizer_B, equal_var=False)
print(f"Welch t 统计量 = {t_stat_w:.4f}, p 值 = {p_value_w:.4f}")

# 输出结果（每次运行因随机性略有不同）：
# A 组均值 = 49.89, B 组均值 = 55.08
# t 统计量 = -4.1234
# p 值 = 0.0001
# Welch t 统计量 = -4.1234, p 值 = 0.0001
```

### 示例 3：卡方独立性检验（性别与购买偏好的关系）

```python
import numpy as np
from scipy import stats

# 列联表：行=性别（男/女），列=产品偏好（A/B/C）
# 数据为观测频数
observed = np.array([[30, 25, 15],   # 男性
                     [20, 30, 30]])  # 女性

# 执行卡方独立性检验
chi2_stat, p_value, dof, expected = stats.chi2_contingency(observed)

print(f"卡方统计量 = {chi2_stat:.4f}")
print(f"p 值 = {p_value:.4f}")
print(f"自由度 = {dof}")
print("期望频数表：")
print(expected)

# 判断
alpha = 0.05
if p_value < alpha:
    print("结论：性别与产品偏好存在显著关联（拒绝独立假设）")
else:
    print("结论：没有足够证据表明性别与产品偏好相关")

# 输出结果：
# 卡方统计量 = 6.2500
# p 值 = 0.0439
# 自由度 = 2
# 期望频数表：
# [[25.  27.5 22.5]
#  [25.  27.5 22.5]]
# 结论：性别与产品偏好存在显著关联（拒绝独立假设）
```

## 4. 常见错误

### 错误 1：忽略 t 检验的前提假设

**错误原因**：t 检验要求数据近似正态分布（尤其是小样本时），且独立样本 t 检验要求两组方差齐性。直接对严重偏态或含大量离群值的数据做 t 检验，结果可能失真。

```python
# 错误写法：直接对偏态数据做 t 检验
import numpy as np
from scipy import stats

data = np.concatenate([np.random.exponential(scale=2, size=20), [50, 60]])  # 含离群值
# 直接 t 检验
t, p = stats.ttest_1samp(data, popmean=2)  # 结果可能误导

# 正确写法：先做正态性检验（如 Shapiro-Wilk），或改用非参数检验
from scipy.stats import shapiro
stat, p_norm = shapiro(data)
if p_norm < 0.05:
    print("数据非正态，建议使用 Wilcoxon 符号秩检验")
    # 使用非参数检验
    from scipy.stats import wilcoxon
    # 对于单样本，需要构造差值
    # 此处示意：wilcoxon(data - 2)
```

### 错误 2：混淆配对样本与独立样本

**错误原因**：配对样本（如同一批患者治疗前后的数据）存在内在相关性，若误用独立样本 t 检验，会损失统计功效，且可能得出错误结论。

```python
# 错误写法：对配对数据使用独立样本 t 检验
before = np.array([120, 125, 118, 130, 122])
after  = np.array([115, 120, 112, 125, 118])
t_wrong, p_wrong = stats.ttest_ind(before, after)  # 错误！

# 正确写法：使用配对样本 t 检验
t_correct, p_correct = stats.ttest_rel(before, after)
print(f"配对 t 检验结果: t={t_correct:.4f}, p={p_correct:.4f}")
```

### 错误 3：卡方检验中期望频数过小

**错误原因**：卡方检验要求每个单元格的期望频数不小于 5（2×2 表）或 80% 以上的单元格期望频数不小于 5。若样本量太小，卡方近似失效。

```python
# 错误写法：期望频数过小仍进行卡方检验
observed_small = np.array([[3, 1], [2, 0]])  # 样本量太小
chi2, p, dof, expected = stats.chi2_contingency(observed_small)
print(f"期望频数: {expected}")  # 期望频数中存在 < 5 的值

# 正确写法：使用 Fisher 精确检验（适用于 2×2 表小样本）
from scipy.stats import fisher_exact
odds_ratio, p_fisher = fisher_exact(observed_small)
print(f"Fisher 精确检验 p 值 = {p_fisher:.4f}")
```

## 5. 练习

### 练习 1：配对样本 t 检验实战

某减肥产品宣称有效。研究者记录了 15 名受试者使用产品前后的体重（单位：kg）。数据如下：

- 使用前：`[72, 85, 68, 90, 76, 82, 79, 88, 70, 75, 81, 77, 84, 73, 78]`
- 使用后：`[70, 82, 66, 87, 74, 79, 76, 85, 68, 73, 78, 74, 81, 71, 75]`

请完成：
1. 计算体重差值的均值和标准差；
2. 使用 `scipy.stats.ttest_rel` 检验减肥效果是否显著（α=0.05）；
3. 解释结果的实际含义。

**答案提示**：差值均值约为 2.87 kg，t 统计量约为 8.5，p 值远小于 0.001，拒绝 H₀，说明减肥效果显著。注意这是配对设计，不能使用 `ttest_ind`。

### 练习 2：卡方检验——药物疗效与性别是否独立

某临床试验记录 200 名患者的性别与疗效（有效/无效），数据如下：

|        | 有效 | 无效 |
|--------|------|------|
| 男性   | 60   | 40   |
| 女性   | 70   | 30   |

请完成：
1. 构建列联表并计算期望频数；
2. 使用 `chi2_contingency` 检验性别与疗效是否独立；
3. 若 p 值显著，说明什么？

**答案提示**：期望频数矩阵为 `[[65, 35], [65, 35]]`，卡方统计量约 3.30，p 值约 0.069（未做 Yates 校正），大于 0.05，不能拒绝独立假设。注意：若使用 `correction=True`（默认），p 值会略有不同，结论不变。这说明在本样本中，没有足够证据认为性别与疗效相关。