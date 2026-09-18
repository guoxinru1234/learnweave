# 数据质量报告自动生成

> 模块：数据清洗实战 | 编号：第25讲 | Python数据分析实战

---

## 1. 概念

数据质量报告（Data Quality Report）是对数据集进行系统性"体检"后生成的标准化文档，它通过统计指标（缺失率、唯一值比例、数据类型、取值范围、重复记录等）量化评估数据的健康状况，帮助分析人员快速定位数据问题，为后续清洗策略提供依据。

**适用场景**：新数据集接入时的初步探查、定期数据质量监控、数据清洗前后的效果对比、交付数据前的质量验收。

**生活化类比**：数据质量报告就像每年体检报告。体检报告会告诉你血压、血糖、心率等指标是否在正常范围，并标出异常项；数据质量报告则告诉你每一列数据的"缺失率"（相当于体检漏检项）、"重复记录"（相当于重复挂号）、"异常值"（相当于异常指标），让你一眼看出数据"哪里不舒服"，再决定是否需要"治疗"（清洗）。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 | 用途 |
|-----|------|----------|--------|------|
| `DataFrame.info()` | `info(verbose=None, buf=None, max_cols=None, memory_usage=None, show_counts=None)` | `verbose`：是否显示全部列；`show_counts`：是否显示非空计数 | 无（打印到控制台） | 快速查看列名、非空计数、数据类型、内存占用 |
| `DataFrame.describe()` | `describe(percentiles=None, include=None, exclude=None)` | `percentiles`：分位数列表；`include`：包含的数据类型；`exclude`：排除的数据类型 | `DataFrame`（统计摘要） | 生成数值列的描述性统计（均值、标准差、最小值、分位数、最大值） |
| `DataFrame.isnull().sum()` | `isnull()` 返回布尔型 `DataFrame`，再调用 `sum()` | 无 | `Series`（每列缺失值总数） | 统计每列缺失值数量 |
| `DataFrame.duplicated()` | `duplicated(subset=None, keep='first')` | `subset`：检查重复的列子集；`keep`：标记重复的方式（'first'/'last'/False） | `Series`（布尔型） | 检测重复行 |
| `pandas.DataFrame.dtypes` | 属性（非方法） | 无 | `Series`（每列数据类型） | 查看每列的数据类型 |

**原理说明**：`info()` 底层通过遍历列索引统计非空值数量，`describe()` 则调用 `Series.describe()` 对每列分别计算统计量。`isnull()` 生成与源数据同形状的布尔掩码，`sum()` 沿列方向求和（True=1, False=0），从而得到缺失计数。这些方法均为向量化操作，性能高效。

---

## 3. 代码示例

### 示例1：基础数据质量报告（单表体检）

```python
import pandas as pd
import numpy as np

# 构造含缺失值、重复值、异常值的数据集
data = {
    '姓名': ['张三', '李四', '王五', '张三', '赵六', '孙七'],
    '年龄': [25, 30, np.nan, 25, 120, 28],  # 含缺失值和异常值(120)
    '城市': ['北京', '上海', '广州', '北京', '深圳', None],
    '薪资': [8000, 12000, 15000, 8000, 20000, 9500]
}
df = pd.DataFrame(data)

print("=== 1. 基本信息 ===")
df.info()

print("\n=== 2. 缺失值统计 ===")
print(df.isnull().sum())

print("\n=== 3. 重复记录数 ===")
print(f"重复行数: {df.duplicated().sum()}")

print("\n=== 4. 数值列统计摘要 ===")
print(df.describe())

print("\n=== 5. 数据类型 ===")
print(df.dtypes)
```

**输出结果**：
```
=== 1. 基本信息 ===
<class 'pandas.core.frame.DataFrame'>
RangeIndex: 6 entries, 0 to 5
Data columns (total 4 columns):
 #   Column  Non-Null Count  Dtype  
---  ------  --------------  -----  
 0   姓名     6 non-null      object 
 1   年龄     5 non-null      float64
 2   城市     5 non-null      object 
 3   薪资     6 non-null      int64  
dtypes: float64(1), int64(1), object(2)
memory usage: 324.0+ bytes

=== 2. 缺失值统计 ===
姓名    0
年龄    1
城市    1
薪资    0
dtype: int64

=== 3. 重复记录数 ===
重复行数: 1

=== 4. 数值列统计摘要 ===
             年龄          薪资
count   5.000000     6.000000
mean   45.600000  12166.666667
std    41.553586   4415.634467
min   25.000000   8000.000000
25%   26.500000   9125.000000
50%   28.000000  10750.000000
75%   29.000000  14250.000000
max  120.000000  20000.000000

=== 5. 数据类型 ===
姓名    object
年龄    float64
城市    object
薪资     int64
dtype: object
```

### 示例2：自定义数据质量报告函数（可复用）

```python
import pandas as pd
import numpy as np

def generate_quality_report(df, df_name="数据集"):
    """自动生成数据质量报告，返回报告DataFrame"""
    
    report_data = []
    
    for col in df.columns:
        col_data = df[col]
        total = len(df)
        missing = col_data.isnull().sum()
        missing_rate = missing / total * 100
        
        # 判断数据类型类别
        if pd.api.types.is_numeric_dtype(col_data):
            dtype_category = "数值型"
            unique_count = col_data.nunique()
            # 检测异常值（超出均值±3倍标准差）
            mean_val = col_data.mean()
            std_val = col_data.std()
            if std_val > 0:
                outliers = ((col_data - mean_val).abs() > 3 * std_val).sum()
            else:
                outliers = 0
        else:
            dtype_category = "类别型"
            unique_count = col_data.nunique()
            outliers = "N/A"
        
        report_data.append({
            "列名": col,
            "数据类型": str(col_data.dtype),
            "类型类别": dtype_category,
            "非空数": total - missing,
            "缺失数": missing,
            "缺失率(%)": round(missing_rate, 2),
            "唯一值数": unique_count,
            "异常值数": outliers
        })
    
    report_df = pd.DataFrame(report_data)
    
    print(f"===== {df_name} 数据质量报告 =====")
    print(f"总记录数: {len(df)}, 总列数: {len(df.columns)}")
    print(f"重复行数: {df.duplicated().sum()}")
    print(f"重复率: {df.duplicated().sum() / len(df) * 100:.2f}%")
    print("\n")
    return report_df

# 测试
data = {
    '订单ID': ['A001', 'A002', 'A003', 'A001', 'A005'],
    '金额': [100, 200, np.nan, 100, 99999],
    '类别': ['电子', '服装', '食品', '电子', '电子']
}
df = pd.DataFrame(data)

report = generate_quality_report(df, "订单数据")
print(report.to_string(index=False))
```

**输出结果**：
```
===== 订单数据 数据质量报告 =====
总记录数: 5, 总列数: 3
重复行数: 1
重复率: 20.00%

列名    数据类型  类型类别  非空数  缺失数  缺失率(%)  唯一值数  异常值数
订单ID   object  类别型     5      0       0.00      4        N/A
金额    float64 数值型     4      1      20.00      4        1
类别    object  类别型     5      0       0.00      3        N/A
```

### 示例3：完整数据质量报告（含可视化输出）

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 构造模拟销售数据
np.random.seed(42)
n = 200
df = pd.DataFrame({
    '日期': pd.date_range('2024-01-01', periods=n, freq='D'),
    '销售额': np.random.normal(5000, 800, n).round(2),
    '客户ID': np.random.choice(['C001', 'C002', 'C003'], n),
    '退货量': np.random.randint(0, 10, n)
})
# 人为制造问题
df.loc[10:15, '销售额'] = np.nan  # 缺失值
df.loc[20, '销售额'] = 999999     # 异常值
df.loc[30:31] = df.loc[28:29].values  # 重复行

def full_quality_report(df):
    """生成完整数据质量报告（含可视化）"""
    
    # 1. 基础统计
    print("=" * 50)
    print("数据质量报告")
    print("=" * 50)
    print(f"数据形状: {df.shape[0]}行 × {df.shape[1]}列")
    print(f"内存占用: {df.memory_usage(deep=True).sum() / 1024:.2f} KB")
    
    # 2. 缺失值分析
    missing_df = pd.DataFrame({
        '缺失数': df.isnull().sum(),
        '缺失率(%)': (df.isnull().sum() / len(df) * 100).round(2)
    })
    print("\n【缺失值分析】")
    print(missing_df[missing_df['缺失数'] > 0])
    
    # 3. 重复值分析
    dup_count = df.duplicated().sum()
    print(f"\n【重复值分析】重复行数: {dup_count} ({dup_count/len(df)*100:.2f}%)")
    
    # 4. 异常值分析（IQR方法）
    print("\n【异常值分析】(IQR方法)")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        outliers = df[(df[col] < lower) | (df[col] > upper)]
        if len(outliers) > 0:
            print(f"  列 '{col}': {len(outliers)} 个异常值, 范围 [{lower:.2f}, {upper:.2f}]")
    
    # 5. 可视化
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    
    # 缺失率柱状图
    missing_rate = df.isnull().mean() * 100
    axes[0, 0].bar(missing_rate.index, missing_rate.values)
    axes[0, 0].set_title('各列缺失率(%)')
    axes[0, 0].set_xticklabels(missing_rate.index, rotation=45)
    
    # 数值列分布直方图
    df['销售额'].dropna().hist(ax=axes[0, 1], bins=30)
    axes[0, 1].set_title('销售额分布')
    
    # 类别列分布
    df['客户ID'].value_counts().plot(kind='bar', ax=axes[1, 0])
    axes[1, 0].set_title('客户ID分布')
    
    # 箱线图（异常值检测）
    df.boxplot(column='销售额', ax=axes[1, 1])
    axes[1, 1].set_title('销售额箱线图')
    
    plt.tight_layout()
    plt.savefig('quality_report.png', dpi=100)
    print("\n📊 可视化报告已保存为 quality_report.png")
    plt.show()

full_quality_report(df)
```

**输出结果**（部分）：
```
==================================================
数据质量报告
==================================================
数据形状: 200行 × 4列
内存占用: 21.48 KB

【缺失值分析】
        缺失数  缺失率(%)
销售额       6      3.0

【重复值分析】重复行数: 2 (1.00%)

【异常值分析】(IQR方法)
  列 '销售额': 1 个异常值, 范围 [3125.25, 6936.75]

📊 可视化报告已保存为 quality_report.png
```

---

## 4. 常见错误

### 错误1：忽略 `NaN` 与 `None` 的区别

```python
# ❌ 错误写法
df = pd.DataFrame({'A': [1, None, 3]})
print(df['A'].isnull().sum())  # 输出: 1 (正确)
print(df['A'] == None)  # 输出: 0 False, 1 False, 2 False (错误！)

# ✅ 正确写法
print(df['A'].isnull())  # 使用 isnull() 检测缺失
# 0    False
# 1     True
# 2    False
```

**原因**：Pandas 将 `None` 自动转换为 `NaN`（`float` 类型），而 `NaN != None`，直接比较会失败。应始终使用 `isnull()` / `notna()` 检测缺失值。

### 错误2：忘记处理 `describe()` 中的非数值列

```python
# ❌ 错误写法
df = pd.DataFrame({'姓名': ['张三', '李四'], '年龄': [25, 30]})
print(df.describe())  # 默认只统计数值列，姓名列被忽略

# ✅ 正确写法
print(df.describe(include='all'))  # 包含所有列
# 或分别处理
print(df.describe(include=[object]))  # 只统计类别列
```

**原因**：`describe()` 默认只对数值列计算统计量。若需查看类别列的统计信息（如唯一值数、出现次数最多的值），需指定 `include='all'` 或明确指定数据类型。

### 错误3：重复值检测未考虑 `subset` 参数

```python
# ❌ 错误写法
df = pd.DataFrame({
    '订单号': ['A1', 'A1', 'A2'],
    '客户': ['张三', '李四', '张三']
})
print(df.duplicated().sum())  # 输出: 0 (整行完全相同才算重复)

# ✅ 正确写法
print(df.duplicated(subset=['订单号']).sum())  # 输出: 1 (按订单号判断重复)
```

**原因**：`duplicated()` 默认基于整行判断重复。实际业务中常需按关键列（如订单号、身份证号）判断重复，需指定 `subset` 参数。

---

## 5. 练习

### 练习1：完善数据质量报告函数

**题目**：基于示例2的 `generate_quality_report` 函数，增加以下功能：
1. 对数值列，增加"零值数量"和"零值率"统计；
2. 对类别列，增加"众数"（出现次数最多的值）统计；
3. 增加一个 `save_path` 参数，当传入路径时将报告保存为 CSV 文件。

**答案提示**：
```python
def generate_quality_report(df, df_name="数据集", save_path=None):
    # ... 原有逻辑 ...
    for col in df.columns:
        col_data = df[col]
        if pd.api.types.is_numeric_dtype(col_data):
            zero_count = (col_data == 0).sum()
            zero_rate = zero_count / total * 100
            # 在报告字典中添加 '零值数' 和 '零值率(%)'
        else:
            mode_val = col_data.mode()
            mode_str = mode_val.iloc[0] if len(mode_val) > 0 else "N/A"
            # 在报告字典中添加 '众数'
    # 最后：if save_path: report_df.to_csv(save_path, index=False, encoding='utf-8-sig')
```

### 练习2：自动生成多表对比报告

**题目**：假设你有清洗前（`raw_df`）和清洗后（`clean_df`）两份数据，编写代码生成一份"清洗效果对比报告"，包含：
1. 清洗前后缺失值总数对比；
2. 清洗前后重复行数对比；
3. 清洗前后数值列的标准差变化（衡量数据波动是否合理）。

**答案提示**：
```python
def compare_quality(raw_df, clean_df):
    # 缺失值对比
    raw_missing = raw_df.isnull().sum().sum()
    clean_missing = clean_df.isnull().sum().sum()
    
    # 重复值对比
    raw_dup = raw_df.duplicated().sum()
    clean_dup = clean_df.duplicated().sum()
    
    #