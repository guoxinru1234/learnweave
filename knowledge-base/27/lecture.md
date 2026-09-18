# Seaborn统计图表
> 模块：数据可视化 | 编号：第27讲 | Python数据分析实战

---

## 1. 概念

Seaborn 是一个基于 Matplotlib 的高级数据可视化库，专门用于**统计图表**的绘制。它的核心价值在于：**用一行代码即可完成带有统计推断的复杂图表**，例如自动计算回归线、置信区间、核密度估计等。

Seaborn 与 Pandas DataFrame 深度集成，可以直接传入列名进行绘图，并自动处理分类变量的颜色映射和图例。它内置了多种美观的主题（如 `darkgrid`、`whitegrid`），使得图表在默认状态下就具备出版级质量。

**适用场景**：探索性数据分析（EDA）、变量关系分析、分布对比、分类数据汇总等。

**生活化类比**：如果把 Matplotlib 比作"手动挡汽车"，你需要自己控制每一个齿轮（坐标轴、刻度、线条样式），那么 Seaborn 就是"自动挡汽车"——你只需要告诉它"去哪里"（数据与图表类型），它自动帮你完成换挡、转向等复杂操作，让你专注于数据分析本身，而非绘图细节。

---

## 2. 核心API与原理

| API | 签名 | 关键参数 | 返回值 | 说明 |
|-----|------|----------|--------|------|
| `sns.scatterplot` | `(data=None, x=None, y=None, hue=None, size=None, style=None, palette=None, alpha=1)` | `x`/`y`: 列名；`hue`: 分组列；`palette`: 颜色方案 | `Axes` 对象 | 散点图，自动添加图例，支持多维度映射 |
| `sns.lineplot` | `(data=None, x=None, y=None, hue=None, style=None, markers=False, dashes=False, errorbar=('ci', 95))` | `errorbar`: 误差棒类型（默认95%置信区间）；`markers`: 是否显示数据点标记 | `Axes` 对象 | 线图，自动计算均值与置信区间 |
| `sns.histplot` | `(data=None, x=None, y=None, hue=None, bins='auto', kde=False, stat='count')` | `bins`: 分箱数；`kde`: 是否叠加核密度曲线；`stat`: 统计量（count/frequency/density） | `Axes` 对象 | 直方图，支持多组对比与核密度估计 |
| `sns.boxplot` | `(data=None, x=None, y=None, hue=None, notch=False, whis=1.5)` | `notch`: 是否绘制凹口；`whis`: 须线范围倍数 | `Axes` 对象 | 箱线图，展示四分位数、中位数与异常值 |
| `sns.heatmap` | `(data, annot=False, fmt='.2g', cmap='coolwarm', cbar=True)` | `annot`: 是否在格内显示数值；`fmt`: 数值格式；`cmap`: 颜色映射 | `Axes` 对象 | 热力图，常用于相关系数矩阵可视化 |

**核心原理**：Seaborn 在底层调用 Matplotlib 绘图，但增加了**统计变换层**——例如 `lineplot` 会对每个 x 值分组计算 y 的均值与置信区间；`histplot` 会自动选择最优分箱宽度；`boxplot` 基于四分位距（IQR）计算须线范围。所有函数均返回 Matplotlib 的 `Axes` 对象，因此可以继续用 Matplotlib 的 API 进行精细化调整。

---

## 3. 代码示例

### 示例1：基础散点图与回归拟合（入门）

```python
import seaborn as sns
import matplotlib.pyplot as plt

# 加载内置数据集（企鹅数据）
penguins = sns.load_dataset("penguins")

# 绘制带回归拟合线的散点图
sns.scatterplot(
    data=penguins,
    x="bill_length_mm",
    y="bill_depth_mm",
    hue="species",          # 按物种着色
    alpha=0.7               # 设置透明度
)

plt.title("企鹅喙长与喙深的关系")
plt.tight_layout()
plt.show()

# 输出：生成一张散点图，包含3个物种（Adelie, Chinstrap, Gentoo）
# 每个物种用不同颜色表示，自动生成图例
```

### 示例2：多子图统计图表（进阶）

```python
import seaborn as sns
import matplotlib.pyplot as plt

# 加载 tips 数据集（餐厅小费数据）
tips = sns.load_dataset("tips")

# 创建1行2列的子图
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 左图：按星期分组的箱线图
sns.boxplot(
    data=tips,
    x="day",
    y="total_bill",
    hue="sex",              # 按性别分组对比
    ax=axes[0]
)
axes[0].set_title("不同星期的小费金额分布")

# 右图：总消费金额的直方图 + 核密度曲线
sns.histplot(
    data=tips,
    x="total_bill",
    kde=True,               # 叠加核密度曲线
    bins=30,
    color="skyblue",
    ax=axes[1]
)
axes[1].set_title("总消费金额分布")

plt.tight_layout()
plt.show()

# 输出：左侧为箱线图，展示周四至周日的小费分布（按性别分色）
# 右侧为直方图，叠加平滑的核密度估计曲线
```

### 示例3：相关系数热力图（综合应用）

```python
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

# 加载鸢尾花数据集
iris = sns.load_dataset("iris")

# 仅选择数值列计算相关系数矩阵
numeric_cols = iris.select_dtypes(include=["float64", "int64"])
corr_matrix = numeric_cols.corr()

# 绘制热力图
plt.figure(figsize=(8, 6))
sns.heatmap(
    corr_matrix,
    annot=True,             # 在格内显示数值
    fmt=".2f",              # 保留2位小数
    cmap="coolwarm",        # 蓝-红渐变
    linewidths=0.5,         # 格子间线宽
    cbar_kws={"label": "相关系数"}
)

plt.title("鸢尾花数值特征相关系数矩阵")
plt.tight_layout()
plt.show()

# 输出：4x4热力图，显示各特征间Pearson相关系数
# 可观察到 petal_length 与 petal_width 相关系数高达 0.96（强正相关）
```

---

## 4. 常见错误

### 错误1：忘记调用 `plt.show()`
**错误原因**：在脚本中运行 Seaborn 代码后，图表不显示。这是因为 Seaborn 只是绘制到 Matplotlib 的当前图形对象上，需要显式调用 `plt.show()` 才能渲染。

```python
# 错误写法
import seaborn as sns
df = sns.load_dataset("tips")
sns.scatterplot(data=df, x="total_bill", y="tip")
# 图表不显示！

# 正确写法
sns.scatterplot(data=df, x="total_bill", y="tip")
plt.show()  # 必须调用
```

### 错误2：混淆 `x`/`y` 参数与直接传入数组
**错误原因**：Seaborn 的面向 DataFrame 接口要求 `data` 参数与 `x`/`y` 列名配合使用。如果直接传入两个数组而不指定 `data`，会报错或行为异常。

```python
# 错误写法
import numpy as np
x = np.random.randn(100)
y = np.random.randn(100)
sns.scatterplot(x, y)  # TypeError: scatterplot() missing 1 required positional argument: 'y'

# 正确写法（两种方式均可）
# 方式1：使用 data 参数
df = pd.DataFrame({"x": x, "y": y})
sns.scatterplot(data=df, x="x", y="y")

# 方式2：显式指定参数名
sns.scatterplot(x=x, y=y)
```

### 错误3：在 `hue` 中使用连续数值变量导致颜色混乱
**错误原因**：`hue` 参数默认按分类变量处理。若传入连续数值列（如年龄），Seaborn 会将其视为分类，导致颜色映射失去渐变意义。

```python
# 错误写法
sns.scatterplot(data=tips, x="total_bill", y="tip", hue="size")
# size 是数值列，被当作分类处理，颜色无渐变

# 正确写法：使用 palette 参数配合 hue_norm
sns.scatterplot(
    data=tips, 
    x="total_bill", 
    y="tip", 
    hue="size",
    palette="viridis",      # 使用连续色带
    hue_norm=(1, 6)         # 设置数值映射范围
)
```

---

## 5. 练习

### 练习1：航班乘客数据分析（动手题）
使用 `sns.load_dataset("flights")` 数据集（包含年份、月份、乘客数三列），完成以下任务：
1. 绘制一张折线图，展示**每年各月份**乘客数量的变化趋势（x轴为月份，y轴为乘客数，不同年份用不同颜色区分）。
2. 在折线图基础上，叠加95%置信区间带。

**答案提示**：
```python
flights = sns.load_dataset("flights")
sns.lineplot(
    data=flights,
    x="month",
    y="passengers",
    hue="year",
    errorbar=("ci", 95)  # 显示置信区间
)
plt.show()
```

### 练习2：数据分布对比（思考题）
你有一份包含"治疗组"和"对照组"两组患者血压数据的数据集。请思考：如何用 Seaborn 在**同一张图**上同时展示两组的分布对比（包括中心趋势、离散程度和异常值），并说明为什么选择该图表类型。

**答案提示**：推荐使用 `sns.boxplot(data=df, x="group", y="blood_pressure")` 或 `sns.violinplot()`。箱线图能清晰展示中位数、四分位数和异常值；小提琴图额外展示核密度分布形状。若需叠加个体数据点，可配合 `sns.stripplot(jitter=True)` 使用。选择依据：箱线图适合快速对比，小提琴图适合观察分布形态。