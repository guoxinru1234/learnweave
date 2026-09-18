# 重复值检测与去重策略

> 模块：数据清洗实战 | 编号：第21讲 | Python数据分析实战

---

## 1. 概念

**重复值**（Duplicate Values）是指数据集中完全一致或部分关键字段一致的多条记录。在数据分析中，重复值会夸大统计指标（如均值、总和），导致模型过拟合或业务决策失误。重复值检测与去重是数据清洗的核心环节，常见于用户行为日志、订单记录、传感器采集等场景。

**生活化类比**：想象你在整理一箱名片——同一人递了两次名片，内容完全一样；另一个人换了手机号但姓名职位没变。前者是"完全重复"（整行一致），后者是"部分重复"（关键字段一致）。去重就像整理名片时，既要扔掉完全相同的多余卡片，也要决定"换号的老客户"该合并成一张还是保留两张。

**适用场景**：
- 多源数据合并后（如CRM系统与Excel导出表拼接）
- ETL管道中上游任务重复执行
- 用户点击流日志中同一事件被多次记录

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 | 原理说明 |
|-----|------|----------|--------|----------|
| `DataFrame.duplicated()` | `duplicated(subset=None, keep='first')` | `subset`：指定判断重复的列名列表（默认所有列）；`keep`：标记重复的方式（`'first'`保留第一个，其余标True；`'last'`保留最后一个；`False`所有重复标True） | `Series[bool]`，长度与行数相同 | 逐行比较，基于哈希算法判断行是否与之前出现的行相同 |
| `DataFrame.drop_duplicates()` | `drop_duplicates(subset=None, keep='first', inplace=False, ignore_index=False)` | `subset`同上；`keep`同上；`inplace`是否原地修改；`ignore_index`是否重置索引 | 去重后的`DataFrame`（或`None`若`inplace=True`） | 先用`duplicated()`生成布尔掩码，再筛选保留的行 |
| `Series.duplicated()` | `duplicated(keep='first')` | `keep`同上 | `Series[bool]` | 单列版本的重复检测 |
| `DataFrame.any()` | `any(axis=0)` | `axis`：0为列方向，1为行方向 | `Series[bool]`或`bool` | 与`duplicated()`组合，快速判断是否存在任何重复行 |

**核心原理**：Pandas 对每一行计算哈希值（基于列值），通过哈希表记录已出现的行。`keep`参数控制当遇到重复时，哪一行被视为"非重复"（即保留哪一行）。时间复杂度为 O(n)，空间复杂度为 O(唯一行数)。

---

## 3. 代码示例

### 示例1：基础完全重复检测与去重

```python
import pandas as pd

# 构造含重复值的数据
df = pd.DataFrame({
    '用户ID': [101, 102, 101, 103, 102],
    '姓名': ['张三', '李四', '张三', '王五', '李四'],
    '年龄': [28, 35, 28, 42, 35]
})
print("原始数据：")
print(df)

# 检测完全重复行（整行一致）
duplicate_mask = df.duplicated()
print("\n重复标记（keep='first'）：")
print(duplicate_mask)

# 去重，保留第一次出现的行
df_clean = df.drop_duplicates()
print("\n去重后数据：")
print(df_clean)
print(f"去重后行数：{len(df_clean)}（原{len(df)}行）")

# 输出结果：
# 原始数据：
#    用户ID  姓名  年龄
# 0    101  张三  28
# 1    102  李四  35
# 2    101  张三  28
# 3    103  王五  42
# 4    102  李四  35
#
# 重复标记（keep='first'）：
# 0    False
# 1    False
# 2     True
# 3    False
# 4     True
# dtype: bool
#
# 去重后数据：
#    用户ID  姓名  年龄
# 0    101  张三  28
# 1    102  李四  35
# 3    103  王五  42
# 去重后行数：3（原5行）
```

### 示例2：基于关键字段的部分重复检测

```python
import pandas as pd

# 模拟订单数据：同一用户可能重复下单，但订单号唯一
orders = pd.DataFrame({
    '订单号': ['A001', 'A002', 'A003', 'A004', 'A005'],
    '用户ID': [1, 2, 1, 3, 2],
    '商品': ['手机', '电脑', '手机', '平板', '电脑'],
    '金额': [5000, 8000, 5000, 3000, 8000]
})

# 场景：只想基于"用户ID+商品"判断重复（同一用户买同一商品视为重复）
dup_subset = orders.duplicated(subset=['用户ID', '商品'], keep='first')
print("基于用户ID+商品的重复标记：")
print(dup_subset)

# 去重：保留每个用户每种商品的第一条记录
orders_dedup = orders.drop_duplicates(subset=['用户ID', '商品'], keep='first')
print("\n去重后（保留首条）：")
print(orders_dedup)

# 若想保留最后一条记录
orders_dedup_last = orders.drop_duplicates(subset=['用户ID', '商品'], keep='last')
print("\n去重后（保留末条）：")
print(orders_dedup_last)

# 输出结果：
# 基于用户ID+商品的重复标记：
# 0    False
# 1    False
# 2     True
# 3    False
# 4     True
# dtype: bool
#
# 去重后（保留首条）：
#    订单号  用户ID  商品    金额
# 0  A001     1   手机  5000
# 1  A002     2   电脑  8000
# 3  A004     3   平板  3000
#
# 去重后（保留末条）：
#    订单号  用户ID  商品    金额
# 2  A003     1   手机  5000
# 3  A004     3   平板  3000
# 4  A005     2   电脑  8000
```

### 示例3：进阶——去重统计与业务规则结合

```python
import pandas as pd
import numpy as np

# 模拟含缺失值和重复值的销售数据
sales = pd.DataFrame({
    '日期': ['2024-01-01', '2024-01-01', '2024-01-02', '2024-01-02', '2024-01-03'],
    '门店': ['A', 'A', 'B', 'B', 'A'],
    '销售额': [1000, 1000, 1500, np.nan, 1200]
})

print("原始数据：")
print(sales)

# 1. 检查是否存在任何重复行
has_dup = sales.duplicated().any()
print(f"\n是否存在完全重复行：{has_dup}")

# 2. 统计重复行数量
dup_count = sales.duplicated().sum()
print(f"重复行数量：{dup_count}")

# 3. 业务规则：先填充缺失值再去重（避免因NaN导致去重失效）
sales_filled = sales.fillna({'销售额': 0})  # 用0填充缺失
sales_final = sales_filled.drop_duplicates(subset=['日期', '门店'], keep='first')

print("\n处理后的数据：")
print(sales_final)

# 4. 去重后重置索引，便于后续操作
sales_final = sales_final.reset_index(drop=True)
print("\n重置索引后：")
print(sales_final)

# 输出结果：
# 原始数据：
#          日期 门店     销售额
# 0  2024-01-01   A  1000.0
# 1  2024-01-01   A  1000.0
# 2  2024-01-02   B  1500.0
# 3  2024-01-02   B     NaN
# 4  2024-01-03   A  1200.0
#
# 是否存在完全重复行：True
# 重复行数量：1
#
# 处理后的数据：
#          日期 门店     销售额
# 0  2024-01-01   A  1000.0
# 2  2024-01-02   B  1500.0
# 4  2024-01-03   A  1200.0
#
# 重置索引后：
#          日期 门店     销售额
# 0  2024-01-01   A  1000.0
# 1  2024-01-02   B  1500.0
# 2  2024-01-03   A  1200.0
```

---

## 4. 常见错误

### 错误1：忽略 `subset` 参数导致误删

**错误代码**：
```python
# 只想按用户ID去重，但未指定subset，导致整行完全一致才去重
df = pd.DataFrame({'用户ID': [1, 1, 2], '购买日期': ['2024-01-01', '2024-01-02', '2024-01-01']})
df_clean = df.drop_duplicates()  # 结果：3行全保留，因为日期不同
```

**错误原因**：`drop_duplicates()` 默认对所有列进行完全匹配，未指定 `subset` 时无法实现"按某列去重"。

**正确写法**：
```python
df_clean = df.drop_duplicates(subset=['用户ID'], keep='first')
# 结果：保留用户ID为1的第一条，共2行
```

### 错误2：`keep` 参数使用错误类型

**错误代码**：
```python
# 想保留所有重复行中的最后一条，但传了字符串"last"而非布尔值
df.drop_duplicates(keep='last')  # 正确用法
# 但新手可能写成：
df.drop_duplicates(keep=True)  # 错误！True等价于'first'，且会保留第一个
```

**错误原因**：`keep` 参数接受 `'first'`、`'last'` 或 `False`（布尔值），不接受 `True`。`True` 会被解释为 `'first'`，导致行为与预期不符。

**正确写法**：
```python
df.drop_duplicates(keep='last')   # 保留最后一条
df.drop_duplicates(keep=False)    # 删除所有重复行（一条都不留）
```

### 错误3：未处理缺失值导致去重失效

**错误代码**：
```python
# 数据中包含NaN，直接去重时NaN与NaN被视为相等，但业务上可能不应相等
df = pd.DataFrame({'A': [1, 1, np.nan, np.nan], 'B': [2, 2, 3, 3]})
df_clean = df.drop_duplicates()  # 结果：2行（1,2）和（NaN,3）各保留一条
# 但若业务上NaN代表"未知"，不同行的NaN可能代表不同实体
```

**错误原因**：Pandas 将 `NaN` 视为相等的值，因此含 `NaN` 的行会被判定为重复。这在某些场景（如缺失值表示不同含义）下会导致误删。

**正确写法**：
```python
# 先填充缺失值，再按业务规则去重
df_filled = df.fillna({'A': -999, 'B': -999})  # 用哨兵值填充
df_clean = df_filled.drop_duplicates()
# 或者：如果业务上NaN表示不同实体，先分组再处理
df_clean = df.drop_duplicates(subset=['B'])  # 只按B列去重，避免NaN干扰
```

---

## 5. 练习

### 练习1：多列组合去重与统计

给定一个用户行为日志数据集，包含列：`user_id`、`action`（如"点击"、"购买"）、`timestamp`。请编写代码完成：
1. 找出所有 `user_id` 和 `action` 完全相同的重复记录（忽略时间戳差异）
2. 统计每个用户有多少条重复记录（即重复次数-1）
3. 去重后保留每个用户每种行为的最新一条记录（按时间戳排序）

**答案提示**：
```python
# 1. 检测重复
dup_mask = df.duplicated(subset=['user_id', 'action'], keep=False)
# 2. 统计重复次数
df[dup_mask].groupby(['user_id', 'action']).size() - 1
# 3. 先排序再去重
df_sorted = df.sort_values('timestamp')
df_dedup = df_sorted.drop_duplicates(subset=['user_id', 'action'], keep='last')
```

### 练习2：去重策略对比分析

有一个包含 10000 行、5 列的 DataFrame，其中约 20% 是重复行。请对比以下三种去重策略的时间复杂度和结果差异：
- 策略A：直接 `drop_duplicates()`（完全匹配）
- 策略B：按主键列 `id` 去重，保留第一条
- 策略C：先按 `id` 分组，再对每组按时间列排序后保留最后一条

**答案提示**：
```python
import time

# 策略A
start = time.time()
df_a = df.drop_duplicates()
time_a = time.time() - start

# 策略B
start = time.time()
df_b = df.drop_duplicates(subset=['id'], keep='first')
time_b = time.time() - start

# 策略C
start = time.time()
df_c = df.sort_values('timestamp').drop_duplicates(subset=['id'], keep='last')
time_c = time.time() - start

print(f"策略A耗时：{time_a:.4f}s，行数：{len(df_a)}")
print(f"策略B耗时：{time_b:.4f}s，行数：{len(df_b)}")
print(f"策略C耗时：{time_c:.4f}s，行数：{len(df_c)}")
# 思考：策略B和C结果行数相同但内容不同（保留哪条记录），策略A可能保留更多行（因其他列不同）
```

---

**总结**：重复值处理的核心是明确"什么算重复"（`subset`）和"保留哪条"（`keep`）。实际项目中建议先做重复检测统计，再结合业务规则选择去重策略，并在去重后重置索引、验证数据完整性。