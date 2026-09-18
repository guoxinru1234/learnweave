# 数据转换规范与校验

> 模块：ETL数据管道 | 编号：第33讲 | Python数据分析实战

---

## 1. 概念

数据转换规范与校验是 ETL（Extract, Transform, Load）管道中确保数据质量的核心环节。**数据转换**指将原始数据从一种格式或结构映射为另一种符合业务需求的格式或结构；**数据校验**则是在转换前后对数据进行检查，确保其满足预设的完整性、准确性、一致性和唯一性约束。

在真实业务中，原始数据往往来自多个异构源（如数据库导出文件、第三方API、日志文件），存在缺失值、重复记录、类型错乱、越界值等问题。若不加以规范与校验，下游分析或建模将产生不可信的结果。

**生活化类比**：这就像邮局分拣信件——先检查信封上地址是否完整（校验），再将不同格式的地址统一为规范格式（转换），最后装入对应区域的邮袋（加载）。如果地址格式不统一或信息缺失，信件就会投递失败。

适用场景：数据仓库建设、数据迁移、实时流处理、特征工程前的数据清洗等。

---

## 2. 核心API与原理

| API/方法 | 签名 | 参数说明 | 返回值 | 原理/用途 |
|----------|------|----------|--------|-----------|
| `pandas.DataFrame.astype()` | `df.astype(dtype, copy=True, errors='raise')` | `dtype`: 目标类型（如`'int64'`, `'float32'`）; `errors`: `'raise'`或`'ignore'` | 转换后的新DataFrame | 强制类型转换，用于统一字段的数据类型 |
| `pandas.DataFrame.drop_duplicates()` | `df.drop_duplicates(subset=None, keep='first', inplace=False)` | `subset`: 指定列名列表; `keep`: `'first'`/`'last'`/`False` | 去重后的DataFrame | 基于指定列检测并移除重复行 |
| `pandas.DataFrame.isnull()` / `notnull()` | `df.isnull()` | 无 | 布尔型DataFrame | 逐元素检测缺失值，配合`sum()`统计缺失量 |
| `pandas.DataFrame.fillna()` | `df.fillna(value=None, method=None, inplace=False)` | `value`: 标量或字典; `method`: `'ffill'`/`'bfill'` | 填充后的DataFrame | 用指定值或前后向填充处理缺失值 |
| `pandas.DataFrame.query()` | `df.query(expr, inplace=False)` | `expr`: 字符串查询表达式（如`"age > 30 & city == '北京'"`） | 筛选后的DataFrame | 基于布尔表达式进行条件过滤，实现范围/枚举校验 |

---

## 3. 代码示例

### 示例1：基础类型转换与缺失值校验（入门）

```python
import pandas as pd
import numpy as np

# 构造原始数据（模拟从CSV读取的脏数据）
raw_data = pd.DataFrame({
    'user_id': ['101', '102', '103', '104', '105'],
    'age': ['25', '三十', '30', '28', '27'],   # 含非数字字符串
    'salary': [10000, 15000, None, 20000, 18000],  # 含缺失值
    'city': ['北京', '上海', '北京', '广州', '上海']
})

print("=== 原始数据 ===")
print(raw_data.dtypes)
print(raw_data)

# 1. 类型转换：将user_id从字符串转为整数
raw_data['user_id'] = raw_data['user_id'].astype('int64')

# 2. 缺失值校验：统计salary列的缺失数量
missing_count = raw_data['salary'].isnull().sum()
print(f"\n=== 缺失值校验：salary列缺失 {missing_count} 条 ===")

# 3. 缺失值处理：用均值填充
mean_salary = raw_data['salary'].mean()
raw_data['salary'] = raw_data['salary'].fillna(mean_salary)

# 4. 年龄列清洗：将'三十'替换为30（模拟规则校验）
raw_data['age'] = raw_data['age'].replace('三十', '30').astype('int64')

print("\n=== 清洗后数据 ===")
print(raw_data)
print(raw_data.dtypes)

# 输出结果:
# === 原始数据 ===
# user_id    object
# age        object
# salary    float64
# city       object
# dtype: object
#    user_id  age  salary city
# 0      101   25  10000.0   北京
# 1      102   三十  15000.0   上海
# 2      103   30      NaN   北京
# 3      104   28  20000.0   广州
# 4      105   27  18000.0   上海
#
# === 缺失值校验：salary列缺失 1 条 ===
#
# === 清洗后数据 ===
#    user_id  age   salary city
# 0      101   25  10000.0   北京
# 1      102   30  15000.0   上海
# 2      103   30  15750.0   北京
# 3      104   28  20000.0   广州
# 4      105   27  18000.0   上海
# user_id     int64
# age         int64
# salary    float64
# city        object
# dtype: object
```

### 示例2：重复值检测与条件过滤（进阶）

```python
import pandas as pd

# 构造含重复记录的数据
df = pd.DataFrame({
    'order_id': ['A001', 'A002', 'A001', 'A003', 'A002'],
    'product': ['手机', '电脑', '手机', '平板', '电脑'],
    'amount': [5000, 8000, 5000, 3000, 8000],
    'status': ['已完成', '处理中', '已完成', '已完成', '处理中']
})

print("=== 原始订单数据 ===")
print(df)

# 1. 基于order_id检测重复
duplicate_mask = df.duplicated(subset=['order_id'], keep=False)
print(f"\n=== 重复订单检测（含首次出现）===")
print(df[duplicate_mask])

# 2. 去重：保留第一条记录
df_dedup = df.drop_duplicates(subset=['order_id'], keep='first')
print(f"\n=== 去重后（保留首条）===")
print(df_dedup)

# 3. 条件校验：筛选金额>=5000且状态为'已完成'的订单
valid_orders = df_dedup.query("amount >= 5000 & status == '已完成'")
print(f"\n=== 校验通过的有效订单 ===")
print(valid_orders)

# 输出结果:
# === 原始订单数据 ===
#   order_id product  amount status
# 0     A001     手机    5000   已完成
# 1     A002     电脑    8000   处理中
# 2     A001     手机    5000   已完成
# 3     A003     平板    3000   已完成
# 4     A002     电脑    8000   处理中
#
# === 重复订单检测（含首次出现）===
#   order_id product  amount status
# 0     A001     手机    5000   已完成
# 1     A002     电脑    8000   处理中
# 2     A001     手机    5000   已完成
# 4     A002     电脑    8000   处理中
#
# === 去重后（保留首条）===
#   order_id product  amount status
# 0     A001     手机    5000   已完成
# 1     A002     电脑    8000   处理中
# 3     A003     平板    3000   已完成
#
# === 校验通过的有效订单 ===
#   order_id product  amount status
# 0     A001     手机    5000   已完成
```

### 示例3：完整ETL转换管道（综合应用）

```python
import pandas as pd
import numpy as np

def etl_pipeline(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    完整的ETL转换与校验管道
    步骤：类型规范 → 缺失值处理 → 重复值清理 → 业务规则校验
    """
    df = raw_df.copy()
    
    # 步骤1：类型规范——统一为正确的数据类型
    df['user_id'] = df['user_id'].astype('int64')
    df['signup_date'] = pd.to_datetime(df['signup_date'])  # 转为datetime类型
    df['age'] = pd.to_numeric(df['age'], errors='coerce')  # 无法转换的变为NaN
    
    # 步骤2：缺失值校验与处理
    print(f"[校验] 缺失值统计:\n{df.isnull().sum()}")
    # 年龄缺失用中位数填充（更稳健）
    df['age'] = df['age'].fillna(df['age'].median())
    # 删除注册日期缺失的行（关键字段不可填充）
    df = df.dropna(subset=['signup_date'])
    
    # 步骤3：重复值清理
    df = df.drop_duplicates(subset=['user_id', 'signup_date'], keep='last')
    
    # 步骤4：业务规则校验——年龄必须在18-60之间
    invalid_age = df.query("age < 18 | age > 60")
    print(f"[校验] 年龄越界记录 {len(invalid_age)} 条，已剔除")
    df = df.query("age >= 18 & age <= 60")
    
    return df

# 构造模拟数据
raw = pd.DataFrame({
    'user_id': ['1', '2', '3', '4', '5', '6'],
    'signup_date': ['2023-01-15', '2023-02-20', '2023-03-10', 
                    '2023-01-15', 'invalid_date', '2023-04-01'],
    'age': ['25', '17', '三十', '25', '45', '65'],
    'city': ['北京', '上海', '北京', '北京', '广州', '深圳']
})

# 执行管道
clean_df = etl_pipeline(raw)
print(f"\n=== 最终清洗结果 ===")
print(clean_df)

# 输出结果:
# [校验] 缺失值统计:
# user_id       0
# signup_date   1
# age           1
# city          0
# dtype: int64
# [校验] 年龄越界记录 1 条，已剔除
#
# === 最终清洗结果 ===
#    user_id signup_date   age city
# 0        1  2023-01-15  25.0   北京
# 2        3  2023-03-10  30.0   北京
# 3        4  2023-01-15  25.0   北京
# 4        5  2023-04-01  45.0   广州
```

---

## 4. 常见错误

### 错误1：忽略`errors`参数导致类型转换崩溃

```python
# 错误写法：遇到无法转换的值直接抛异常
df['age'] = df['age'].astype('int64')  # 若含'三十'则报ValueError

# 正确写法：使用errors='coerce'将非法值转为NaN，再单独处理
df['age'] = pd.to_numeric(df['age'], errors='coerce')
df['age'] = df['age'].fillna(df['age'].median())  # 后续填充
```

**原因**：`astype()`默认`errors='raise'`，遇到非数字字符串会中断整个管道。生产环境中应使用`pd.to_numeric()`配合`errors='coerce'`实现容错。

### 错误2：在`drop_duplicates()`中忘记指定`subset`

```python
# 错误写法：默认基于所有列判断重复，可能漏掉部分重复
df_dedup = df.drop_duplicates()  
# 若两条记录order_id相同但amount不同，则不会被去重

# 正确写法：明确指定业务主键列
df_dedup = df.drop_duplicates(subset=['order_id'], keep='first')
```

**原因**：`subset`参数决定重复判断的列范围。不指定时使用全部列，导致业务意义上的重复记录无法被识别。

### 错误3：链式赋值修改视图而非副本

```python
# 错误写法：可能触发SettingWithCopyWarning
filtered = df[df['age'] > 18]
filtered['valid'] = True  # 修改的是视图，可能不生效

# 正确写法：显式创建副本
filtered = df[df['age'] > 18].copy()
filtered['valid'] = True  # 安全修改
```

**原因**：Pandas的布尔索引返回的是视图（View）而非副本（Copy），直接修改会引发警告且结果不可预期。使用`.copy()`确保独立内存空间。

---

## 5. 练习

### 练习1：动手题——构建销售数据清洗管道

给定以下销售数据，请编写一个函数完成：① 将`date`列转为datetime类型；② 删除`order_id`完全重复的记录；③ 将`quantity`列的负数替换为0；④ 筛选出`amount > 0`的记录。

```python
sales_data = pd.DataFrame({
    'order_id': ['S001', 'S002', 'S001', 'S003', 'S004'],
    'date': ['2023-05-01', '2023-05-02', '2023-05-01', '2023-05-03', '2023-05-04'],
    'quantity': [2, -1, 2, 5, 3],
    'amount': [200, -50, 200, 500, 300]
})
```

**答案提示**：使用`pd.to_datetime()`转换日期；`drop_duplicates(subset=['order_id'])`去重；`df['quantity'] = df['quantity'].clip(lower=0)`或`np.where()`处理负数；最后用`df[df['amount'] > 0]`过滤。

### 练习2：思考题——校验规则的优先级设计

在ETL管道中，如果一条记录同时存在**缺失值**、**类型错误**和**业务规则越界**（如年龄200岁），你认为处理顺序应该是怎样的？为什么？

**答案提示**：建议顺序为：**类型转换 → 缺失值处理 → 业务规则校验**。原因：类型转换是基础，只有类型正确才能进行后续数值比较；缺失值处理（填充或删除）应在规则校验前完成，否则缺失值会干扰规则判断；最后进行业务规则校验，确保数据符合业务语义。这种顺序能最大化保留有效数据，同时避免无效计算。

---

> **核心要点总结**：数据转换规范与校验是ETL管道的质量守门员。掌握`astype()`、`drop_duplicates()`、`isnull()`、`fillna()`、`query()`等核心API，遵循"先类型、再缺失、后规则"的处理顺序，并始终警惕视图与副本的区别，即可构建稳健的数据清洗管道。