# 文本数据清洗与正则
> 模块：数据清洗实战 | 编号：第23讲 | Python数据分析实战

---

## 1. 概念

文本数据清洗是指对原始文本数据中存在的噪声（如特殊符号、多余空格、重复字符、不一致格式等）进行识别、修正和标准化的过程。正则表达式（Regular Expression，简称 regex）是一种描述字符串匹配模式的工具，它通过特定的语法规则，能够在文本中精准地查找、匹配、提取或替换符合某种模式的内容。

**适用场景**：日志解析、用户评论情感分析前的预处理、爬虫数据的字段提取、身份证号/手机号/邮箱格式校验、中文分词前的噪声去除等。在真实数据分析项目中，文本数据往往占据 80% 以上的原始数据量，而清洗质量直接影响后续建模效果。

**生活化类比**：正则表达式就像一台"高级筛子"。普通筛子只能按颗粒大小过滤，而正则筛子可以按"形状、颜色、花纹"任意组合条件来筛选——比如"筛出所有红色且带五角星的珠子"。同理，正则可以用一个模式同时匹配多种格式的文本，极大提高清洗效率。

---

## 2. 核心API与原理

Python 中处理正则的核心模块是 `re`，Pandas 中则通过 `str` 访问器调用正则方法。以下为最常用的 5 个 API：

| API | 签名 | 参数说明 | 返回值 | 用途 |
|-----|------|----------|--------|------|
| `re.sub` | `re.sub(pattern, repl, string, count=0, flags=0)` | `pattern`：正则模式；`repl`：替换字符串或函数；`string`：原字符串；`count`：最大替换次数（0 表示全部）；`flags`：如 `re.IGNORECASE` | `str`（替换后的新字符串） | 替换匹配到的文本 |
| `re.findall` | `re.findall(pattern, string, flags=0)` | 同上，无需 `repl` 和 `count` | `list`（所有匹配的子串列表） | 提取所有匹配内容 |
| `re.search` | `re.search(pattern, string, flags=0)` | 同上 | `Match` 对象或 `None` | 扫描整个字符串，返回第一个匹配 |
| `Series.str.replace` | `Series.str.replace(pat, repl, regex=True)` | `pat`：正则模式或普通字符串；`repl`：替换内容；`regex=True` 时 `pat` 按正则处理 | `Series` | Pandas 列级批量替换 |
| `Series.str.extract` | `Series.str.extract(pat, flags=0, expand=True)` | `pat`：含捕获组 `()` 的正则模式 | `DataFrame` | 从文本列中提取分组内容 |

**原理**：正则引擎按模式从左到右扫描字符串，通过元字符（如 `\d` 匹配数字、`*` 表示重复 0 次或多次）组合出匹配规则。Pandas 的 `str` 方法底层调用了 `re` 模块，并对 Series 的每个元素进行向量化操作。

---

## 3. 代码示例

### 示例 1：基础清洗——去除多余空格和特殊符号（简单）

```python
import re
import pandas as pd

# 原始数据：包含多余空格、HTML标签和特殊符号
raw_text = "  Hello,  World!  <p>Python</p>  ###数据分析###  "

# 1. 去除首尾及多余空格（将连续多个空格替换为单个空格）
cleaned = re.sub(r'\s+', ' ', raw_text).strip()
print(cleaned)
# 输出: Hello, World! <p>Python</p> ###数据分析###

# 2. 去除 HTML 标签
cleaned_no_html = re.sub(r'<[^>]+>', '', cleaned)
print(cleaned_no_html)
# 输出: Hello, World! Python ###数据分析###

# 3. 去除所有 # 符号
final_text = re.sub(r'#+', '', cleaned_no_html)
print(final_text)
# 输出: Hello, World! Python 数据分析
```

### 示例 2：Pandas 列级批量清洗（进阶）

```python
import pandas as pd

# 模拟用户评论数据，包含脏数据
df = pd.DataFrame({
    '评论': [
        '  商品质量很好！！！！！',
        '物流速度一般...但包装OK',
        '客服电话:138-1234-5678, 态度差',
        '【差评】商品与描述不符!!!'
    ]
})

# 1. 去除首尾空格和多余标点（连续感叹号压缩为1个）
df['评论_清洗'] = df['评论'].str.strip() \
                          .str.replace(r'！+', '！', regex=True) \
                          .str.replace(r'\.+', '.', regex=True)

# 2. 提取电话号码（正则匹配 3-4位-4位 或 连续11位）
df['电话'] = df['评论'].str.extract(r'(1[3-9]\d{1}[- ]?\d{4}[- ]?\d{4})')

# 3. 去除【】中的标签
df['评论_最终'] = df['评论_清洗'].str.replace(r'【.*?】', '', regex=True)

print(df[['评论_最终', '电话']])
# 输出:
#   评论_最终              电话
# 0  商品质量很好！        NaN
# 1  物流速度一般.但包装OK  NaN
# 2  客服电话:138-1234-5678, 态度差  138-1234-5678
# 3  差评商品与描述不符!   NaN
```

### 示例 3：复杂模式——日志解析与数据提取（高级）

```python
import re

# 模拟服务器访问日志
log_data = """
2024-01-15 10:23:45 ERROR 192.168.1.1 "GET /api/user" 500
2024-01-15 10:25:12 INFO  10.0.0.5  "POST /api/login" 200
2024-01-15 10:30:33 ERROR 172.16.0.9 "GET /api/order" 404
"""

# 定义日志解析正则：日期 时间 级别 IP "请求" 状态码
pattern = r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(\w+)\s+(\d+\.\d+\.\d+\.\d+)\s+"(\w+)\s+(\S+)"\s+(\d{3})'

# 使用 findall 提取所有字段
matches = re.findall(pattern, log_data)
print(f"共解析出 {len(matches)} 条日志")
for m in matches:
    print(f"日期:{m[0]} 时间:{m[1]} 级别:{m[2]} IP:{m[3]} 方法:{m[4]} 路径:{m[5]} 状态:{m[6]}")

# 输出:
# 共解析出 3 条日志
# 日期:2024-01-15 时间:10:23:45 级别:ERROR IP:192.168.1.1 方法:GET 路径:/api/user 状态:500
# 日期:2024-01-15 时间:10:25:12 级别:INFO IP:10.0.0.5 方法:POST 路径:/api/login 状态:200
# 日期:2024-01-15 时间:10:30:33 级别:ERROR IP:172.16.0.9 方法:GET 路径:/api/order 状态:404

# 进一步统计 ERROR 日志数量
error_count = len(re.findall(r'\bERROR\b', log_data))
print(f"ERROR 日志数量: {error_count}")  # 输出: ERROR 日志数量: 2
```

---

## 4. 常见错误

### 错误 1：忘记转义特殊字符导致匹配失败
```python
# 错误写法：匹配句号时直接用 "."，但 "." 在正则中匹配任意字符
text = "数据分析.python"
result = re.findall(r"数据.分析", text)  # 会匹配到 "数据分析" 或 "数据x分析"

# 正确写法：使用反斜杠转义
result = re.findall(r"数据\.分析", text)  # 只匹配 "数据.分析"
print(result)  # 输出: ['数据.分析']
```

### 错误 2：在 Pandas 中忘记设置 `regex=True`
```python
import pandas as pd
s = pd.Series(['abc123', 'def456'])

# 错误写法：默认 regex=False，"\d" 被当作普通字符
result = s.str.replace('\d', 'X')  # 输出: ['abc123', 'def456']（未替换）

# 正确写法：显式开启正则模式
result = s.str.replace(r'\d', 'X', regex=True)
print(result.tolist())  # 输出: ['abcXXX', 'defXXX']
```

### 错误 3：贪婪匹配导致提取内容过多
```python
import re
html = "<b>标题A</b> 和 <b>标题B</b>"

# 错误写法：默认贪婪匹配，会从第一个 <b> 匹配到最后一个 </b>
result = re.findall(r'<b>(.*)</b>', html)
print(result)  # 输出: ['标题A</b> 和 <b>标题B']  ← 错误！

# 正确写法：使用非贪婪模式（加 ?）
result = re.findall(r'<b>(.*?)</b>', html)
print(result)  # 输出: ['标题A', '标题B']  ← 正确
```

---

## 5. 练习

### 练习 1：手机号脱敏
给定一个包含用户信息的 DataFrame，其中 `手机号` 列包含类似 `13812345678` 的 11 位号码。请编写代码将中间 4 位替换为 `****`，输出脱敏后的结果。

**答案提示**：
```python
import pandas as pd
df = pd.DataFrame({'手机号': ['13812345678', '15998765432', '13611112222']})
# 使用正则：保留前3位和后4位，中间替换
df['脱敏'] = df['手机号'].str.replace(r'(\d{3})\d{4}(\d{4})', r'\1****\2', regex=True)
print(df)
# 输出: 138****5678, 159****5432, 136****2222
```

### 练习 2：中文文本中的英文单词提取
给定一段中英混合文本，提取其中所有英文单词（仅包含字母，长度≥2），并统计每个单词出现的次数。

**答案提示**：
```python
import re
from collections import Counter

text = "Python 数据分析很好用，Pandas 和 NumPy 是核心库。Python 也很适合做机器学习。"

# 提取所有英文单词（忽略大小写，统一转为小写）
words = re.findall(r'[A-Za-z]{2,}', text.lower())
word_count = Counter(words)
print(word_count)
# 输出: Counter({'python': 2, 'pandas': 1, 'numpy': 1})
```

---

> **小结**：文本清洗的核心是"模式思维"——先观察数据规律，再设计正则模式。建议在 [regex101.com](https://regex101.com) 等在线工具中先验证模式，再应用到 Pandas 批量处理中。掌握 `re.sub`、`re.findall`、`str.extract` 三个核心方法，即可覆盖 90% 以上的文本清洗需求。