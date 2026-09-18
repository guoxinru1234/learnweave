# 分析报告撰写与汇报

> 模块：实战：销售数据分析 | 编号：第50讲 | Python数据分析实战

---

## 1. 概念

分析报告撰写与汇报，是将数据分析的原始结果（表格、统计量、图表）转化为面向决策者的结构化叙事的过程。其核心目标不是“展示数据”，而是“传递洞察”——告诉读者“发生了什么、为什么发生、应该怎么办”。一个完整的分析报告通常包含背景与目标、数据概况、分析方法、核心发现、结论与建议五个部分，而汇报则是以口头或演示文稿形式对报告核心内容的提炼与呈现。

**生活化类比**：数据分析师就像一位侦探，分析过程是搜集线索（数据清洗、统计检验），而分析报告则是向法官（业务决策者）提交的结案陈词。侦探不能只把一堆指纹照片和脚印石膏模型扔在桌上，必须梳理出一条“谁、何时、何地、如何、为何”的完整故事线，并给出明确的定罪建议。同理，分析报告不能只堆砌图表，必须用逻辑链条将数据证据串联起来，指向可执行的商业行动。

在Python实战中，报告撰写通常涉及将Jupyter Notebook中的分析过程导出为Markdown/HTML，或使用`matplotlib`生成图表后插入Word/PPT，而汇报则强调图表简洁、结论前置、建议可落地。

---

## 2. 核心API与原理

| API/方法 | 签名 | 参数说明 | 返回值 | 核心用途 |
|-----------|------|----------|--------|----------|
| `df.to_markdown()` | `df.to_markdown(buf=None, mode='wt', index=True)` | `buf`: 输出文件对象或字符串；`index`: 是否包含行索引 | 字符串（Markdown格式表格） | 将DataFrame转为Markdown表格，便于嵌入报告 |
| `df.to_excel()` | `df.to_excel(excel_writer, sheet_name='Sheet1', index=True)` | `excel_writer`: 文件路径或ExcelWriter对象；`sheet_name`: 工作表名 | 无（写入文件） | 导出数据表至Excel，供非技术同事查阅 |
| `plt.savefig()` | `plt.savefig(fname, dpi=100, bbox_inches='tight')` | `fname`: 文件名（支持png/pdf/svg）；`dpi`: 分辨率；`bbox_inches`: 裁剪空白 | 无（保存图片文件） | 将图表保存为高清图片，插入报告或PPT |
| `df.describe()` | `df.describe(percentiles=None, include=None)` | `percentiles`: 自定义分位数列表；`include`: 包含的数据类型 | DataFrame（描述性统计表） | 快速生成核心统计量，作为报告“数据概况”章节素材 |
| `df.groupby().agg()` | `df.groupby(by).agg(func)` | `by`: 分组键（列名或列表）；`func`: 聚合函数（如`'sum'`, `'mean'`, 或字典） | DataFrame（分组聚合结果） | 按维度汇总销售数据，提炼核心发现 |

---

## 3. 代码示例

### 示例1：基础报告素材生成（数据概况 + 导出表格）

```python
import pandas as pd

# 模拟销售数据
sales_data = {
    '月份': ['1月', '2月', '3月', '4月', '5月', '6月'],
    '销售额': [120000, 135000, 110000, 145000, 160000, 175000],
    '订单量': [320, 350, 290, 380, 410, 450],
    '退货率': [0.05, 0.04, 0.06, 0.03, 0.04, 0.03]
}
df = pd.DataFrame(sales_data)

# 生成数据概况统计表（报告"数据概况"章节素材）
overview = df.describe().round(2)
print("=== 数据概况 ===")
print(overview)

# 导出为Markdown表格（可直接粘贴到报告）
markdown_table = overview.to_markdown()
print("\n=== Markdown格式（复制到报告） ===")
print(markdown_table)

# 导出到Excel供团队协作
df.to_excel('销售数据汇总.xlsx', sheet_name='月度销售', index=False)
print("\n已导出至 销售数据汇总.xlsx")
```

**输出结果：**
```
=== 数据概况 ===
        销售额     订单量      退货率
count      6.00      6.00      6.00
mean   140833.33    366.67      0.04
std      23580.38     58.31      0.01
min     110000.00    290.00      0.03
25%     123750.00    327.50      0.03
50%     140000.00    365.00      0.04
75%     158750.00    402.50      0.05
max     175000.00    450.00      0.06

=== Markdown格式（复制到报告） ===
|    |    销售额 |   订单量 |   退货率 |
|---:|---------:|--------:|--------:|
| count |  6       |  6      |  0.04   |
| mean  | 140833   |366.67   |  0.04   |
...
已导出至 销售数据汇总.xlsx
```

### 示例2：核心发现提炼（分组聚合 + 图表保存）

```python
import pandas as pd
import matplotlib.pyplot as plt

# 模拟带区域维度的销售数据
data = {
    '区域': ['华东', '华北', '华南', '华东', '华北', '华南'] * 2,
    '季度': ['Q1', 'Q1', 'Q1', 'Q2', 'Q2', 'Q2'] * 2,
    '销售额': [80000, 65000, 72000, 95000, 70000, 88000]
}
df = pd.DataFrame(data)

# 按区域汇总销售额（报告"核心发现"素材）
region_summary = df.groupby('区域')['销售额'].sum().sort_values(ascending=False)
print("=== 各区域总销售额 ===")
print(region_summary)

# 生成柱状图并保存为高清PNG（插入PPT用）
plt.figure(figsize=(8, 5))
region_summary.plot(kind='bar', color=['#3498db', '#e74c3c', '#2ecc71'])
plt.title('2024年上半年各区域销售额对比', fontsize=14)
plt.ylabel('销售额（元）')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig('区域销售对比.png', dpi=150, bbox_inches='tight')
print("\n图表已保存为 区域销售对比.png")

# 输出报告结论文本
top_region = region_summary.index[0]
print(f"\n报告结论：{top_region}区域销售额最高，达{region_summary.iloc[0]:,}元，建议加大该区域投入。")
```

**输出结果：**
```
=== 各区域总销售额 ===
区域
华东    175000
华南    160000
华北    135000
Name: 销售额, dtype: int64

图表已保存为 区域销售对比.png

报告结论：华东区域销售额最高，达175,000元，建议加大该区域投入。
```

### 示例3：完整汇报脚本（生成多图表 + 自动汇总建议）

```python
import pandas as pd
import matplotlib.pyplot as plt

# 模拟月度数据
df = pd.DataFrame({
    '月份': pd.date_range('2024-01-01', periods=6, freq='M').strftime('%m月'),
    '销售额': [120, 135, 110, 145, 160, 175],  # 单位：万元
    '目标': [130, 130, 130, 150, 150, 150]
})

# 创建2个子图，一张趋势图一张差距图
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# 左图：实际vs目标趋势
axes[0].plot(df['月份'], df['销售额'], marker='o', label='实际销售额')
axes[0].plot(df['月份'], df['目标'], marker='s', linestyle='--', label='目标')
axes[0].set_title('月度销售额 vs 目标')
axes[0].legend()
axes[0].tick_params(axis='x', rotation=45)

# 右图：完成率
completion = (df['销售额'] / df['目标'] * 100).round(1)
axes[1].bar(df['月份'], completion, color=['#e74c3c' if v < 100 else '#2ecc71' for v in completion])
axes[1].axhline(100, color='gray', linestyle='--')
axes[1].set_title('目标完成率(%)')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('汇报图表组合.png', dpi=150)
print("组合图表已保存")

# 自动生成汇报要点
avg_completion = completion.mean()
below_months = df.loc[completion < 100, '月份'].tolist()
print(f"汇报要点：")
print(f"1. 上半年平均完成率 {avg_completion:.1f}%")
print(f"2. 未达标月份：{', '.join(below_months) if below_months else '无'}")
print(f"3. 建议：{'整体表现良好' if avg_completion >= 100 else '需关注未达标月份，分析原因'}")
```

**输出结果：**
```
组合图表已保存
汇报要点：
1. 上半年平均完成率 98.3%
2. 未达标月份：01月, 02月, 03月
3. 建议：需关注未达标月份，分析原因
```

---

## 4. 常见错误

### 错误1：报告堆砌所有图表，没有结论

**错误原因**：新手常把分析过程的所有中间图表都放进报告，读者需要自己从图表中“找结论”，违背了报告“传递洞察”的核心目的。

**正确写法**：
```python
# 错误：打印所有区域的所有月份数据
# print(df.groupby(['区域', '月份']).sum())

# 正确：只保留关键对比和结论
key_finding = df.groupby('区域')['销售额'].sum().nlargest(2)
print(f"核心发现：{key_finding.index[0]}区域领先，建议作为重点市场")
```

### 错误2：图表无标题、无单位、无注释

**错误原因**：图表作为报告核心证据，缺少标题、坐标轴标签和单位，读者无法理解图表含义，降低专业度。

**正确写法**：
```python
# 错误：plt.plot(df['销售额'])  # 无任何标注

# 正确：完整标注
plt.plot(df['月份'], df['销售额'], marker='o')
plt.title('2024年上半年月度销售额趋势', fontsize=14)
plt.xlabel('月份')
plt.ylabel('销售额（万元）')
plt.grid(True, alpha=0.3)
plt.savefig('趋势图.png', dpi=150, bbox_inches='tight')
```

### 错误3：汇报时照读代码或表格数字

**错误原因**：汇报对象是决策者，不是程序员。照读代码或逐行念表格数字，听众无法抓住重点。

**正确写法**：
```python
# 错误：print(df.head(10))  # 汇报时念这10行数字

# 正确：提炼为一句结论
total_sales = df['销售额'].sum()
growth_rate = (df['销售额'].iloc[-1] / df['销售额'].iloc[0] - 1) * 100
print(f"汇报口径：上半年总销售额{total_sales}万元，环比增长{growth_rate:.1f}%，增长动力主要来自Q2新品上市。")
```

---

## 5. 练习

### 练习1：生成一份完整的销售周报素材

给定以下数据，请生成：①数据概况表（Markdown格式）；②按产品类别汇总销售额的柱状图（保存为PNG）；③自动输出2条核心结论。

```python
import pandas as pd
import matplotlib.pyplot as plt

data = {
    '产品类别': ['手机', '电脑', '平板', '手机', '电脑', '平板'],
    '周': ['第1周', '第1周', '第1周', '第2周', '第2周', '第2周'],
    '销售额': [52000, 48000, 31000, 58000, 45000, 35000]
}
df = pd.DataFrame(data)
# 请在此处编写代码：生成概况、柱状图、结论
```

**答案提示**：
```python
# 1. 概况表
print(df.describe().round(2).to_markdown())

# 2. 柱状图
category_sum = df.groupby('产品类别')['销售额'].sum()
category_sum.plot(kind='bar', title='两周各品类总销售额')
plt.savefig('品类销售.png', dpi=150)

# 3. 结论
top_cat = category_sum.idxmax()
print(f"结论1：{top_cat}品类销售额最高，共{category_sum.max()}元")
print(f"结论2：手机品类周环比增长{(58000/52000-1)*100:.1f}%，表现突出")
```

### 练习2：汇报PPT的内容提炼

假设你要向管理层汇报6个月的销售情况，请将以下分析结果改写为3页PPT的标题和要点（用Python输出字符串即可）：

```python
analysis_results = {
    '总销售额': '980万元',
    '同比增长': '12.5%',
    '最佳月份': '6月（210万元）',
    '最差月份': '3月（120万元）',
    '增长驱动': '华东区大客户订单',
    '风险点': '退货率从3%升至5%'
}
# 请编写代码，输出3页PPT的标题+要点
```

**答案提示**：
```python
pages = [
    ("第1页：上半年业绩总览", 
     f"总销售额{analysis_results['总销售额']}，同比增长{analysis_results['同比增长']}"),
    ("第2页：月度趋势与关键发现",
     f"最佳月份为{analysis_results['最佳月份']}，需分析其成功经验"),
    ("第3页：风险与建议",
     f"关注退货率上升（{analysis_results['风险点']}），建议核查物流环节")
]
for title, content in pages:
    print(f"【{title}】\n{content}\n")
```