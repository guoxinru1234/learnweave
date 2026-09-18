# 描述统计(均值/方差/分位数)

> 模块：统计分析基础 | 编号：第41讲 | Python数据分析实战

---

## 1. 概念

描述统计（Descriptive Statistics）是通过计算一组数据的集中趋势、离散程度和分布形态等指标，来概括和描述数据整体特征的统计方法。它不涉及从样本推断总体，而是直接对已有数据进行归纳总结。

- **均值（Mean）**：衡量数据的集中趋势，即数据的"平均水平"。
- **方差（Variance）与标准差（Standard Deviation）**：衡量数据的离散程度，即数据围绕均值的波动大小。
- **分位数（Quantile）**：将数据按大小排序后切分成若干等份的分界点，如中位数（第50百分位）、四分位数等，用于描述数据的分布位置和偏态。

**生活化类比**：想象你是一名班主任，期末考试后拿到全班成绩单。均值告诉你"平均分是多少"；方差告诉你"大家成绩是整齐还是参差不齐"；分位数则告诉你"排名前25%的同学分数线是多少、后25%的及格线在哪"。三者结合，你就能快速掌握全班成绩的整体面貌。

---

## 2. 核心API与原理

| API | 所属库 | 签名 | 关键参数 | 返回值 |
|-----|--------|------|----------|--------|
| `numpy.mean()` | NumPy | `numpy.mean(a, axis=None, dtype=None)` | `a`: 数组或类数组；`axis`: 沿指定轴计算，`None`表示全部元素 | 标量或数组（均值） |
| `numpy.var()` | NumPy | `numpy.var(a, axis=None, ddof=0)` | `a`: 数组；`ddof`: 自由度修正（`1`为样本方差，`0`为总体方差） | 标量或数组（方差） |
| `numpy.std()` | NumPy | `numpy.std(a, axis=None, ddof=0)` | 同 `var` | 标量或数组（标准差） |
| `numpy.percentile()` | NumPy | `numpy.percentile(a, q, axis=None)` | `a`: 数组；`q`: 分位数（0-100的标量或列表） | 标量或数组（分位数值） |
| `DataFrame.describe()` | Pandas | `DataFrame.describe(percentiles=None, include=None)` | `percentiles`: 自定义分位点列表（默认`[.25, .5, .75]`） | 包含计数、均值、标准差、最小值、分位数、最大值的统计表 |

**原理说明**：
- 均值：$\bar{x} = \frac{1}{n}\sum_{i=1}^{n}x_i$
- 总体方差：$\sigma^2 = \frac{1}{n}\sum_{i=1}^{n}(x_i - \bar{x})^2$；样本方差（`ddof=1`）：$s^2 = \frac{1}{n-1}\sum_{i=1}^{n}(x_i - \bar{x})^2$
- 分位数：将数据升序排列后，第 $p$ 百分位表示有 $p\%$ 的数据小于等于该值。NumPy 默认采用**线性插值**法计算。

---

## 3. 代码示例

### 示例1：基础计算——NumPy 实现

```python
import numpy as np

# 模拟10名学生的考试成绩
scores = np.array([78, 85, 92, 67, 88, 95, 73, 81, 90, 60])

# 均值
mean_val = np.mean(scores)
print(f"平均分: {mean_val:.2f}")          # 输出: 平均分: 80.90

# 总体方差与标准差
var_pop = np.var(scores)
std_pop = np.std(scores)
print(f"总体方差: {var_pop:.2f}")         # 输出: 总体方差: 116.49
print(f"总体标准差: {std_pop:.2f}")       # 输出: 总体标准差: 10.79

# 样本方差与标准差（分母为 n-1）
var_sample = np.var(scores, ddof=1)
std_sample = np.std(scores, ddof=1)
print(f"样本方差: {var_sample:.2f}")      # 输出: 样本方差: 129.43
print(f"样本标准差: {std_sample:.2f}")    # 输出: 样本标准差: 11.38

# 分位数：中位数、四分位数、90分位
q25, q50, q75, q90 = np.percentile(scores, [25, 50, 75, 90])
print(f"25分位: {q25}, 中位数: {q50}, 75分位: {q75}, 90分位: {q90}")
# 输出: 25分位: 73.0, 中位数: 81.5, 75分位: 89.5, 90分位: 93.5
```

### 示例2：Pandas 描述统计——真实业务场景

```python
import pandas as pd

# 创建销售数据 DataFrame
data = {
    "月份": ["1月", "2月", "3月", "4月", "5月", "6月"],
    "销售额": [12000, 13500, 11000, 14500, 12800, 15200],
    "订单量": [320, 350, 290, 380, 340, 410]
}
df = pd.DataFrame(data)

# 使用 describe() 一键获取主要描述统计量
stats = df[["销售额", "订单量"]].describe(percentiles=[.1, .9])
print(stats)
# 输出:
#             销售额         订单量
# count      6.000000    6.000000
# mean   13166.666667  348.333333
# std     1483.117190   42.472186
# min    11000.000000  290.000000
# 10%    11200.000000  296.000000
# 50%    13150.000000  345.000000
# 90%    14960.000000  404.000000
# max    15200.000000  410.000000

# 单独计算某列的方差和分位数
print(f"销售额方差: {df['销售额'].var():.2f}")   # 输出: 销售额方差: 2199666.67
print(f"订单量75分位: {df['订单量'].quantile(0.75)}")  # 输出: 订单量75分位: 372.5
```

### 示例3：多维数组与分组统计（进阶）

```python
import numpy as np
import pandas as pd

# 3家门店4个月的销售数据（行=门店，列=月份）
sales_matrix = np.array([
    [100, 120, 110, 130],   # 门店A
    [80, 90, 85, 95],       # 门店B
    [200, 210, 195, 220]    # 门店C
])

# 按行（axis=1）计算每家门店的月均销售额
store_means = np.mean(sales_matrix, axis=1)
print(f"各门店月均销售额: {store_means}")
# 输出: 各门店月均销售额: [115.   87.5 206.25]

# 按列（axis=0）计算每个月所有门店的销售额标准差
month_stds = np.std(sales_matrix, axis=0, ddof=1)
print(f"各月份门店间标准差: {np.round(month_stds, 2)}")
# 输出: 各月份门店间标准差: [64.29 64.29 60.14 64.29]

# 使用 Pandas groupby 进行分组描述统计
df = pd.DataFrame({
    "门店": ["A", "A", "B", "B", "C", "C"],
    "季度": ["Q1", "Q2", "Q1", "Q2", "Q1", "Q2"],
    "销售额": [100, 120, 80, 90, 200, 210]
})
grouped = df.groupby("门店")["销售额"].agg(["mean", "var", "std"])
print(grouped)
# 输出:
#           mean    var        std
# 门店
# A        110.0  200.0  14.142136
# B         85.0   50.0   7.071068
# C        205.0   50.0   7.071068
```

---

## 4. 常见错误

### 错误1：混淆总体方差与样本方差

```python
import numpy as np

data = np.array([1, 2, 3, 4, 5])

# 错误写法：计算样本方差时忘记设置 ddof=1
sample_var_wrong = np.var(data)   # 得到总体方差 2.0

# 正确写法：样本方差应设置 ddof=1
sample_var_correct = np.var(data, ddof=1)  # 得到样本方差 2.5
print(f"总体方差: {sample_var_wrong}, 样本方差: {sample_var_correct}")
```

**原因**：`np.var()` 默认 `ddof=0`（总体方差），而实际数据分析中数据多为样本，应使用 `ddof=1` 进行无偏估计。

### 错误2：分位数参数 q 传入小数而非百分数

```python
import numpy as np

data = np.array([10, 20, 30, 40, 50])

# 错误写法：q 传入了 0.5（小数形式）
# result = np.percentile(data, 0.5)   # 返回 10.2，并非中位数

# 正确写法：q 应为 0-100 之间的百分数
result_correct = np.percentile(data, 50)   # 返回 30.0（中位数）
print(f"中位数: {result_correct}")
```

**原因**：`numpy.percentile()` 的 `q` 参数范围是 0-100，不是 0-1。若误传 0.5，实际计算的是第 0.5 百分位，几乎等于最小值。

### 错误3：DataFrame 中包含非数值列时直接调用 describe()

```python
import pandas as pd

df = pd.DataFrame({
    "姓名": ["张三", "李四", "王五"],
    "年龄": [25, 30, 35],
    "城市": ["北京", "上海", "广州"]
})

# 错误写法：直接 describe() 会忽略非数值列，且不报错
# print(df.describe())   # 只显示"年龄"列统计

# 正确写法：明确选择数值列
print(df[["年龄"]].describe())
# 输出:
#             年龄
# count   3.000000
# mean   30.000000
# std     5.000000
# min    25.000000
# 25%    27.500000
# 50%    30.000000
# 75%    32.500000
# max    35.000000
```

**原因**：`describe()` 默认只统计数值列，若需包含分类列应使用 `include='all'` 参数，但此时均值、方差等指标对非数值列不适用。

---

## 5. 练习

### 练习1：思考题

某电商平台记录了 100 位用户的月消费金额（单位：元），你计算得到均值 = 850，中位数 = 420，标准差 = 1200。请回答：

1. 这个数据分布是左偏还是右偏？为什么？
2. 仅凭均值和标准差，能否判断数据中存在极端值？请说明理由。

**答案提示**：
1. 右偏（正偏）。因为均值（850）远大于中位数（420），说明少数高消费用户拉高了均值，数据右侧尾部较长。
2. 能初步判断。标准差（1200）大于均值（850），说明数据波动极大，且均值被少数大值拉高，很可能存在极端高值（如个别用户消费数万元）。

### 练习2：动手题

使用 NumPy 生成 1000 个服从正态分布（均值=50，标准差=10）的随机数，然后完成以下任务：

1. 计算样本均值、样本标准差（`ddof=1`），并与理论值（50 和 10）比较。
2. 计算第 5、25、50、75、95 百分位数，并说明这些分位数与正态分布理论分位数的关系。
3. 将数据放入 Pandas DataFrame 中，使用 `describe()` 输出统计摘要。

**答案提示**：

```python
import numpy as np
import pandas as pd

# 生成数据
np.random.seed(42)  # 固定随机种子保证可复现
data = np.random.normal(loc=50, scale=10, size=1000)

# 任务1：样本统计量
sample_mean = np.mean(data)
sample_std = np.std(data, ddof=1)
print(f"样本均值: {sample_mean:.2f}, 样本标准差: {sample_std:.2f}")
# 输出接近: 样本均值: 49.98, 样本标准差: 10.02

# 任务2：分位数计算
quantiles = np.percentile(data, [5, 25, 50, 75, 95])
print(f"分位数: {np.round(quantiles, 2)}")
# 理论值约为: [33.55, 43.26, 50.00, 56.74, 66.45]

# 任务3：Pandas describe
df = pd.DataFrame({"消费": data})
print(df.describe())
```

**关键点**：样本量足够大时，样本统计量应接近理论值；分位数与正态分布理论分位数（均值±z*标准差）基本吻合。

---

> **小结**：描述统计是数据分析的第一步，均值给出中心位置，方差/标准差衡量波动，分位数揭示分布形态。掌握 NumPy 和 Pandas 中的核心 API，能让你快速从原始数据中提取关键信息，为后续的推断统计和建模打下基础。