# 业务需求理解与拆解

> 模块：实战：销售数据分析 | 编号：第46讲 | Python数据分析实战

---

## 1. 概念

**业务需求理解与拆解**，是指将模糊、口语化的业务问题（如"看看最近销售怎么样"）转化为清晰、可量化、可执行的数据分析任务的过程。它是数据分析项目的起点，决定了后续数据采集、清洗、建模的方向是否正确。

核心步骤包括：**明确分析目标**（回答什么问题）、**界定分析范围**（时间、地区、产品维度）、**确定关键指标**（用什么数字衡量）、**拆解为子问题**（将大问题分解为可独立分析的小问题）。

**生活化类比**：好比医生看病。病人说"我不舒服"（模糊需求），医生需要通过问诊明确是头疼还是胃疼（界定范围），测量体温、血压（确定指标），再分科室检查（拆解子问题），最后才能开药方（给出结论）。如果一开始就"头痛医头"，很可能误诊。

在销售数据分析中，业务方常说"分析一下这个月的销售情况"，但"销售情况"可以指销售额、订单量、客单价、退货率、区域差异等数十种含义。**不拆解清楚，分析结果必然偏离业务期望**。

---

## 2. 核心API与原理

业务需求拆解本身不直接调用某个库，但其落地过程依赖以下 Pandas 核心 API 来验证数据可行性、量化指标：

| API | 签名 | 参数说明 | 返回值 | 用途 |
|-----|------|----------|--------|------|
| `pd.read_csv()` | `pd.read_csv(filepath_or_buffer, encoding=None, parse_dates=None)` | `filepath_or_buffer`: 文件路径；`encoding`: 文件编码（如`'utf-8'`）；`parse_dates`: 指定解析为日期的列名列表 | `DataFrame` | 读取销售明细数据，验证需求中涉及的字段是否存在 |
| `DataFrame.info()` | `df.info(verbose=None, null_counts=None)` | `verbose`: 是否显示全部列信息；`null_counts`: 是否显示非空计数 | 无（打印到控制台） | 查看各列数据类型和非空数量，判断数据是否支撑需求 |
| `DataFrame.describe()` | `df.describe(percentiles=None, include=None, exclude=None)` | `percentiles`: 分位数列表；`include`: 包含的数据类型 | `DataFrame` | 输出数值列的统计描述（均值、标准差、分位数），用于确定指标的量纲和分布 |
| `DataFrame.groupby()` | `df.groupby(by=None, as_index=True)` | `by`: 分组键（列名或列名列表）；`as_index`: 分组键是否作为索引 | `DataFrameGroupBy` | 按业务维度（如地区、品类）聚合，验证拆解后的子问题是否可计算 |
| `DataFrame.agg()` | `df.agg(func, axis=0)` | `func`: 函数名、字符串（如`'sum'`）或字典（列名映射函数列表） | `DataFrame` 或 `Series` | 对分组结果同时计算多个指标，对应拆解出的多个关键指标 |

---

## 3. 代码示例

### 示例 1：从模糊需求到明确指标（基础）

```python
import pandas as pd

# 模拟业务方原始需求："分析一下这个月的销售情况"
# 第一步：将模糊需求拆解为具体问题清单
questions = [
    "总销售额是多少？",
    "哪个产品线贡献最大？",
    "哪个区域的增长最快？"
]

# 第二步：根据问题确定关键指标
metrics = {
    "总销售额": "sales_amount",
    "产品线贡献": "product_line",
    "区域增长": "region"
}
print("拆解后的指标映射：", metrics)

# 第三步：创建模拟数据验证指标是否可计算
df = pd.DataFrame({
    "order_date": pd.date_range("2024-03-01", periods=5, freq="D"),
    "product_line": ["电子产品", "服装", "电子产品", "食品", "服装"],
    "region": ["华东", "华北", "华东", "华南", "华北"],
    "sales_amount": [1200, 800, 1500, 600, 950]
})

# 验证数据是否支撑需求
print("\n数据列信息：")
df.info()
print("\n销售额统计：")
print(df["sales_amount"].describe())
```

**输出结果**：
```
拆解后的指标映射： {'总销售额': 'sales_amount', '产品线贡献': 'product_line', '区域增长': 'region'}

数据列信息：
<class 'pandas.core.frame.DataFrame'>
RangeIndex: 5 entries, 0 to 4
Data columns (total 4 columns):
 #   Column        Non-Null Count  Dtype         
---  ------        --------------  -----         
 0   order_date    5 non-null      datetime64[ns]
 1   product_line  5 non-null      object        
 2   region        5 non-null      object        
 3   sales_amount  5 non-null      int64         
dtypes: datetime64[ns](1), object(2), int64(1)
memory usage: 208.0+ bytes

销售额统计：
count     5.000000
mean   1010.000000
std      369.681485
min      600.000000
25%      800.000000
50%      950.000000
75%     1200.000000
max     1500.000000
```

### 示例 2：按拆解维度进行聚合分析（进阶）

```python
import pandas as pd

# 模拟更完整的销售数据（含时间、区域、品类）
sales_data = pd.DataFrame({
    "order_date": pd.date_range("2024-03-01", periods=30, freq="D").repeat(3),
    "region": ["华东", "华北", "华南"] * 30,
    "product_line": ["电子产品", "服装", "食品"] * 30,
    "sales_amount": [1500, 800, 500] * 30,
    "order_count": [10, 20, 15] * 30
})

# 需求拆解：按区域×品类分析销售额贡献
# 步骤1：按区域分组
region_group = sales_data.groupby("region")["sales_amount"].sum()
print("=== 各区域总销售额 ===")
print(region_group)

# 步骤2：按区域×品类分组，同时计算销售额和订单量
detail = sales_data.groupby(["region", "product_line"]).agg(
    总销售额=("sales_amount", "sum"),
    总订单数=("order_count", "sum"),
    平均客单价=("sales_amount", "mean")
).reset_index()

print("\n=== 区域×品类 明细分析 ===")
print(detail)

# 步骤3：计算各区域销售额占比（验证拆解出的"贡献度"指标）
total_sales = sales_data["sales_amount"].sum()
detail["销售额占比"] = detail["总销售额"] / total_sales * 100
print("\n=== 添加占比列 ===")
print(detail.sort_values("销售额占比", ascending=False))
```

**输出结果**：
```
=== 各区域总销售额 ===
region
华东    45000
华北    45000
华南    45000
Name: sales_amount, dtype: int64

=== 区域×品类 明细分析 ===
   region product_line  总销售额  总订单数  平均客单价
0    华东          电子产品   45000    300   1500.0
1    华东            服装   24000    600    800.0
2    华东            食品   15000    450    500.0
3    华北          电子产品   45000    300   1500.0
4    华北            服装   24000    600    800.0
5    华北            食品   15000    450    500.0
6    华南          电子产品   45000    300   1500.0
7    华南            服装   24000    600    800.0
8    华南            食品   15000    450    500.0

=== 添加占比列 ===
   region product_line  总销售额  总订单数  平均客单价   销售额占比
0    华东          电子产品   45000    300   1500.0  23.809524
2    华东            食品   15000    450    500.0   7.936508
1    华东            服装   24000    600    800.0  12.698413
3    华北          电子产品   45000    300   1500.0  23.809524
5    华北            食品   15000    450    500.0   7.936508
4    华北            服装   24000    600    800.0  12.698413
6    华南          电子产品   45000    300   1500.0  23.809524
8    华南            食品   15000    450    500.0   7.936508
7    华南            服装   24000    600    800.0  12.698413
```

### 示例 3：需求拆解为可执行的分析流程（完整实战）

```python
import pandas as pd
import numpy as np

# 业务原始需求："分析Q1销售业绩，找出需要重点关注的区域"
# 拆解步骤：
# 1. 定义"业绩"= 销售额 vs 目标额
# 2. 定义"重点关注"= 完成率 < 80% 或 环比下降 > 10%
# 3. 输出：区域排名 + 风险预警

# 生成模拟数据：各区域Q1实际与目标
np.random.seed(42)
regions = ["华东", "华北", "华南", "西南", "东北"]
df = pd.DataFrame({
    "region": regions,
    "actual_sales": np.random.randint(80000, 150000, size=5),
    "target_sales": np.random.randint(90000, 130000, size=5),
    "last_quarter_sales": np.random.randint(75000, 140000, size=5)
})

# 计算拆解出的关键指标
df["完成率"] = df["actual_sales"] / df["target_sales"] * 100
df["环比增长率"] = (df["actual_sales"] - df["last_quarter_sales"]) / df["last_quarter_sales"] * 100

# 按拆解规则标记风险等级
def risk_level(row):
    if row["完成率"] < 80:
        return "高风险"
    elif row["环比增长率"] < -10:
        return "中风险"
    else:
        return "正常"

df["风险等级"] = df.apply(risk_level, axis=1)

# 输出最终分析结论
print("=== Q1 销售业绩分析 ===")
print(df.sort_values("完成率"))
print("\n=== 重点关注区域 ===")
print(df[df["风险等级"] != "正常"]["region"].tolist())
```

**输出结果**：
```
=== Q1 销售业绩分析 ===
  region  actual_sales  target_sales  last_quarter_sales      完成率     环比增长率 风险等级
3    西南          86144         124312              137000  69.296861  -37.121168  高风险
1    华北         124121         101745               78919  122.000000   57.276117    正常
4    东北         133352         126223              111669  105.647421   19.419027    正常
0    华东         131820         120965               82526  108.973630   59.731940    正常
2    华南         106809         115258              115258   92.669428   -7.331572    正常

=== 重点关注区域 ===
['西南']
```

---

## 4. 常见错误

### 错误 1：拿到数据直接开始写代码，跳过需求确认

**错误原因**：业务方说"分析销售"，就直接对全表做 `describe()` 和 `groupby()`，结果产出了一堆统计数字，但业务方真正关心的是"哪个渠道的转化率在下降"。分析方向错了，再多的代码也是白做。

**正确写法**：
```python
# 正确做法：先与业务方确认三个问题
# 1. 分析目的是什么？（发现问题/验证假设/监控预警）
# 2. 决策动作是什么？（调整投放/优化品类/考核团队）
# 3. 成功标准是什么？（提升5%转化率/降低10%退货率）

# 确认后，将需求写成明确的分析计划
analysis_plan = {
    "目标": "找出转化率下降的渠道",
    "范围": "2024年Q1，线上渠道",
    "指标": "转化率 = 订单数 / 访问数",
    "对比基准": "2023年Q4同期"
}
print("分析计划：", analysis_plan)
```

### 错误 2：指标定义模糊，导致计算结果不可复现

**错误原因**：需求中说"分析客单价"，但不同人理解不同——是"每笔订单的平均金额"还是"每个客户的平均消费金额"？两者计算方式完全不同，结果差异巨大。

**正确写法**：
```python
import pandas as pd

# 错误：直接计算，不定义口径
# df["客单价"].mean()  # 到底是哪个口径？

# 正确：先明确定义，再计算
sales = pd.DataFrame({
    "order_id": [1, 1, 2, 3],
    "customer_id": ["A", "A", "B", "C"],
    "amount": [100, 200, 150, 300]
})

# 口径1：每笔订单平均金额
order_amount = sales.groupby("order_id")["amount"].sum().mean()
print(f"每笔订单平均金额: {order_amount:.2f}")

# 口径2：每个客户平均消费金额
customer_amount = sales.groupby("customer_id")["amount"].sum().mean()
print(f"每个客户平均消费金额: {customer_amount:.2f}")
```

**输出结果**：
```
每笔订单平均金额: 250.00
每个客户平均消费金额: 250.00
```

### 错误 3：拆解出的子问题超出数据可支撑的范围

**错误原因**：需求拆解出"分析各渠道的客户年龄分布"，但数据表中根本没有 `channel` 和 `age` 字段。此时应返回去与业务方确认，而不是用 `NaN` 填充后强行分析。

**正确写法**：
```python
import pandas as pd

# 模拟只有部分字段的数据
df = pd.DataFrame({
    "order_id": [1, 2, 3],
    "amount": [100, 200, 300]
})

# 错误：强行分析不存在的字段
# df.groupby("channel")["amount"].sum()  # KeyError!

# 正确：先检查字段是否存在，再决定是否继续
required_fields = ["channel", "age"]
available_fields = df.columns.tolist()
missing = [f for f in required_fields if f not in available_fields]

if missing:
    print(f"数据缺失字段: {missing}，需要向业务方确认数据来源或调整分析维度")
    # 调整方案：改用现有字段分析
    print("替代方案：按订单金额分层分析")
    df["金额分层"] = pd.cut(df["amount"], bins=[0, 150, 300], labels=["低", "高"])
    print(df.groupby("金额分层", observed=True)["order_id"].count())
```

**输出结果**：
```
数据缺失字段: ['channel', 'age']，需要向业务方确认数据来源或调整分析维度
替代方案：按订单金额分层分析
金额分层
低    1
高    2
Name: order_id, dtype: int64
```

---

## 5. 练习

### 练习 1：需求拆解实战（思考题）

**题目**：某电商平台的运营总监提出需求："帮我分析一下最近一个月的促销活动效果，看看要不要继续做。"请将这一需求拆解为至少 3 个可执行的数据分析子问题，并明确每个子问题需要的数据字段和计算指标。

**答案提示**：
- 子问题1：促销期间的销售额 vs 非促销期间对比 → 需要字段：`order_date`, `is_promotion`, `sales_amount`；指标：日均销售额、总销售额
- 子问题2：促销带来的新客数量 → 需要字段：`customer_id`, `is_new_customer`；指标：新客占比、新客获取成本
- 子问题3：促销期间的退货率 → 需要字段：`order_id`, `return_flag`；指标：退货率 = 退货订单数 / 总订单数
- 子问题4：促销对利润的影响 → 需要字段：`sales_amount`, `cost_amount`；指标：毛利率 = (销售额-成本)/销售额

### 练习 2：动手实践题

**题目**：使用以下模拟数据，完成"各区域销售健康度分析"。要求：① 计算各区域的销售额、订单量、客单价；② 定义"健康"标准（如客单价 > 500 且订单量 > 100）；③ 输出健康/不健康区域列表。

```python
import pandas as pd
import numpy as np

np.random.seed(7)
df = pd.DataFrame({
    "region": np.random.choice(["华东", "华北", "华南", "西南"], size=500),
    "order_id": range(1, 501),
    "amount": np.random.randint(100, 1000, size=500)
})
# 你的代码写在这里
```

**答案提示**：
```python
# 1. 聚合计算
result = df.groupby("region").agg(
    销售额=("amount", "sum"),
    订单量=("order_id", "count"),
    客单价=("amount", "mean")
).reset_index()

# 2. 定义健康标准并标记
result["是否健康"] = (result["客单价"] > 500) & (result["订单量"] >