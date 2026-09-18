# CSV/Excel/JSON数据读取

> 模块：Pandas数据处理(上) | 编号：第12讲 | Python数据分析实战

---

## 1. 概念

数据读取是数据分析流程的第一步，也是最重要的一步——没有数据，一切分析都无从谈起。Pandas 提供了 `read_csv()`、`read_excel()` 和 `read_json()` 三个核心函数，分别用于读取逗号分隔值（CSV）、Excel 电子表格和 JSON 格式的数据文件，并将其转换为 **DataFrame** 对象——这是 Pandas 中最核心的二维表格数据结构。

**生活化类比**：可以把读取数据想象成"打开快递箱"。CSV 就像是一个标准的纸箱（纯文本、通用、轻便）；Excel 像是一个带隔层的收纳盒（可以有多个工作表、带格式）；JSON 则像是一个带有嵌套结构的礼物盒（数据有层级关系）。`read_*` 系列函数就是你的"开箱工具"，它们知道每种箱子的打开方式，并把里面的物品（数据）整齐地摆放到桌面上（DataFrame）。

**适用场景**：
- **CSV**：日志数据、机器学习数据集（如 Kaggle 竞赛数据）、系统导出数据
- **Excel**：财务报表、业务报表、需要保留格式的多表数据
- **JSON**：API 接口返回数据、NoSQL 数据库导出、Web 爬虫抓取的数据

---

## 2. 核心API与原理

| API | 签名 | 关键参数 | 返回值 |
|-----|------|----------|--------|
| `pd.read_csv()` | `pd.read_csv(filepath_or_buffer, sep=',', encoding=None, header='infer', index_col=None, usecols=None, dtype=None, parse_dates=False)` | `sep`：分隔符，默认逗号；`encoding`：文件编码（如 `'utf-8'`、`'gbk'`）；`header`：指定哪一行作为列名，默认第0行；`index_col`：指定哪一列作为行索引；`usecols`：只读取指定列；`dtype`：指定列的数据类型；`parse_dates`：将指定列解析为日期类型 | DataFrame |
| `pd.read_excel()` | `pd.read_excel(io, sheet_name=0, header=0, index_col=None, usecols=None, dtype=None)` | `sheet_name`：工作表名称或索引（如 `0` 或 `'Sheet1'`）；`header`：列名所在行；`usecols`：读取指定列（如 `"A:C"` 或 `[0,1,2]`）；`dtype`：指定列数据类型 | DataFrame（若 `sheet_name` 为列表则返回 dict of DataFrame） |
| `pd.read_json()` | `pd.read_json(path_or_buf, orient='columns', typ='frame', dtype=None)` | `orient`：JSON 字符串的格式，可选 `'split'`、`'records'`、`'index'`、`'columns'`、`'values'`；`typ`：返回类型，`'frame'` 返回 DataFrame，`'series'` 返回 Series | DataFrame 或 Series |
| `df.to_csv()` / `df.to_excel()` / `df.to_json()` | 与读取函数对应 | `index`：是否写入行索引，默认 `True`；`encoding`：输出编码 | 无（写入文件） |

**原理说明**：`read_csv()` 底层使用 C 语言实现的高性能解析器（`c` 引擎），逐行读取并解析分隔符。`read_excel()` 依赖 `openpyxl`（处理 `.xlsx`）或 `xlrd`（处理旧版 `.xls`）库。`read_json()` 将 JSON 字符串解析为 Python 字典/列表，再转换为 DataFrame。三者最终都通过 Pandas 内部的索引对齐机制构建出结构化的 DataFrame。

---

## 3. 代码示例

### 示例 1：基础 CSV 读取（入门）

```python
import pandas as pd

# 创建示例 CSV 文件（模拟学生成绩数据）
csv_content = """姓名,语文,数学,英语
张三,85,92,78
李四,76,88,95
王五,93,79,86
"""
with open('students.csv', 'w', encoding='utf-8') as f:
    f.write(csv_content)

# 读取 CSV 文件
df = pd.read_csv('students.csv', encoding='utf-8')
print(df)
# 输出：
#    姓名  语文  数学  英语
# 0  张三   85   92   78
# 1  李四   76   88   95
# 2  王五   93   79   86

# 查看数据类型
print(df.dtypes)
# 输出：
# 姓名    object
# 语文     int64
# 数学     int64
# 英语     int64
# dtype: object
```

### 示例 2：Excel 多工作表读取（进阶）

```python
import pandas as pd

# 创建示例 Excel 文件（包含两个工作表）
with pd.ExcelWriter('sales.xlsx') as writer:
    pd.DataFrame({'月份': ['1月', '2月'], '销售额': [100, 150]}).to_excel(writer, sheet_name='华东', index=False)
    pd.DataFrame({'月份': ['1月', '2月'], '销售额': [80, 120]}).to_excel(writer, sheet_name='华南', index=False)

# 读取指定工作表
df_east = pd.read_excel('sales.xlsx', sheet_name='华东')
print(df_east)
# 输出：
#    月份   销售额
# 0  1月   100
# 1  2月   150

# 读取所有工作表（返回字典）
all_sheets = pd.read_excel('sales.xlsx', sheet_name=None)
print(list(all_sheets.keys()))
# 输出：
# ['华东', '华南']

# 只读取 A 列到 B 列
df_partial = pd.read_excel('sales.xlsx', sheet_name='华东', usecols='A:B')
print(df_partial)
# 输出：
#    月份   销售额
# 0  1月   100
# 1  2月   150
```

### 示例 3：JSON 数据读取（进阶）

```python
import pandas as pd
import json

# 创建示例 JSON 文件（records 格式）
json_data = [
    {"商品": "手机", "价格": 4999, "库存": 50},
    {"商品": "电脑", "价格": 8999, "库存": 30},
    {"商品": "耳机", "价格": 999, "库存": 200}
]
with open('products.json', 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False)

# 读取 JSON 文件（records 格式）
df = pd.read_json('products.json', orient='records')
print(df)
# 输出：
#    商品    价格   库存
# 0  手机   4999   50
# 1  电脑   8999   30
# 2  耳机    999  200

# 处理嵌套 JSON（split 格式）
nested_json = {
    "columns": ["城市", "人口"],
    "index": [0, 1],
    "data": [["北京", 2189], ["上海", 2487]]
}
with open('nested.json', 'w', encoding='utf-8') as f:
    json.dump(nested_json, f, ensure_ascii=False)

df_nested = pd.read_json('nested.json', orient='split')
print(df_nested)
# 输出：
#    城市    人口
# 0  北京  2189
# 1  上海  2487
```

---

## 4. 常见错误

### 错误 1：编码问题导致读取失败

```python
# 错误写法：默认使用 utf-8 编码读取 GBK 编码的文件
df = pd.read_csv('chinese_data.csv')  # UnicodeDecodeError: 'utf-8' codec can't decode byte

# 正确写法：指定正确的编码
df = pd.read_csv('chinese_data.csv', encoding='gbk')
# 或使用 gb18030（更全面的中文编码）
df = pd.read_csv('chinese_data.csv', encoding='gb18030')
```

**原因**：中文 Windows 系统导出的 CSV 文件默认使用 GBK 编码，而 Pandas 默认使用 UTF-8。

### 错误 2：Excel 文件路径包含特殊字符或文件被占用

```python
# 错误写法：路径中包含中文且 Excel 文件正在被打开
df = pd.read_excel('C:\用户\数据\报表.xlsx')  # 路径错误 + 文件被占用

# 正确写法：使用原始字符串或正斜杠
df = pd.read_excel(r'C:\用户\数据\报表.xlsx')  # 使用 r 前缀
# 或使用正斜杠
df = pd.read_excel('C:/用户/数据/报表.xlsx')
```

**原因**：Windows 路径中的反斜杠 `\` 在 Python 字符串中是转义字符，且 Excel 打开文件时会锁定文件。

### 错误 3：JSON 格式不匹配

```python
# 错误写法：JSON 是嵌套字典格式，但未指定 orient
json_str = '{"a": {"x": 1, "y": 2}, "b": {"x": 3, "y": 4}}'
df = pd.read_json(json_str)  # 结果不是预期的两行两列

# 正确写法：指定 orient='index'
df = pd.read_json(json_str, orient='index')
print(df)
# 输出：
#    x  y
# a  1  2
# b  3  4
```

**原因**：`read_json()` 默认 `orient='columns'`，对于嵌套 JSON 结构需要明确指定 `orient` 参数。

---

## 5. 练习

### 练习 1：综合读取与清洗

**题目**：有一个 `sales_data.csv` 文件，包含列：`日期`、`产品`、`销量`、`单价`。请完成以下操作：
1. 读取该文件，并将 `日期` 列解析为日期类型（`datetime`）
2. 只读取 `产品` 和 `销量` 两列
3. 将 `产品` 列设置为行索引

**答案提示**：
```python
import pandas as pd

# 创建示例数据
df = pd.read_csv('sales_data.csv', 
                  parse_dates=['日期'],  # 解析日期列
                  usecols=['产品', '销量'],  # 只读取两列
                  index_col='产品')  # 设置行索引
```

### 练习 2：JSON 格式转换

**题目**：将以下嵌套 JSON 结构读取为 DataFrame，并计算每个人的总成绩：

```json
{
  "students": [
    {"name": "Alice", "scores": {"math": 90, "english": 85}},
    {"name": "Bob", "scores": {"math": 78, "english": 92}}
  ]
}
```

**答案提示**：
```python
import pandas as pd
import json

with open('students.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取并展开嵌套数据
records = []
for student in data['students']:
    records.append({
        'name': student['name'],
        **student['scores']  # 展开嵌套字典
    })

df = pd.DataFrame(records)
df['总成绩'] = df['math'] + df['english']
print(df)
# 输出：
#     name  math  english  总成绩
# 0  Alice    90       85    175
# 1    Bob    78       92    170
```