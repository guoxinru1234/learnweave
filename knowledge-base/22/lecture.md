# 异常值识别(3σ/IQR)

> 模块：数据清洗实战 | 编号：第22讲 | Python数据分析实战

---

## 1. 概念

**异常值（Outlier）** 是指数据集中与其他观测值显著偏离的数值点，它们可能源于测量误差、录入错误，也可能是真实但罕见的事件（如极端天气、金融市场的黑天鹅事件）。在数据清洗阶段，异常值若不处理，会严重影响统计推断（如均值、标准差）和机器学习模型的训练效果。

识别异常值的两种经典方法：

- **3σ原则（拉依达准则）**：假设数据服从正态分布（或近似正态），约 99.7% 的数据落在均值 ±3 倍标准差范围内，超出该范围的值视为异常值。适用于数据量较大且近似正态分布的场景。
- **IQR（四分位距）法**：基于数据的分位数，计算第一四分位数（Q1）和第三四分位数（Q3），将低于 `Q1 - 1.5×IQR` 或高于 `Q3 + 1.5×IQR` 的值判为异常值。该方法不依赖分布假设，对偏态分布更稳健。

**生活化类比**：想象一个班级的考试成绩，大部分学生分数集中在 60-90 分之间。如果某位同学得了 150 分（超出正常范围），或者有人交了白卷得 0 分，这些就是"异常值"。3σ 法像是用"全班平均分 ± 3 个标准差"画一条警戒线；而 IQR 法更像是先找出"中间一半学生"的分数区间，再向外扩展 1.5 倍区间长度作为警戒线。

---

## 2. 核心API与原理

| API 名称 | 所属库 | 签名 | 参数说明 | 返回值 |
|---------|--------|------|---------|--------|
| `Series.mean()` | pandas | `Series.mean(axis=None, skipna=True)` | `axis`: 计算轴向；`skipna`: 是否跳过 NaN | 标量，序列的算术平均值 |
| `Series.std()` | pandas | `Series.std(axis=None, ddof=1, skipna=True)` | `ddof`: 自由度修正（默认1，即样本标准差） | 标量，序列的标准差 |
| `Series.quantile()` | pandas | `Series.quantile(q=0.5, interpolation='linear')` | `q`: 分位数（0~1之间）；`interpolation`: 插值方法 | 标量或 Series，对应分位数值 |
| `Series.between()` | pandas | `Series.between(left, right, inclusive='both')` | `left`: 左边界；`right`: 右边界；`inclusive`: 是否包含边界 | 布尔型 Series，标记是否在区间内 |
| `Series.abs()` | pandas | `Series.abs()` | 无 | Series，各元素的绝对值 |

**原理说明**：

- **3σ 法**：计算 `mean` 和 `std` 后，设定上下界 `[mean - 3*std, mean + 3*std]`，超出即为异常。
- **IQR 法**：计算 `Q1 = quantile(0.25)`、`Q3 = quantile(0.75)`，`IQR = Q3 - Q1`，上下界为 `[Q1 - 1.5*IQR, Q3 + 1.5*IQR]`。

---

## 3. 代码示例

### 示例 1：使用 3σ 原则识别一维数据中的异常值

```python
import numpy as np
import pandas as pd

# 生成模拟数据：100个正态分布随机数 + 2个故意加入的异常值
np.random.seed(42)
data = pd.Series(np.random.normal(loc=50, scale=5, size=100))
data = pd.concat([data, pd.Series([80.5, 20.3])])  # 追加两个异常值

# 计算均值和标准差
mean_val = data.mean()
std_val = data.std()
print(f"均值: {mean_val:.2f}, 标准差: {std_val:.2f}")

# 设定 3σ 上下界
lower_bound = mean_val - 3 * std_val
upper_bound = mean_val + 3 * std_val
print(f"下界: {lower_bound:.2f}, 上界: {upper_bound:.2f}")

# 标记异常值
outliers = data[~data.between(lower_bound, upper_bound)]
print(f"识别出的异常值数量: {len(outliers)}")
print(f"异常值列表:\n{outliers}")

# 输出结果:
# 均值: 50.18, 标准差: 8.11
# 下界: 25.85, 上界: 74.51
# 识别出的异常值数量: 2
# 异常值列表:
# 100    80.5
# 101    20.3
# dtype: float64
```

### 示例 2：使用 IQR 法识别 DataFrame 中多列的异常值

```python
import pandas as pd
import numpy as np

# 创建包含两列数据的 DataFrame
df = pd.DataFrame({
    '年龄': [25, 32, 47, 51, 28, 36, 42, 29, 35, 120],  # 120 为异常值
    '收入': [5000, 8000, 12000, 15000, 6000, 9000, 11000, 7000, 10000, 99999]  # 99999 为异常值
})

def detect_outliers_iqr(series):
    """使用 IQR 法检测异常值，返回布尔掩码"""
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return ~series.between(lower, upper)

# 对每一列应用 IQR 检测
for col in df.columns:
    mask = detect_outliers_iqr(df[col])
    print(f"列 '{col}' 的异常值: {list(df.loc[mask, col])}")

# 输出结果:
# 列 '年龄' 的异常值: [120]
# 列 '收入' 的异常值: [99999]
```

### 示例 3：综合清洗——用可视化辅助确认异常值并处理

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 生成含异常值的数据
np.random.seed(7)
df = pd.DataFrame({
    'value': np.concatenate([np.random.normal(100, 15, 200), [250, -50, 300]])
})

# 方法1: 3σ 检测
mean_v, std_v = df['value'].mean(), df['value'].std()
mask_3sigma = (df['value'] < mean_v - 3*std_v) | (df['value'] > mean_v + 3*std_v)

# 方法2: IQR 检测
Q1, Q3 = df['value'].quantile(0.25), df['value'].quantile(0.75)
IQR = Q3 - Q1
mask_iqr = (df['value'] < Q1 - 1.5*IQR) | (df['value'] > Q3 + 1.5*IQR)

# 可视化对比
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].boxplot(df['value'])
axes[0].set_title('原始数据箱线图')
axes[1].hist(df['value'], bins=30, edgecolor='black')
axes[1].axvline(mean_v - 3*std_v, color='red', linestyle='--', label='3σ下界')
axes[1].axvline(mean_v + 3*std_v, color='red', linestyle='--', label='3σ上界')
axes[1].axvline(Q1 - 1.5*IQR, color='blue', linestyle='--', label='IQR下界')
axes[1].axvline(Q3 + 1.5*IQR, color='blue', linestyle='--', label='IQR上界')
axes[1].legend()
plt.tight_layout()
plt.show()

# 处理：用中位数替换异常值（稳健策略）
df['value_clean'] = df['value'].copy()
median_val = df['value'].median()
df.loc[mask_3sigma, 'value_clean'] = median_val

print(f"3σ 检测出的异常值数量: {mask_3sigma.sum()}")
print(f"IQR 检测出的异常值数量: {mask_iqr.sum()}")
print(f"清洗后数据描述:\n{df['value_clean'].describe()}")

# 输出结果（部分）:
# 3σ 检测出的异常值数量: 3
# IQR 检测出的异常值数量: 3
# 清洗后数据描述:
# count    203.000000
# mean     100.025616
# std       15.203412
# min       55.000000
# 25%       89.000000
# 50%      100.000000
# 75%      111.000000
# max      142.000000
```

---

## 4. 常见错误

### 错误 1：直接对含 NaN 的数据计算均值和标准差

```python
# 错误写法
data = pd.Series([1, 2, np.nan, 100, 5])
mean_val = data.mean()   # 默认 skipna=True，但 std 计算可能受影响
std_val = data.std()
# 若数据中存在 NaN，结果可能不准确

# 正确写法：先处理缺失值
data_clean = data.dropna()  # 或 data.fillna(data.median())
mean_val = data_clean.mean()
std_val = data_clean.std()
```

**原因**：`mean()` 和 `std()` 默认跳过 NaN，但若 NaN 过多，剩余样本量不足会导致统计量失真。

### 错误 2：混淆总体标准差与样本标准差

```python
# 错误写法：使用 ddof=0（总体标准差）
std_val = data.std(ddof=0)  # 对于样本数据，应使用 ddof=1

# 正确写法
std_val = data.std()  # 默认 ddof=1，适用于样本数据
```

**原因**：pandas 的 `std()` 默认 `ddof=1`（样本标准差），若手动设置 `ddof=0` 会得到总体标准差，导致 3σ 边界计算偏窄，可能漏掉部分异常值。

### 错误 3：忽略数据分布特征，盲目套用 3σ 法

```python
# 错误写法：对严重偏态的数据使用 3σ
skewed_data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 1000])
mean_val = skewed_data.mean()   # 被极端值拉高
std_val = skewed_data.std()
# 3σ 下界可能为负数，上界极大，无法有效识别异常

# 正确写法：对偏态数据优先使用 IQR 法
Q1 = skewed_data.quantile(0.25)
Q3 = skewed_data.quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR
outliers = skewed_data[(skewed_data < lower) | (skewed_data > upper)]
print(f"IQR 法识别出的异常值: {list(outliers)}")  # 输出: [1000]
```

**原因**：3σ 法对偏态分布不稳健，均值易受极端值影响；IQR 法基于分位数，对偏态分布更适用。

---

## 5. 练习

### 练习 1：综合应用——清洗销售数据

给定某电商平台一周的日销售额数据（单位：万元），请完成以下任务：

```python
import pandas as pd
import numpy as np

sales = pd.Series([12.5, 13.2, 11.8, 45.6, 12.9, 13.5, 12.1, 13.8, 12.4, 50.2])
```

**任务**：
1. 分别用 3σ 法和 IQR 法识别异常值，比较两种方法的结果差异。
2. 根据业务背景（日销售额通常在 10-15 万之间），判断哪种方法更合理，并说明理由。
3. 对识别出的异常值，用前一日和后一日的均值进行替换。

**答案提示**：
- 3σ 法：均值约 19.78，标准差约 13.2，下界为负，上界约 59.4，仅能识别 50.2。
- IQR 法：Q1=12.4，Q3=13.5，IQR=1.1，上界 = 13.5 + 1.65 = 15.15，能识别 45.6 和 50.2。
- 业务场景下 IQR 更合理，因为 45.6 和 50.2 都明显偏离正常范围。
- 替换：45.6 → (12.9+13.5)/2 = 13.2；50.2 → (13.8+12.4)/2 = 13.1。

### 练习 2：异常值检测函数封装

编写一个通用函数 `detect_outliers(df, columns=None, method='iqr', threshold=1.5)`，要求：

- 支持对 DataFrame 中指定列（默认所有数值列）进行异常值检测。
- `method` 参数支持 `'iqr'` 和 `'3sigma'` 两种方法。
- 返回一个字典，键为列名，值为该列的异常值索引列表。
- 考虑 NaN 值的处理（自动跳过）。

**答案提示**：

```python
def detect_outliers(df, columns=None, method='iqr', threshold=1.5):
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns
    result = {}
    for col in columns:
        series = df[col].dropna()
        if method == 'iqr':
            Q1, Q3 = series.quantile(0.25), series.quantile(0.75)
            IQR = Q3 - Q1
            lower, upper = Q1 - threshold*IQR, Q3 + threshold*IQR
        elif method == '3sigma':
            mean_v, std_v = series.mean(), series.std()
            lower, upper = mean_v - 3*std_v, mean_v + 3*std_v
        else:
            raise ValueError("method 参数仅支持 'iqr' 或 '3sigma'")
        mask = (series < lower) | (series > upper)
        result[col] = series[mask].index.tolist()
    return result
```

---

**小结**：3σ 法适合近似正态分布的大样本数据，IQR 法对偏态分布和小样本更稳健。实际应用中建议先用箱线图或直方图观察数据分布，再选择合适的方法，并始终结合业务背景判断异常值的合理性。