# 时间序列处理

> 模块：Pandas数据处理(下) | 编号：第19讲 | Python数据分析实战

---

## 1. 概念

时间序列（Time Series）是指按时间顺序排列的一组数据点，例如每日股票收盘价、每小时气温记录、每月销售额等。在 Pandas 中，时间序列处理的核心是 **DatetimeIndex**——一种特殊的索引类型，它允许我们使用日期/时间字符串、`datetime` 对象或 `Timestamp` 对象来索引和切片数据。

时间序列分析广泛应用于金融（股价预测）、气象（温度趋势）、物联网（传感器数据）和商业（销售预测）等领域。Pandas 提供了从 **解析字符串日期**、**生成日期范围**、**重采样（resample）** 到 **滑动窗口计算** 的一整套工具，使时间序列的清洗、聚合和可视化变得高效。

**生活化类比**：把时间序列想象成一本按日期排列的日记。普通 DataFrame 像一本无序的相册，而 DatetimeIndex 则像日记本上的日历页——你可以直接翻到"3月15日"那一页，也可以快速统计"这个月写了多少篇"，还能按周或按月汇总内容。Pandas 就是这本智能日记的管理员。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `pd.to_datetime()` | `pd.to_datetime(arg, format=None, errors='raise')` | `arg`：待转换的字符串、列表或 Series；`format`：指定解析格式（如 `'%Y-%m-%d'`）；`errors`：错误处理策略（`'raise'`/`'coerce'`/`'ignore'`） | `DatetimeIndex` 或 `Series`（类型为 `datetime64[ns]`） |
| `pd.date_range()` | `pd.date_range(start=None, end=None, periods=None, freq='D')` | `start`/`end`：起始/结束日期；`periods`：生成数量；`freq`：频率（`'D'`天、`'H'`小时、`'M'`月末、`'T'`分钟等） | `DatetimeIndex` |
| `Series.resample()` | `Series.resample(rule, axis=0, closed=None, label=None)` | `rule`：重采样频率（如 `'M'`、`'W'`）；`closed`：区间闭合方向；`label`：聚合标签位置 | `DatetimeIndexResampler` 对象（可继续调用聚合方法如 `.mean()`、`.sum()`） |
| `Series.rolling()` | `Series.rolling(window, min_periods=None, center=False)` | `window`：窗口大小（整数或偏移量）；`min_periods`：最少有效观测数；`center`：是否居中 | `Rolling` 对象（可调用 `.mean()`、`.sum()` 等） |
| `DataFrame.shift()` | `DataFrame.shift(periods=1, freq=None, axis=0)` | `periods`：移动的周期数（正数向后移）；`freq`：使用时间频率移动索引 | 移动后的新 DataFrame/Series |

---

## 3. 代码示例

### 示例 1：解析日期字符串并建立时间索引（入门）

```python
import pandas as pd

# 原始数据：日期以字符串形式存储
data = {
    'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
    'sales': [120, 135, 98]
}
df = pd.DataFrame(data)

# 将字符串列转换为 datetime 类型，并设为索引
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')

print(df)
print("\n索引类型:", type(df.index))
# 输出：
#             sales
# date
# 2024-01-01    120
# 2024-01-02    135
# 2024-01-03     98
#
# 索引类型: <class 'pandas.core.indexes.datetimes.DatetimeIndex'>
```

### 示例 2：生成日期范围与重采样（进阶）

```python
import pandas as pd
import numpy as np

# 生成 2024 年 1 月每天的日期索引
idx = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
print("生成的天数:", len(idx))

# 模拟每日温度数据（随机生成）
np.random.seed(42)
temperature = np.random.randint(0, 30, size=len(idx))
ts = pd.Series(temperature, index=idx, name='temp')

# 按周重采样，计算每周平均温度
weekly_mean = ts.resample('W').mean()
print("\n每周平均温度：")
print(weekly_mean)
# 输出（部分）：
# 生成的天数: 31
#
# 每周平均温度：
# 2024-01-07    12.857143
# 2024-01-14    14.285714
# 2024-01-21    15.428571
# 2024-01-28    17.000000
# 2024-02-04    12.000000
# Freq: W-SUN, Name: temp, dtype: float64
```

### 示例 3：滑动窗口计算与滞后特征（进阶）

```python
import pandas as pd

# 创建 10 天的股票收盘价序列
dates = pd.date_range('2024-03-01', periods=10, freq='D')
prices = pd.Series([100, 102, 101, 105, 108, 107, 110, 112, 115, 114], index=dates, name='close')

# 计算 3 日移动平均线
ma3 = prices.rolling(window=3).mean()
print("3日移动平均线：")
print(ma3)
# 输出：
# 2024-03-01         NaN
# 2024-03-02         NaN
# 2024-03-03  101.000000
# 2024-03-04  102.666667
# 2024-03-05  104.666667
# 2024-03-06  106.666667
# 2024-03-07  108.333333
# 2024-03-08  109.666667
# 2024-03-09  112.333333
# 2024-03-10  113.666667
# Freq: D, Name: close, dtype: float64

# 创建滞后 1 天的特征（用于预测）
prices_lag1 = prices.shift(1)
print("\n滞后1天价格：")
print(prices_lag1.head(3))
# 输出：
# 2024-03-01    NaN
# 2024-03-02  100.0
# 2024-03-03  102.0
# Freq: D, Name: close, dtype: float64
```

---

## 4. 常见错误

### 错误 1：忘记将字符串转换为 datetime 类型就进行时间操作

```python
# 错误写法
df = pd.DataFrame({'date': ['2024-01-01', '2024-01-02'], 'val': [1, 2]})
# 直接这样写会报错：TypeError: string indices must be integers
# df.resample('M', on='date').sum()

# 正确写法
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')
result = df.resample('M').sum()
```

**原因**：`resample()` 要求索引必须是 `DatetimeIndex`，字符串索引无法识别时间频率。

### 错误 2：`to_datetime()` 遇到无法解析的格式直接报错

```python
# 错误写法
s = pd.Series(['2024/01/01', 'not-a-date', '2024-01-03'])
# pd.to_datetime(s)  # 直接抛异常 ValueError

# 正确写法：使用 errors='coerce' 将无效日期转为 NaT
s_clean = pd.to_datetime(s, errors='coerce')
print(s_clean)
# 输出：
# 0   2024-01-01
# 1          NaT
# 2   2024-01-03
# dtype: datetime64[ns]
```

**原因**：默认 `errors='raise'` 遇到非法格式会终止程序，实际数据处理中应容忍脏数据。

### 错误 3：`rolling()` 窗口大小误用字符串频率

```python
# 错误写法
prices = pd.Series([1, 2, 3, 4, 5], index=pd.date_range('2024-01-01', periods=5, freq='D'))
# prices.rolling('3D').mean()  # 如果索引不是等间隔，会报错或结果不符合预期

# 正确写法：等间隔索引下使用偏移量字符串
result = prices.rolling('3D').mean()
print(result)
# 输出：
# 2024-01-01    1.0
# 2024-01-02    1.5
# 2024-01-03    2.0
# 2024-01-04    3.0
# 2024-01-05    4.0
# Freq: D, dtype: float64
```

**原因**：字符串窗口（如 `'3D'`）基于时间偏移量，要求索引是等间隔的；若索引有缺失或不规则，应使用整数窗口。

---

## 5. 练习

### 练习 1：月度销售汇总

给定以下数据，请完成：① 将 `order_date` 转为 datetime 并设为索引；② 按月份汇总销售额（`amount`）总和；③ 计算每个月的环比增长率（即本月相对上月的增长百分比）。

```python
import pandas as pd

data = {
    'order_date': ['2024-01-15', '2024-01-28', '2024-02-03', '2024-02-19', '2024-03-01'],
    'amount': [200, 150, 300, 250, 400]
}
df = pd.DataFrame(data)
```

**答案提示**：
- 使用 `pd.to_datetime()` 转换后 `set_index()`；
- 用 `resample('M').sum()` 得到月度总额；
- 用 `.pct_change()` 计算环比增长率，注意首月为 `NaN`。

### 练习 2：滑动窗口异常检测

生成 30 天的随机数据（均值 50，标准差 5），计算 7 日滚动均值和滚动标准差。找出所有「当日值超过滚动均值 ± 2 倍滚动标准差」的异常点，并输出异常日期和数值。

**答案提示**：
- 用 `np.random.normal(50, 5, 30)` 生成数据；
- 用 `rolling(7).mean()` 和 `rolling(7).std()`；
- 用布尔索引筛选：`(ts > mean + 2*std) | (ts < mean - 2*std)`，注意前 6 天因窗口不足为 `NaN`，需用 `min_periods=1` 或丢弃。