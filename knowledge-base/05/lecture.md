# 常用标准库(os/datetime/collections)

> 模块：Python基础速成 | 编号：第5讲 | Python数据分析实战

---

## 1. 概念

Python 标准库是 Python 安装时自带的模块集合，无需额外安装即可导入使用。本讲聚焦三个在数据分析中高频使用的标准库：

- **os**：提供与操作系统交互的接口，用于文件路径操作、目录遍历、环境变量读取等。在数据分析中，我们经常需要批量读取数据文件、创建输出目录，os 库是文件管理的基石。
- **datetime**：提供日期和时间的处理能力，支持日期运算、格式化输出、时间差计算。数据分析中，时间序列数据的清洗、按时间聚合、时间窗口划分都离不开它。
- **collections**：提供额外的容器数据类型，如计数器（Counter）、默认字典（defaultdict）、有序字典（OrderedDict）等。它们能显著简化数据统计和分组逻辑的代码。

**生活化类比**：os 就像你的文件柜管理员，帮你找到文件、创建文件夹；datetime 就像你的日历和手表，帮你记录和计算时间；collections 就像你的多功能工具箱，里面有各种特制的收纳盒（计数器、默认字典等），让整理数据更高效。

---

## 2. 核心API与原理

| 模块 | API | 签名 | 参数说明 | 返回值 |
|------|-----|------|----------|--------|
| os | `os.path.join()` | `os.path.join(a, *p)` | `a`: 路径首段；`*p`: 后续路径段 | 拼接后的完整路径字符串 |
| os | `os.listdir()` | `os.listdir(path='.')` | `path`: 目录路径，默认当前目录 | 目录下所有文件名和子目录名的列表 |
| os | `os.makedirs()` | `os.makedirs(name, mode=0o777, exist_ok=False)` | `name`: 要创建的目录路径；`exist_ok`: 若为True且目录已存在则不报错 | 无返回值，创建目录 |
| datetime | `datetime.datetime.now()` | `datetime.datetime.now(tz=None)` | `tz`: 时区对象，默认本地时区 | 当前日期时间的 datetime 对象 |
| datetime | `datetime.datetime.strftime()` | `dt.strftime(format)` | `format`: 格式化字符串，如 `%Y-%m-%d` | 按格式输出的日期时间字符串 |
| datetime | `datetime.datetime.strptime()` | `datetime.datetime.strptime(date_string, format)` | `date_string`: 日期字符串；`format`: 对应的格式 | 解析出的 datetime 对象 |
| collections | `collections.Counter()` | `collections.Counter(iterable=None)` | `iterable`: 可迭代对象（列表、字符串等） | 计数器对象，元素为键、频次为值 |
| collections | `collections.defaultdict()` | `collections.defaultdict(default_factory)` | `default_factory`: 工厂函数，如 `list`、`int` | 默认字典对象，访问不存在的键时自动创建默认值 |
| collections | `collections.OrderedDict()` | `collections.OrderedDict()` | 无 | 有序字典对象，保持键的插入顺序 |

**常用日期格式化符号**：`%Y`（四位年份）、`%m`（两位月份）、`%d`（两位日期）、`%H`（24小时制小时）、`%M`（分钟）、`%S`（秒）。

---

## 3. 代码示例

### 示例1：使用 os 批量管理数据文件（入门）

```python
import os

# 创建数据输出目录（如果不存在）
output_dir = "./output"
os.makedirs(output_dir, exist_ok=True)
print(f"目录已创建或已存在: {output_dir}")

# 列出当前目录下的所有文件和文件夹
current_files = os.listdir(".")
print(f"当前目录下的内容: {current_files}")

# 拼接文件路径（跨平台安全写法）
data_path = os.path.join(output_dir, "sales_data.csv")
print(f"拼接后的数据文件路径: {data_path}")

# 检查文件是否存在
print(f"文件是否存在: {os.path.exists(data_path)}")
```

**输出结果**：
```
目录已创建或已存在: ./output
当前目录下的内容: ['output', 'example.py', ...]
拼接后的数据文件路径: output/sales_data.csv
文件是否存在: False
```

### 示例2：使用 datetime 处理时间序列数据（进阶）

```python
from datetime import datetime, timedelta

# 获取当前时间
now = datetime.now()
print(f"当前时间: {now}")

# 格式化输出
formatted = now.strftime("%Y年%m月%d日 %H:%M:%S")
print(f"格式化时间: {formatted}")

# 解析字符串为 datetime 对象
date_str = "2024-03-15 14:30:00"
parsed_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
print(f"解析后的日期: {parsed_date}")

# 时间运算：计算7天前的日期
seven_days_ago = now - timedelta(days=7)
print(f"7天前的日期: {seven_days_ago.strftime('%Y-%m-%d')}")

# 计算两个日期之间的天数差
delta = now - parsed_date
print(f"距离2024-03-15已经过去: {delta.days} 天")
```

**输出结果**：
```
当前时间: 2024-03-22 10:30:45.123456
格式化时间: 2024年03月22日 10:30:45
解析后的日期: 2024-03-15 14:30:00
7天前的日期: 2024-03-15
距离2024-03-15已经过去: 7 天
```

### 示例3：使用 collections 进行数据统计与分组（综合应用）

```python
from collections import Counter, defaultdict, OrderedDict
import random

# 模拟一组销售数据：城市和销售额
cities = ["北京", "上海", "广州", "深圳", "北京", "上海", "北京"]
sales = [100, 200, 150, 300, 120, 180, 90]

# 使用 Counter 统计各城市出现次数
city_counter = Counter(cities)
print(f"各城市销售记录数: {dict(city_counter)}")
print(f"出现最多的城市: {city_counter.most_common(1)}")

# 使用 defaultdict 按城市分组销售额
city_sales = defaultdict(list)
for city, amount in zip(cities, sales):
    city_sales[city].append(amount)

print(f"按城市分组销售额: {dict(city_sales)}")

# 使用 defaultdict(int) 统计各城市总销售额
city_total = defaultdict(int)
for city, amount in zip(cities, sales):
    city_total[city] += amount

print(f"各城市总销售额: {dict(city_total)}")

# 使用 OrderedDict 保持排序后的顺序
sorted_cities = OrderedDict(sorted(city_total.items(), key=lambda x: x[1], reverse=True))
print(f"按销售额降序排列: {dict(sorted_cities)}")
```

**输出结果**：
```
各城市销售记录数: {'北京': 3, '上海': 2, '广州': 1, '深圳': 1}
出现最多的城市: [('北京', 3)]
按城市分组销售额: {'北京': [100, 120, 90], '上海': [200, 180], '广州': [150], '深圳': [300]}
各城市总销售额: {'北京': 310, '上海': 380, '广州': 150, '深圳': 300}
按销售额降序排列: {'上海': 380, '北京': 310, '深圳': 300, '广州': 150}
```

---

## 4. 常见错误

### 错误1：使用字符串拼接路径导致跨平台问题

```python
# 错误写法
import os
path = "./data" + "/" + "file.csv"  # 在Windows上可能出错

# 正确写法
path = os.path.join("data", "file.csv")  # 自动适配操作系统分隔符
```

**原因**：Windows 使用反斜杠 `\`，Linux/macOS 使用正斜杠 `/`。手动拼接会导致代码在其他平台运行时路径错误。

### 错误2：strptime 格式字符串与日期字符串不匹配

```python
# 错误写法
from datetime import datetime
date_str = "2024/03/15"
# 下面这行会报错，因为格式不匹配
# parsed = datetime.strptime(date_str, "%Y-%m-%d")

# 正确写法
parsed = datetime.strptime(date_str, "%Y/%m/%d")
print(parsed)  # 输出: 2024-03-15 00:00:00
```

**原因**：`strptime` 要求格式字符串与输入字符串严格匹配，`/` 和 `-` 不能混用。建议先统一数据格式再进行解析。

### 错误3：直接访问 defaultdict 中不存在的键时类型错误

```python
# 错误写法
from collections import defaultdict
d = defaultdict(list)
# 下面这行会报错，因为默认工厂是 list，不能直接加数字
# d["count"] += 1

# 正确写法
d2 = defaultdict(int)
d2["count"] += 1
print(d2["count"])  # 输出: 1

# 或者使用 list 默认工厂时，先 append
d["items"].append("apple")
print(d["items"])  # 输出: ['apple']
```

**原因**：`defaultdict` 的默认工厂决定了默认值的类型。`defaultdict(list)` 的默认值是空列表，不能直接做数值运算；需要数值统计时应使用 `defaultdict(int)`。

---

## 5. 练习

### 练习1：批量重命名文件（动手题）

编写一个函数，接收一个目录路径，将该目录下所有以 `.txt` 结尾的文件重命名为 `data_序号.txt` 格式（序号从1开始）。要求使用 `os.listdir()` 和 `os.rename()`。

**答案提示**：
```python
import os

def rename_txt_files(directory):
    files = os.listdir(directory)
    txt_files = [f for f in files if f.endswith(".txt")]
    for i, filename in enumerate(txt_files, start=1):
        old_path = os.path.join(directory, filename)
        new_path = os.path.join(directory, f"data_{i}.txt")
        os.rename(old_path, new_path)
        print(f"已重命名: {filename} -> data_{i}.txt")
```

### 练习2：时间序列数据统计（思考题）

给定一个包含日期字符串的列表 `dates = ["2024-01-05", "2024-01-15", "2024-02-03", "2024-02-20", "2024-03-10"]`，请使用 `datetime` 和 `collections.Counter` 统计每个月各有多少条记录，并按月份排序输出。

**答案提示**：
```python
from datetime import datetime
from collections import Counter

dates = ["2024-01-05", "2024-01-15", "2024-02-03", "2024-02-20", "2024-03-10"]
months = [datetime.strptime(d, "%Y-%m-%d").strftime("%Y-%m") for d in dates]
month_counter = Counter(months)
for month in sorted(month_counter.keys()):
    print(f"{month}: {month_counter[month]}条记录")
# 输出:
# 2024-01: 2条记录
# 2024-02: 2条记录
# 2024-03: 1条记录
```