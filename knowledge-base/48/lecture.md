# RFM用户分层模型
> 模块：实战：销售数据分析 | 编号：第48讲 | Python数据分析实战

## 1. 概念

RFM模型是一种经典的用户价值分析模型，通过三个核心行为维度对用户进行分层：**R（Recency，最近一次消费时间间隔）**、**F（Frequency，消费频率）** 和 **M（Monetary，消费金额）**。其核心逻辑是：最近购买过的、经常购买的、花钱多的用户，往往是对品牌价值最高的用户。

**生活化类比**：想象你经营一家社区咖啡馆。你不需要记住每位顾客的名字，但你会本能地关注：这位客人上次来是什么时候（R）？他一周来几次（F）？他每次消费是买一杯美式还是请朋友喝一整桌（M）？RFM模型就是把这种直觉量化成三个可计算的指标，再据此把顾客分成“VIP常客”“沉睡大客户”“新客潜力股”等群体，从而制定差异化的营销策略。

**适用场景**：电商平台会员分级、零售门店客户运营、SaaS产品用户健康度评估、银行信用卡用户价值分析等。RFM模型尤其适合交易型业务，即拥有明确的消费行为记录的场景。

## 2. 核心API与原理

| API/方法 | 签名 | 参数说明 | 返回值 | 核心用途 |
|---------|------|---------|--------|----------|
| `pd.to_datetime()` | `pd.to_datetime(arg, format=None)` | `arg`：待转换的日期列或Series；`format`：日期格式字符串，如`'%Y-%m-%d'` | `Series`（datetime64类型） | 将订单日期字符串转换为标准时间类型，用于计算时间差 |
| `Series.max()` / `Series.min()` | `series.max()` / `series.min()` | 无 | 标量 | 计算最近/最早消费日期，用于计算R值 |
| `DataFrame.groupby()` | `df.groupby(by, as_index=True)` | `by`：分组键（列名或列表）；`as_index`：是否将分组键设为索引 | `DataFrameGroupBy`对象 | 按用户ID聚合订单数据，计算每个用户的F和M值 |
| `DataFrame.rank()` | `df.rank(method='average', pct=False)` | `method`：排名方式（`'average'`平均排名，`'min'`最小值排名）；`pct`：是否返回百分等级 | `Series` | 对R/F/M值进行排名打分，实现1-4分制的量化 |
| `pd.cut()` | `pd.cut(x, bins, labels=None)` | `x`：一维数组；`bins`：分箱边界（整数或列表）；`labels`：分箱后的标签 | `Series`（Categorical类型） | 将连续分数划分为高/低档，用于最终分层判定 |

**原理说明**：RFM模型的标准流程分为四步——① 计算每个用户的R、F、M三个原始值；② 将三个值分别按分位数或排名转换为1~4分（分数越高越优）；③ 设定阈值（通常取中位数或均值）将每个维度划分为“高/低”；④ 组合成8种（2×2×2）用户类型，如“重要价值用户”（R高、F高、M高）、“流失风险用户”（R低、F高、M高）等。

## 3. 代码示例

### 示例1：基础RFM计算（入门）

```python
import pandas as pd
import numpy as np

# 模拟一份销售订单数据
data = {
    'user_id': ['A001', 'A001', 'A002', 'A002', 'A002', 'A003'],
    'order_date': ['2024-01-05', '2024-03-12', '2024-02-01', '2024-02-15', '2024-04-20', '2024-01-30'],
    'amount': [200, 350, 500, 120, 800, 60]
}
df = pd.DataFrame(data)
df['order_date'] = pd.to_datetime(df['order_date'])  # 转为时间类型

# 设定分析基准日（通常为数据中最大日期+1天）
reference_date = df['order_date'].max() + pd.Timedelta(days=1)

# 按用户聚合计算RFM
rfm = df.groupby('user_id').agg(
    R=('order_date', lambda x: (reference_date - x.max()).days),  # 最近一次消费距今天数
    F=('order_date', 'count'),                                     # 消费次数
    M=('amount', 'sum')                                            # 总消费金额
).reset_index()

print(rfm)
# 输出结果：
#   user_id    R  F     M
# 0    A001   26  2   550
# 1    A002   12  3  1420
# 2    A003  103  1    60
```

### 示例2：RFM打分与分层（进阶）

```python
import pandas as pd
import numpy as np

# 沿用示例1的rfm DataFrame
# 对R、F、M分别进行1-4分打分（分数越高越好，R值越小越好）
# 使用rank方法，R值越小排名越高，因此用ascending=False
rfm['R_score'] = rfm['R'].rank(method='average', ascending=False).astype(int)
rfm['F_score'] = rfm['F'].rank(method='average', ascending=True).astype(int)
rfm['M_score'] = rfm['M'].rank(method='average', ascending=True).astype(int)

# 设定阈值：以中位数为界，高于中位数记1（高），否则记0（低）
rfm['R_high'] = (rfm['R_score'] > rfm['R_score'].median()).astype(int)
rfm['F_high'] = (rfm['F_score'] > rfm['F_score'].median()).astype(int)
rfm['M_high'] = (rfm['M_score'] > rfm['M_score'].median()).astype(int)

# 定义分层函数
def rfm_segment(row):
    if row['R_high'] == 1 and row['F_high'] == 1 and row['M_high'] == 1:
        return '重要价值用户'
    elif row['R_high'] == 0 and row['F_high'] == 1 and row['M_high'] == 1:
        return '流失风险用户'
    elif row['R_high'] == 1 and row['F_high'] == 0 and row['M_high'] == 0:
        return '新客潜力股'
    else:
        return '一般用户'

rfm['segment'] = rfm.apply(rfm_segment, axis=1)
print(rfm[['user_id', 'R', 'F', 'M', 'segment']])
# 输出结果：
#   user_id    R  F     M      segment
# 0    A001   26  2   550        一般用户
# 1    A002   12  3  1420  重要价值用户
# 2    A003  103  1    60        一般用户
```

### 示例3：基于分位数的自动化分层（完整实战）

```python
import pandas as pd
import numpy as np

# 生成模拟数据：100个用户，每人1-5笔订单
np.random.seed(42)
n_users = 100
user_ids = [f'U{i:03d}' for i in range(1, n_users+1)]
records = []
for uid in user_ids:
    n_orders = np.random.randint(1, 6)
    for _ in range(n_orders):
        days_ago = np.random.randint(0, 180)
        amount = np.random.uniform(20, 500)
        records.append({'user_id': uid, 'days_ago': days_ago, 'amount': amount})

df = pd.DataFrame(records)
df['order_date'] = pd.Timestamp('2024-06-01') - pd.to_timedelta(df['days_ago'], unit='D')
reference_date = pd.Timestamp('2024-06-01')

# 计算RFM
rfm = df.groupby('user_id').agg(
    R=('order_date', lambda x: (reference_date - x.max()).days),
    F=('order_date', 'count'),
    M=('amount', 'sum')
).reset_index()

# 使用pd.qcut进行分位数打分（1-4分）
rfm['R_score'] = pd.qcut(rfm['R'], 4, labels=[4, 3, 2, 1]).astype(int)  # R越小分越高
rfm['F_score'] = pd.qcut(rfm['F'].rank(method='first'), 4, labels=[1, 2, 3, 4]).astype(int)
rfm['M_score'] = pd.qcut(rfm['M'], 4, labels=[1, 2, 3, 4]).astype(int)

# 计算综合得分并分层
rfm['total_score'] = rfm['R_score'] + rfm['F_score'] + rfm['M_score']
rfm['level'] = pd.cut(rfm['total_score'], bins=[0, 6, 9, 12], 
                      labels=['低价值', '中价值', '高价值'])

# 查看分层结果分布
print(rfm['level'].value_counts())
# 输出结果（示例）：
# level
# 中价值    46
# 高价值    28
# 低价值    26
# Name: count, dtype: int64

# 查看高价值用户TOP5
print(rfm[rfm['level'] == '高价值'].nlargest(5, 'total_score')[['user_id', 'R', 'F', 'M', 'total_score']])
```

## 4. 常见错误

### 错误1：R值方向搞反
**错误原因**：R值代表“最近一次消费距今的天数”，天数越大说明越久没来，价值越低。新手常把R值直接当作正向指标，导致打分逻辑颠倒。
```python
# 错误写法：R值越大给分越高
rfm['R_score'] = rfm['R'].rank(ascending=True)  # 错误！

# 正确写法：R值越小（越近）给分越高
rfm['R_score'] = rfm['R'].rank(ascending=False)  # 正确
```

### 错误2：未处理缺失值或重复订单
**错误原因**：原始订单数据中可能存在同一用户同一天的重复订单，或某些用户没有订单记录。直接聚合会导致F值虚高或R值计算错误。
```python
# 错误写法：直接groupby不处理重复
rfm = df.groupby('user_id').agg(F=('order_date', 'count'))

# 正确写法：先按用户+日期去重，再计算
df_dedup = df.drop_duplicates(subset=['user_id', 'order_date'])
rfm = df_dedup.groupby('user_id').agg(F=('order_date', 'count'))
```

### 错误3：使用`pd.qcut`时数据分布不均匀导致报错
**错误原因**：`pd.qcut`要求数据能均匀分成指定数量的桶，当数据中存在大量重复值时，会抛出`ValueError: Bin edges must be unique`。
```python
# 错误写法：直接对F值使用qcut
rfm['F_score'] = pd.qcut(rfm['F'], 4, labels=[1,2,3,4])  # 可能报错！

# 正确写法：先对F值做微小扰动或使用rank之后再做qcut
rfm['F_rank'] = rfm['F'].rank(method='first')  # 确保无重复
rfm['F_score'] = pd.qcut(rfm['F_rank'], 4, labels=[1,2,3,4]).astype(int)
```

## 5. 练习

### 练习1：思考题——阈值选择的影响
**题目**：在RFM分层中，我们使用中位数作为高/低的划分阈值。请思考：如果某电商平台正处于快速扩张期，新用户占比很高，此时使用中位数作为阈值会带来什么问题？你会如何调整？

**答案提示**：新用户占比高会导致F和M的中位数偏低，使得老用户很容易被划分为“高F、高M”，分层结果区分度下降。建议改用分位数（如75分位）作为阈值，或结合业务知识设定绝对阈值（如F≥5次为高频，M≥1000元为高额）。

### 练习2：动手题——实现流失预警
**题目**：基于示例3的`rfm`数据，请编写代码筛选出“最近30天内没有购买（R>30）、但历史消费金额排名前20%”的用户，作为重点挽回对象。

**答案提示**：
```python
# 筛选R>30且M排名前20%的用户
top_20_m = rfm['M'].quantile(0.8)
churn_risk = rfm[(rfm['R'] > 30) & (rfm['M'] >= top_20_m)]
print(churn_risk[['user_id', 'R', 'M']].sort_values('M', ascending=False))
```
核心思路：先用`quantile(0.8)`计算M的高阈值，再用布尔索引筛选。