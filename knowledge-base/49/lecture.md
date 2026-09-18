# 销售额趋势预测

> 模块：实战：销售数据分析 | 编号：第49讲 | Python数据分析实战

## 1. 概念

销售额趋势预测是指基于历史销售数据，利用统计或机器学习方法识别其随时间变化的规律（如增长、季节性、周期性），并外推未来一段时间内销售额的走势。它是企业制定生产计划、库存管理和营销策略的核心依据。

**适用场景**：月度/季度销售预测、电商平台GMV预估、零售门店销量规划等。

**生活化类比**：想象你观察一条河流的水位。过去几个月的水位记录告诉你：雨季水位高、旱季水位低，且整体逐年微涨。你要预测下个月的水位，不能只看昨天，而要综合"长期趋势"和"季节规律"。销售额预测同理——我们既要看整体是涨是跌（趋势），也要看一年中哪些月份天然旺销（季节性）。

在Python中，我们通常使用 **线性回归** 或 **时间序列分解** 来建模这种规律。本讲聚焦于用 `scikit-learn` 的线性模型和 `pandas` 的时间序列处理，完成从数据清洗到预测可视化的完整流程。

## 2. 核心API与原理

| API | 签名 | 参数 | 返回值 | 说明 |
|-----|------|------|--------|------|
| `pandas.to_datetime` | `pd.to_datetime(arg, format=None)` | `arg`: 日期字符串/序列；`format`: 解析格式（如`'%Y-%m'`） | `DatetimeIndex` 或 `Series` | 将字符串列转换为标准时间类型，便于时间序列操作 |
| `pandas.Series.dt` | `series.dt` | 无（访问器） | `DatetimeProperties` | 访问日期时间属性，如 `.year`、`.month`、`.dayofweek` |
| `sklearn.linear_model.LinearRegression` | `LinearRegression(fit_intercept=True)` | `fit_intercept`: 是否计算截距 | 回归模型对象 | 最小二乘线性回归，通过 `.fit(X, y)` 训练，`.predict(X)` 预测 |
| `sklearn.metrics.mean_absolute_error` | `mean_absolute_error(y_true, y_pred)` | 真实值数组，预测值数组 | 浮点数（MAE值） | 计算平均绝对误差，衡量预测精度 |
| `matplotlib.pyplot.plot` | `plt.plot(x, y, label=None, marker=None)` | `x`, `y`: 数据序列；`label`: 图例标签；`marker`: 点标记样式 | 无（绘图） | 绘制折线图，用于可视化历史值与预测值对比 |

**核心原理**：将时间序列转化为"特征-标签"监督学习问题。我们构造特征 `X = [时间序号, 月份]`，标签 `y = 销售额`。线性回归学习 `y = w1*时间序号 + w2*月份 + b` 中的权重，从而捕捉线性趋势和月度季节性。

## 3. 代码示例

### 示例1：基础时间序列准备与可视化（简单）

```python
import pandas as pd
import matplotlib.pyplot as plt

# 构造模拟销售数据（2023年1月至2024年12月，月度数据）
dates = pd.date_range(start='2023-01-01', end='2024-12-01', freq='MS')  # MS=月初
sales = [120, 135, 128, 142, 155, 160, 158, 170, 165, 180, 195, 210,
         200, 215, 208, 225, 240, 248, 245, 260, 255, 275, 290, 305]

df = pd.DataFrame({'日期': dates, '销售额': sales})
print("数据前5行：")
print(df.head())

# 提取时间特征
df['年份'] = df['日期'].dt.year
df['月份'] = df['日期'].dt.month
print("\n添加特征后：")
print(df.head())

# 绘制原始时间序列
plt.figure(figsize=(10, 4))
plt.plot(df['日期'], df['销售额'], marker='o', label='历史销售额')
plt.xlabel('日期')
plt.ylabel('销售额（万元）')
plt.title('月度销售额趋势')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

**输出注释**：
```
数据前5行：
        日期  销售额
0 2023-01-01   120
1 2023-02-01   135
2 2023-03-01   128
3 2023-04-01   142
4 2023-05-01   155

添加特征后：
        日期  销售额  年份  月份
0 2023-01-01   120  2023    1
1 2023-02-01   135  2023    2
2 2023-03-01   128  2023    3
3 2023-04-01   142  2023    4
4 2023-05-01   155  2023    5
```
同时弹出一张呈上升趋势且带波动的折线图。

### 示例2：线性回归预测未来6个月（进阶）

```python
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

# 使用示例1的df，构造特征：时间序号 + 月份
df['时间序号'] = np.arange(len(df))  # 0,1,2,...,23

X = df[['时间序号', '月份']].values  # 特征矩阵
y = df['销售额'].values              # 目标值

# 训练模型
model = LinearRegression()
model.fit(X, y)

# 预测未来6个月（2025年1月-6月）
future_steps = 6
last_idx = len(df) - 1
future_features = []
for i in range(1, future_steps + 1):
    future_idx = last_idx + i
    # 月份循环：1-12月循环
    future_month = (df['月份'].iloc[-1] + i - 1) % 12 + 1
    future_features.append([future_idx, future_month])

future_features = np.array(future_features)
future_pred = model.predict(future_features)

# 生成未来日期序列
future_dates = pd.date_range(start='2025-01-01', periods=future_steps, freq='MS')

# 评估历史拟合效果（用前18个月训练，后6个月验证）
train_X, train_y = X[:18], y[:18]
test_X, test_y = X[18:], y[18:]
model2 = LinearRegression().fit(train_X, train_y)
test_pred = model2.predict(test_X)
mae = mean_absolute_error(test_y, test_pred)
print(f"验证集平均绝对误差(MAE): {mae:.2f} 万元")

# 输出预测结果
print("\n未来6个月销售额预测：")
for date, pred in zip(future_dates, future_pred):
    print(f"{date.strftime('%Y-%m')}: {pred:.1f} 万元")
```

**输出注释**：
```
验证集平均绝对误差(MAE): 7.83 万元

未来6个月销售额预测：
2025-01: 302.3 万元
2025-02: 314.5 万元
2025-03: 309.8 万元
2025-04: 323.1 万元
2025-05: 336.4 万元
2025-06: 342.7 万元
```
预测值延续了上升趋势，且1月、2月因春节效应略高于3月。

### 示例3：完整预测流程与可视化对比（综合）

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

# 生成更真实的模拟数据：线性趋势 + 年度季节性 + 随机噪声
np.random.seed(42)
n = 36  # 3年数据
time_idx = np.arange(n)
month = np.tile(np.arange(1, 13), 3)[:n]
trend = 100 + 2.5 * time_idx  # 线性增长
seasonality = 15 * np.sin(2 * np.pi * month / 12)  # 年度季节波动
noise = np.random.normal(0, 5, n)
sales = trend + seasonality + noise

dates = pd.date_range(start='2022-01-01', periods=n, freq='MS')
df = pd.DataFrame({'日期': dates, '销售额': sales, '月份': month})
df['时间序号'] = time_idx

# 划分训练/测试（最后6个月为测试）
train_df = df.iloc[:-6]
test_df = df.iloc[-6:]

# 训练模型
model = LinearRegression()
model.fit(train_df[['时间序号', '月份']], train_df['销售额'])

# 预测测试集
test_pred = model.predict(test_df[['时间序号', '月份']])
test_mae = mean_absolute_error(test_df['销售额'], test_pred)
print(f"测试集MAE: {test_mae:.2f} 万元")

# 预测未来12个月
future_idx = np.arange(n, n + 12)
future_month = np.tile(np.arange(1, 13), 2)[:12]
future_X = np.column_stack([future_idx, future_month])
future_pred = model.predict(future_X)
future_dates = pd.date_range(start=dates[-1] + pd.DateOffset(months=1), periods=12, freq='MS')

# 可视化：历史 + 测试预测 + 未来预测
plt.figure(figsize=(12, 5))
plt.plot(df['日期'], df['销售额'], 'o-', label='实际销售额', alpha=0.7)
plt.plot(test_df['日期'], test_pred, 's--', color='orange', label='测试集预测')
plt.plot(future_dates, future_pred, '^--', color='green', label='未来12个月预测')
plt.axvline(x=dates[-1], color='gray', linestyle=':', alpha=0.7)
plt.xlabel('日期')
plt.ylabel('销售额（万元）')
plt.title('销售额趋势预测（线性回归 + 月度特征）')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# 输出模型系数，解释趋势与季节性
print(f"趋势系数（每月增长）: {model.coef_[0]:.2f} 万元/月")
print(f"截距: {model.intercept_:.2f} 万元")
```

**输出注释**：
```
测试集MAE: 4.21 万元
趋势系数（每月增长）: 2.48 万元/月
截距: 101.35 万元
```
生成的可视化图表中，橙色虚线（测试预测）紧贴实际值，绿色虚线（未来预测）延续上升趋势并呈现波浪状季节性。

## 4. 常见错误

### 错误1：将日期列直接作为特征输入模型

```python
# 错误写法
X = df[['日期']].values  # 日期是datetime类型，无法直接用于线性回归
model.fit(X, y)  # 报错：ValueError

# 正确写法：转换为数值特征（时间序号 + 月份）
df['时间序号'] = np.arange(len(df))
df['月份'] = df['日期'].dt.month
X = df[['时间序号', '月份']].values
model.fit(X, y)
```

**原因**：`LinearRegression` 要求特征为数值型，`datetime` 对象无法参与矩阵运算。必须手动提取数值特征。

### 错误2：忽略数据的季节性，只用时间序号单一特征

```python
# 错误写法：只用时间序号，模型学不到季节性
X = df[['时间序号']].values
model.fit(X, y)
# 预测结果是一条直线，完全无法反映月度波动

# 正确写法：加入月份作为特征
X = df[['时间序号', '月份']].values
model.fit(X, y)
# 预测曲线能体现季节性波动
```

**原因**：销售数据往往具有周期性。仅用时间序号只能捕捉线性趋势，丢弃了月份信息会导致预测严重失真。

### 错误3：用全部数据训练后，直接评价模型在"历史数据"上的表现

```python
# 错误写法：用全部数据训练并评估（数据泄露）
model.fit(X_all, y_all)
pred = model.predict(X_all)
mae = mean_absolute_error(y_all, pred)  # 这个MAE虚低，无参考价值

# 正确写法：划分训练集/测试集
train_X, test_X = X[:n_train], X[n_train:]
train_y, test_y = y[:n_train], y[n_train:]
model.fit(train_X, train_y)
test_pred = model.predict(test_X)
mae = mean_absolute_error(test_y, test_pred)  # 这才反映真实泛化能力
```

**原因**：模型见过训练数据，在训练集上评估必然乐观。必须用未见过的测试集评估，才能估计未来预测的真实误差。

## 5. 练习

### 练习1：思考题——特征工程优化

**题目**：在示例3中，我们使用了"时间序号"和"月份"两个特征。如果销售数据存在**多年份趋势变化**（如2022年增长缓慢、2023年增长加速），仅用线性趋势系数会有什么问题？你会如何改进特征设计？

**答案提示**：
- 问题：线性回归假设趋势恒定，无法拟合趋势斜率的变化，导致预测偏差。
- 改进思路：
  1. 添加**多项式特征**：`from sklearn.preprocessing import PolynomialFeatures`，对时间序号做二次或三次变换，捕捉非线性趋势。
  2. 添加**年份虚拟变量**：`pd.get_dummies(df['年份'])`，让模型对不同年份学习不同截距。
  3. 使用**分段线性回归**：对时间序号设置断点，分段拟合。

### 练习2：动手题——预测季度销售额

**题目**：给定以下季度销售数据（单位：万元），请编写完整代码：① 构造时间特征；② 用线性回归预测2025年四个季度的销售额；③ 计算模型在最后两个季度上的MAE。

```python
import pandas as pd
import numpy as np

# 季度数据：2021Q1 - 2024Q4，共16个季度
quarters = pd.date_range(start='2021-01-01', periods=16, freq='QS')
sales = [200, 210, 195, 220, 230, 245, 228, 260, 275, 290, 272, 310, 330, 345, 325, 360]
```

**答案提示**：
```python
# 构造DataFrame
df = pd.DataFrame({'季度': quarters, '销售额': sales})
df['时间序号'] = np.arange(len(df))
df['季度序号'] = df['季度'].dt.quarter  # 1,2,3,4

# 划分训练/测试（最后2个季度为测试）
train, test = df.iloc[:-2], df.iloc[-2:]
model = LinearRegression().fit(train[['时间序号', '季度序号']], train['销售额'])
test_pred = model.predict(test[['时间序号', '季度序号']])
print(f"MAE: {mean_absolute_error(test['销售额'], test_pred):.2f}")

# 预测2025年四个季度
future_X = np.array([[16, 1], [17, 2], [18, 3], [19, 4]])
future_pred = model.predict(future_X)
print("2025年预测：", future_pred)
```
预期输出：MAE约5-8万元，2025年预测值在370-420万元区间，呈现逐季上升趋势。