# 缺失值检测与处理

> 模块：Pandas数据处理(上) | 编号：第14讲 | Python数据分析实战

---

## 1. 概念

缺失值（Missing Values）是指数据集中因未记录、采集失败或数据损坏等原因而空白的值，在 Pandas 中通常表示为 `NaN`（Not a Number）或 `None`。缺失值检测与处理是数据清洗的核心环节——原始数据中几乎不可避免地存在缺失，若不处理，轻则导致统计结果偏差，重则使机器学习模型无法训练。

**生活化类比**：把数据集想象成一张班级点名表。有些同学请假了（缺失值），点名册上对应位置是空的。你要么打电话问清楚补上（填充），要么在统计出勤率时把请假的人排除（删除），但绝不能把空位当作"0分"计入平均分（错误处理）。同理，数据分析时我们必须先"点名"找出缺失值，再决定是删除还是填充。

**适用场景**：数据探索前的质量检查、特征工程前的预处理、模型训练前的数据清洗，以及任何涉及聚合统计（如 `mean()`、`sum()`）的操作之前。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `isna()` | `DataFrame.isna()` | 无参数 | 返回同形状的布尔型 DataFrame，缺失位置为 `True` |
| `notna()` | `DataFrame.notna()` | 无参数 | `isna()` 的取反结果，非缺失位置为 `True` |
| `dropna()` | `DataFrame.dropna(*, axis=0, how='any', thresh=None, subset=None)` | `axis`：0 删除行，1 删除列；`how`：`'any'` 有任一缺失即删，`'all'` 全部缺失才删；`thresh`：保留至少 N 个非缺失值的行/列；`subset`：只在指定列/行中检测缺失 | 删除缺失后的新 DataFrame |
| `fillna()` | `DataFrame.fillna(value=None, *, method=None, axis=None, inplace=False, limit=None)` | `value`：填充值（标量或字典）；`method`：`'ffill'` 用前值填充，`'bfill'` 用后值填充；`limit`：连续填充的最大数量 | 填充后的新 DataFrame（若 `inplace=True` 则返回 `None`） |
| `interpolate()` | `DataFrame.interpolate(method='linear', *, axis=0, limit=None, inplace=False)` | `method`：插值方法，如 `'linear'` 线性插值、`'polynomial'` 多项式插值 | 插值填充后的新 DataFrame |

**原理说明**：Pandas 底层用 NumPy 的 `np.nan` 表示数值列的缺失，用 Python 的 `None` 表示对象列的缺失。`isna()` 会统一识别这两者。`dropna()` 本质是布尔索引过滤——先通过 `isna()` 生成掩码，再选取满足条件的行/列。`fillna()` 则是将掩码位置替换为指定值或前向/后向值。

---

## 3. 代码示例

### 示例 1：检测缺失值（入门）

```python
import pandas as pd
import numpy as np

# 创建包含缺失值的数据集
df = pd.DataFrame({
    '姓名': ['张三', '李四', '王五', '赵六'],
    '年龄': [25, np.nan, 30, 28],
    '薪资': [8000, 9500, np.nan, 12000],
    '部门': ['技术', '市场', None, '技术']
})

print("原始数据：")
print(df)
print("\n缺失值检测 isna()：")
print(df.isna())
print("\n每列缺失数量：")
print(df.isna().sum())
print("\n每行缺失数量：")
print(df.isna().sum(axis=1))

# 输出结果：
# 原始数据：
#    姓名   年龄     薪资   部门
# 0  张三  25.0   8000.0   技术
# 1  李四   NaN   9500.0   市场
# 2  王五  30.0      NaN  None
# 3  赵六  28.0  12000.0   技术
#
# 缺失值检测 isna()：
#       姓名     年龄     薪资    部门
# 0  False  False  False  False
# 1  False   True  False  False
# 2  False  False   True   True
# 3  False  False  False  False
#
# 每列缺失数量：
# 姓名    0
# 年龄    1
# 薪资    1
# 部门    1
# dtype: int64
```

### 示例 2：删除缺失值（进阶）

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'A': [1, 2, np.nan, 4],
    'B': [5, np.nan, np.nan, 8],
    'C': [9, 10, 11, 12]
})

print("原始数据：")
print(df)

# 删除含有任何缺失值的行（默认行为）
df_drop_any = df.dropna()
print("\ndropna() 默认删除含缺失的行：")
print(df_drop_any)

# 只删除全部为缺失值的行
df_drop_all = df.dropna(how='all')
print("\ndropna(how='all') 只删全缺失行：")
print(df_drop_all)

# 指定列检测缺失
df_drop_subset = df.dropna(subset=['A'])
print("\ndropna(subset=['A']) 只看A列是否有缺失：")
print(df_drop_subset)

# 保留至少2个非缺失值的行
df_thresh = df.dropna(thresh=2)
print("\ndropna(thresh=2) 保留至少2个非缺失值的行：")
print(df_thresh)

# 输出结果：
# 原始数据：
#      A    B   C
# 0  1.0  5.0   9
# 1  2.0  NaN  10
# 2  NaN  NaN  11
# 3  4.0  8.0  12
#
# dropna() 默认删除含缺失的行：
#      A    B   C
# 0  1.0  5.0   9
# 3  4.0  8.0  12
#
# dropna(how='all') 只删全缺失行：
#      A    B   C
# 0  1.0  5.0   9
# 1  2.0  NaN  10
# 2  NaN  NaN  11
# 3  4.0  8.0  12
#
# dropna(subset=['A']) 只看A列是否有缺失：
#      A    B   C
# 0  1.0  5.0   9
# 1  2.0  NaN  10
# 3  4.0  8.0  12
#
# dropna(thresh=2) 保留至少2个非缺失值的行：
#      A    B   C
# 0  1.0  5.0   9
# 1  2.0  NaN  10
# 3  4.0  8.0  12
```

### 示例 3：填充与插值（进阶）

```python
import pandas as pd
import numpy as np

# 模拟一周的每日温度（周三、周五缺失）
df = pd.DataFrame({
    '日期': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    '温度': [22, 24, np.nan, 23, np.nan, 27, 26]
})

print("原始数据：")
print(df)

# 方法1：用固定值填充（如平均值）
mean_temp = df['温度'].mean()
df_fill_mean = df.copy()
df_fill_mean['温度'] = df_fill_mean['温度'].fillna(mean_temp)
print(f"\n用均值 {mean_temp:.2f} 填充：")
print(df_fill_mean)

# 方法2：前向填充（用前一天的值）
df_ffill = df.copy()
df_ffill['温度'] = df_ffill['温度'].ffill()  # 等价于 fillna(method='ffill')
print("\n前向填充 ffill()：")
print(df_ffill)

# 方法3：线性插值
df_interp = df.copy()
df_interp['温度'] = df_interp['温度'].interpolate()
print("\n线性插值 interpolate()：")
print(df_interp)

# 输出结果：
# 原始数据：
#    日期   温度
# 0  周一  22.0
# 1  周二  24.0
# 2  周三   NaN
# 3  周四  23.0
# 4  周五   NaN
# 5  周六  27.0
# 6  周日  26.0
#
# 用均值 24.40 填充：
#    日期   温度
# 0  周一  22.00
# 1  周二  24.00
# 2  周三  24.40
# 3  周四  23.00
# 4  周五  24.40
# 5  周六  27.00
# 6  周日  26.00
#
# 前向填充 ffill()：
#    日期   温度
# 0  周一  22.0
# 1  周二  24.0
# 2  周三  24.0
# 3  周四  23.0
# 4  周五  23.0
# 5  周六  27.0
# 6  周日  26.0
#
# 线性插值 interpolate()：
#    日期   温度
# 0  周一  22.0
# 1  周二  24.0
# 2  周三  23.5
# 3  周四  23.0
# 4  周五  25.0
# 5  周六  27.0
# 6  周日  26.0
```

---

## 4. 常见错误

### 错误 1：用 `== np.nan` 判断缺失值

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({'A': [1, np.nan, 3]})

# 错误写法：np.nan != np.nan，永远返回 False
print(df['A'] == np.nan)   # 输出：0    False / 1    False / 2    False

# 正确写法：使用 isna()
print(df['A'].isna())      # 输出：0    False / 1     True / 2    False
```

**错误原因**：`np.nan` 是一个特殊的浮点数，它不等于自身（IEEE 754 标准规定 NaN 不参与比较）。因此 `==` 永远无法匹配到缺失值。

### 错误 2：在 `fillna()` 中忘记赋值

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({'A': [1, np.nan, 3]})

# 错误写法：fillna() 默认返回新对象，原 df 不变
df.fillna(0)
print(df)  # 输出：A 列仍有 NaN

# 正确写法1：接收返回值
df = df.fillna(0)

# 正确写法2：使用 inplace=True
df.fillna(0, inplace=True)
```

**错误原因**：Pandas 大多数方法默认返回新对象而非原地修改（`inplace` 参数默认 `False`），新手容易忘记接收返回值。

### 错误 3：对全缺失列使用 `dropna()` 后仍参与计算

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({'A': [1, 2, 3], 'B': [np.nan, np.nan, np.nan]})

# 错误写法：未删除全缺失列就计算均值
print(df.mean())  # 输出：A    2.0 / B    NaN —— B 列均值是 NaN

# 正确写法：先删除全缺失列
df_clean = df.dropna(axis=1, how='all')
print(df_clean.mean())  # 输出：A    2.0
```

**错误原因**：`dropna()` 默认 `axis=0`（删行），若要删除全缺失的列必须显式指定 `axis=1` 且 `how='all'`。否则全缺失列会继续污染后续统计结果。

---

## 5. 练习

### 练习 1：综合处理

给定以下销售数据，请完成：① 检测每列缺失数量；② 删除"销售额"列缺失的行；③ 对"销量"列的缺失值用该列中位数填充。

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    '产品': ['A', 'B', 'C', 'D', 'E'],
    '销量': [120, np.nan, 95, 150, np.nan],
    '销售额': [2400, 3100, np.nan, 4500, 5200]
})
```

**答案提示**：
```python
# ① 检测缺失
print(df.isna().sum())

# ② 删除销售额缺失的行
df = df.dropna(subset=['销售额'])

# ③ 中位数填充销量
median_sales = df['销量'].median()
df['销量'] = df['销量'].fillna(median_sales)
```

### 练习 2：思考题

某时间序列数据记录了每日股价，其中连续 3 天数据缺失。如果使用 `ffill()` 填充，会有什么问题？如果改用 `interpolate(method='linear')` 呢？在什么场景下你会选择 `dropna()` 而不是填充？

**答案提示**：`ffill()` 会用缺失前最后一天的价格填充这 3 天，导致股价看起来"横盘"，掩盖了真实的波动趋势；`interpolate()` 则会在前后已知值之间画一条直线，更接近真实走势。当缺失比例很低（如 <5%）且缺失是完全随机时，删除是安全且简单的选择；当缺失比例较高或缺失与业务含义相关时，应优先考虑填充。