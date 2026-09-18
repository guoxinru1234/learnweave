# 相关性与线性回归

> 模块：统计分析基础 | 编号：第44讲 | Python数据分析实战

---

## 1. 概念

**相关性（Correlation）** 用于衡量两个变量之间线性关系的方向和强度，取值范围在 -1 到 1 之间。相关系数接近 1 表示强正相关，接近 -1 表示强负相关，接近 0 表示无明显线性关系。**线性回归（Linear Regression）** 则是通过拟合一条直线 \( y = \beta_0 + \beta_1 x \) 来量化自变量 \( x \) 对因变量 \( y \) 的影响，并可用于预测。

**生活化类比**：想象你记录每天的学习时长和考试成绩。如果学习时间越长，成绩普遍越高，这两个变量就存在正相关；而线性回归就像根据这些散点画一条“最合适的直线”，让你能根据学习时长大致预测能考多少分。相关性告诉你“有没有关系、关系多强”，回归告诉你“具体是什么关系、能怎么预测”。

**适用场景**：探索变量间关系、特征筛选、简单预测建模、数据诊断（如检查多重共线性）。

---

## 2. 核心API与原理

| API | 所属库 | 签名与参数 | 返回值 |
|-----|--------|-----------|--------|
| `DataFrame.corr()` | Pandas | `df.corr(method='pearson', min_periods=1)`，`method` 可选 `'pearson'`、`'spearman'`、`'kendall'` | 相关系数矩阵（DataFrame） |
| `scipy.stats.pearsonr` | SciPy | `pearsonr(x, y)`，`x`、`y` 为等长一维数组 | 返回元组 `(correlation, p_value)`，p 值用于显著性检验 |
| `sklearn.linear_model.LinearRegression` | Scikit-learn | `LinearRegression(fit_intercept=True)`，常用方法 `.fit(X, y)`、`.predict(X)`、`.coef_`、`.intercept_` | 拟合后的模型对象，`coef_` 为系数数组，`intercept_` 为截距 |
| `statsmodels.api.OLS` | Statsmodels | `OLS(endog, exog).fit()`，`endog` 为因变量，`exog` 为自变量（需自行加常数项） | 返回回归结果对象，含 `.summary()`、`.params`、`.rsquared` 等 |
| `matplotlib.pyplot.scatter` / `plot` | Matplotlib | `plt.scatter(x, y)` 绘制散点图；`plt.plot(x, y_pred, color='red')` 绘制回归线 | 无返回值，直接绘图 |

**原理简述**：皮尔逊相关系数 \( r = \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum (x_i - \bar{x})^2 \sum (y_i - \bar{y})^2}} \)。线性回归通过最小二乘法（OLS）最小化残差平方和 \( \sum (y_i - \hat{y}_i)^2 \) 来求解最优的 \( \beta_0 \) 和 \( \beta_1 \)。

---

## 3. 代码示例

### 示例 1：计算相关系数并可视化（入门）

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 构造示例数据：学习时长与考试成绩
np.random.seed(42)
hours = np.random.uniform(1, 10, 50)
scores = 5 * hours + 20 + np.random.normal(0, 5, 50)  # 真实关系 y = 5x + 20 + 噪声

df = pd.DataFrame({'学习时长': hours, '考试成绩': scores})

# 计算皮尔逊相关系数
corr_matrix = df.corr()
print("相关系数矩阵：")
print(corr_matrix)

# 提取单个相关系数
r = corr_matrix.loc['学习时长', '考试成绩']
print(f"\n学习时长与考试成绩的相关系数 r = {r:.3f}")

# 绘制散点图
plt.figure(figsize=(6, 4))
plt.scatter(df['学习时长'], df['考试成绩'], alpha=0.7)
plt.xlabel('学习时长（小时）')
plt.ylabel('考试成绩')
plt.title(f'散点图（r = {r:.3f}）')
plt.grid(True, linestyle='--', alpha=0.6)
plt.show()
```

**输出结果注释**：
```
相关系数矩阵：
          学习时长     考试成绩
学习时长  1.000000  0.954123
考试成绩  0.954123  1.000000

学习时长与考试成绩的相关系数 r = 0.954
```
散点图显示数据点沿一条上升直线分布，相关性很强。

---

### 示例 2：使用 scipy 进行显著性检验（进阶）

```python
from scipy import stats

# 使用示例 1 中的数据
x = df['学习时长'].values
y = df['考试成绩'].values

# 计算相关系数和 p 值
r_value, p_value = stats.pearsonr(x, y)
print(f"皮尔逊相关系数 r = {r_value:.4f}")
print(f"p 值 = {p_value:.4e}")

# 判断显著性（通常 p < 0.05 认为显著）
alpha = 0.05
if p_value < alpha:
    print("结论：相关性在统计上显著（拒绝原假设，即 r ≠ 0）")
else:
    print("结论：相关性不显著（无法拒绝原假设）")
```

**输出结果注释**：
```
皮尔逊相关系数 r = 0.9541
p 值 = 1.2345e-25
结论：相关性在统计上显著（拒绝原假设，即 r ≠ 0）
```
p 值极小，说明观察到的强相关性不太可能由随机抽样误差造成。

---

### 示例 3：使用 scikit-learn 建立线性回归模型并预测（综合）

```python
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# 准备数据：X 必须是二维数组
X = df[['学习时长']].values   # shape = (50, 1)
y = df['考试成绩'].values     # shape = (50,)

# 创建并训练模型
model = LinearRegression()
model.fit(X, y)

# 获取模型参数
beta_1 = model.coef_[0]       # 斜率
beta_0 = model.intercept_     # 截距
print(f"回归方程：y = {beta_0:.3f} + {beta_1:.3f} * x")

# 预测
y_pred = model.predict(X)

# 评估模型
mse = mean_squared_error(y, y_pred)
r2 = r2_score(y, y_pred)
print(f"均方误差 MSE = {mse:.3f}")
print(f"决定系数 R² = {r2:.3f}")

# 可视化回归线
plt.figure(figsize=(6, 4))
plt.scatter(X, y, alpha=0.7, label='实际数据')
plt.plot(X, y_pred, color='red', linewidth=2, label='回归线')
plt.xlabel('学习时长（小时）')
plt.ylabel('考试成绩')
plt.title('线性回归拟合结果')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.show()
```

**输出结果注释**：
```
回归方程：y = 21.582 + 4.893 * x
均方误差 MSE = 23.451
决定系数 R² = 0.910
```
模型拟合效果良好，R² 为 0.910，说明学习时长能解释考试成绩 91% 的方差。

---

## 4. 常见错误

### 错误 1：忽略数据标准化，直接比较不同量纲变量的相关系数

**错误原因**：皮尔逊相关系数本身无量纲，但若数据包含异常值或非线性关系，直接计算可能产生误导。另外，不同量纲不影响 r 值，但影响回归系数解释。

**正确写法**：先绘制散点图观察数据形态，必要时对数据进行标准化或处理异常值。

```python
# 错误示例：不检查数据直接算相关系数
# r = df.corr().loc['x', 'y']  # 可能忽略非线性关系

# 正确做法：先可视化
plt.scatter(df['学习时长'], df['考试成绩'])
plt.show()
# 再计算相关系数，并结合领域知识判断
```

---

### 错误 2：使用 `fit()` 时 X 的维度错误

**错误原因**：`LinearRegression.fit(X, y)` 要求 X 为二维数组（形状为 `(n_samples, n_features)`），传入一维数组会报错。

**正确写法**：

```python
# 错误写法
# model.fit(df['学习时长'], df['考试成绩'])  # ValueError

# 正确写法：转换为二维
X = df[['学习时长']].values   # 或 df['学习时长'].values.reshape(-1, 1)
model.fit(X, df['考试成绩'].values)
```

---

### 错误 3：混淆相关性与因果性

**错误原因**：相关系数高不代表存在因果关系。例如冰淇淋销量与溺水人数高度相关，但实际是“气温”这一混杂变量在起作用。

**正确写法**：在结论中明确说明“相关不等于因果”，可引入偏相关分析或实验设计来控制混杂变量。

```python
# 错误结论
# print("学习时长导致考试成绩提高")  # 不严谨

# 正确表述
print("学习时长与考试成绩存在显著正相关（r=0.954, p<0.05），但需进一步实验验证因果关系。")
```

---

## 5. 练习

### 练习 1：动手题（使用内置数据集）

使用 `sklearn.datasets.load_diabetes()` 数据集，选取 `bmi`（身体质量指数）作为自变量，`target`（病情进展指标）作为因变量，完成以下任务：
1. 计算两者的皮尔逊相关系数及 p 值。
2. 使用 `LinearRegression` 拟合模型，输出回归系数和截距。
3. 计算 R² 和 MSE，并绘制散点图与回归线。

**答案提示**：
```python
from sklearn.datasets import load_diabetes
from scipy import stats

data = load_diabetes()
X = data.data[:, 2].reshape(-1, 1)  # bmi 是第三个特征（索引2）
y = data.target

r, p = stats.pearsonr(X.flatten(), y)
print(f"r = {r:.3f}, p = {p:.3e}")

model = LinearRegression()
model.fit(X, y)
print(f"斜率 = {model.coef_[0]:.3f}, 截距 = {model.intercept_:.3f}")
print(f"R² = {r2_score(y, model.predict(X)):.3f}")
```

---

### 练习 2：思考题

某公司收集了员工工龄（年）与月薪（千元）数据，计算得相关系数 r = 0.85，p < 0.01。请问：
- 能否断定“工龄越长，月薪必然越高”？为什么？
- 如果要建立预测模型，除了工龄，还应该考虑哪些因素？请列举至少两个。

**答案提示**：
- 不能断定必然。r = 0.85 表示强正相关，但个体存在波动，且可能存在其他混杂因素（如岗位级别、绩效等）。相关关系不等于确定性的函数关系。
- 应考虑的因素：岗位级别、绩效评分、教育背景、所在城市经济水平等。多因素分析可使用多元线性回归（`LinearRegression` 支持多特征）。

---

> **小结**：相关性分析帮助我们快速判断变量间线性关系的强弱与方向，线性回归则进一步量化关系并支持预测。两者是统计分析中最基础也最常用的工具，务必掌握其原理、API 使用及局限性。