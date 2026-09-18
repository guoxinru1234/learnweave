# 文件读写与异常处理
> 模块：Python基础速成 | 编号：第4讲 | Python数据分析实战

## 1. 概念

文件读写（File I/O）是程序与外部存储设备（硬盘、U盘等）进行数据交换的过程。在数据分析中，我们经常需要从 CSV、TXT、JSON 等文件中读取原始数据，经过处理后，再将结果写回新文件。异常处理（Exception Handling）则是程序在运行过程中遇到错误（如文件不存在、磁盘空间不足、数据类型不匹配）时，能够优雅地捕获并处理这些错误，而不是让程序直接崩溃退出。

**生活化类比**：文件读写就像你去图书馆借书和还书——借书（读取文件）需要先找到书（打开文件），阅读内容（读取数据），最后归还（关闭文件）；还书（写入文件）则是把新内容记录到书本上。异常处理则像你出门前查看天气预报——如果预报有雨（可能出错），你就带上伞（异常处理），这样即使下雨（出错）也不会被淋湿（程序崩溃）。

**适用场景**：数据导入导出、日志记录、配置文件读取、批量处理多个数据文件、网络请求容错等。

## 2. 核心API与原理

| API/方法 | 签名 | 参数说明 | 返回值 | 说明 |
|---------|------|---------|--------|------|
| `open()` | `open(file, mode='r', encoding=None)` | `file`: 文件路径字符串；`mode`: 打开模式，常用 `'r'` 读、`'w'` 写（覆盖）、`'a'` 追加、`'rb'`/`'wb'` 二进制；`encoding`: 字符编码，如 `'utf-8'` | 文件对象 | 打开文件，返回文件对象；文件不存在且模式为 `'w'` 或 `'a'` 时自动创建 |
| `file.read()` | `read(size=-1)` | `size`: 读取字节数，默认 `-1` 表示读取全部 | 字符串（文本模式）或字节（二进制模式） | 一次性读取整个文件内容 |
| `file.readline()` | `readline(size=-1)` | `size`: 读取的最大字符数 | 字符串（含换行符） | 逐行读取，适合处理大文件 |
| `file.write()` | `write(str)` | `str`: 要写入的字符串 | 写入的字符数 | 将字符串写入文件，需手动添加换行符 `\n` |
| `try-except` | `try: ... except Exception as e: ...` | `Exception` 可替换为具体异常类型（如 `FileNotFoundError`、`ValueError`） | 无 | 捕获并处理异常，`as e` 可获取异常对象 |

**核心原理**：`open()` 返回的文件对象是一个迭代器，支持 `for line in file` 逐行遍历。使用 `with open(...) as f:` 语句可以自动管理文件生命周期，即使发生异常也会自动关闭文件，这是官方推荐的最佳实践。

## 3. 代码示例

### 示例1：基础文件读取与异常捕获（入门）

```python
# 尝试读取一个不存在的文件，演示异常处理
try:
    # 使用 with 语句自动管理文件关闭
    with open('sales_data.txt', 'r', encoding='utf-8') as f:
        content = f.read()
        print("文件内容：")
        print(content)
except FileNotFoundError:
    print("错误：文件 sales_data.txt 不存在！")
except PermissionError:
    print("错误：没有权限访问该文件！")

# 输出结果：
# 错误：文件 sales_data.txt 不存在！
```

### 示例2：逐行读取CSV数据并计算平均值（进阶）

```python
# 先创建一个示例数据文件
with open('temperatures.csv', 'w', encoding='utf-8') as f:
    f.write("城市,温度\n")
    f.write("北京,25\n")
    f.write("上海,28\n")
    f.write("广州,30\n")
    f.write("深圳,29\n")

# 逐行读取并计算平均温度
total_temp = 0
city_count = 0

try:
    with open('temperatures.csv', 'r', encoding='utf-8') as f:
        header = f.readline()  # 跳过表头
        print("表头:", header.strip())
        
        for line in f:
            # 去除换行符并按逗号分割
            parts = line.strip().split(',')
            if len(parts) == 2:  # 确保格式正确
                city, temp_str = parts
                try:
                    temp = float(temp_str)  # 可能引发 ValueError
                    total_temp += temp
                    city_count += 1
                    print(f"{city}: {temp}°C")
                except ValueError:
                    print(f"警告：{city} 的温度数据 '{temp_str}' 不是有效数字")
    
    if city_count > 0:
        avg_temp = total_temp / city_count
        print(f"\n平均温度: {avg_temp:.1f}°C")
    else:
        print("没有有效的温度数据")

except FileNotFoundError:
    print("错误：找不到文件 temperatures.csv")

# 输出结果：
# 表头: 城市,温度
# 北京: 25.0°C
# 上海: 28.0°C
# 广州: 30.0°C
# 深圳: 29.0°C
# 
# 平均温度: 28.0°C
```

### 示例3：数据写入与追加（进阶）

```python
# 将处理结果写入新文件
results = [
    {"城市": "北京", "温度": 25, "湿度": 60},
    {"城市": "上海", "温度": 28, "湿度": 75},
    {"城市": "广州", "温度": 30, "湿度": 85},
]

# 使用 'w' 模式写入新文件
with open('weather_summary.csv', 'w', encoding='utf-8') as f:
    f.write("城市,温度,湿度\n")  # 写入表头
    for item in results:
        line = f"{item['城市']},{item['温度']},{item['湿度']}\n"
        f.write(line)

print("已写入 weather_summary.csv")

# 使用 'a' 模式追加数据
new_record = {"城市": "深圳", "温度": 29, "湿度": 80}
with open('weather_summary.csv', 'a', encoding='utf-8') as f:
    f.write(f"{new_record['城市']},{new_record['温度']},{new_record['湿度']}\n")

# 验证写入结果
with open('weather_summary.csv', 'r', encoding='utf-8') as f:
    print("\n最终文件内容：")
    print(f.read())

# 输出结果：
# 已写入 weather_summary.csv
# 
# 最终文件内容：
# 城市,温度,湿度
# 北京,25,60
# 上海,28,75
# 广州,30,85
# 深圳,29,80
```

## 4. 常见错误

### 错误1：忘记关闭文件导致资源泄漏

```python
# 错误写法：没有关闭文件
f = open('data.txt', 'r')
content = f.read()
# 忘记调用 f.close()，文件句柄一直占用

# 正确写法：使用 with 语句自动管理
with open('data.txt', 'r') as f:
    content = f.read()
# 即使发生异常，文件也会自动关闭
```

### 错误2：编码问题导致乱码或UnicodeDecodeError

```python
# 错误写法：不指定编码，Windows 系统默认可能使用 GBK
with open('data.csv', 'r') as f:  # 如果文件是 UTF-8 编码，可能报错
    content = f.read()

# 正确写法：明确指定 UTF-8 编码
with open('data.csv', 'r', encoding='utf-8') as f:
    content = f.read()
```

### 错误3：在 except 块中吞掉所有异常，掩盖真实错误

```python
# 错误写法：捕获所有异常但什么都不做
try:
    num = int(input("请输入数字: "))
    result = 100 / num
except Exception:
    pass  # 静默失败，程序继续运行但结果未知

# 正确写法：针对性捕获，并给出明确提示
try:
    num = int(input("请输入数字: "))
    result = 100 / num
except ValueError:
    print("输入的不是有效数字！")
except ZeroDivisionError:
    print("不能除以零！")
else:
    print(f"计算结果: {result}")
```

## 5. 练习

### 练习1：日志记录器

编写一个函数 `log_message(message, log_file='app.log')`，将带时间戳的消息追加写入日志文件。要求：
- 使用 `datetime` 模块生成时间戳（格式：`2024-01-15 14:30:25`）
- 如果日志文件不存在，自动创建
- 每次调用追加一行：`[时间戳] 消息内容`
- 使用 `with` 语句确保文件正确关闭

**答案提示**：
```python
from datetime import datetime

def log_message(message, log_file='app.log'):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")
```

### 练习2：健壮的数据读取器

编写一个函数 `safe_read_csv(filepath)`，能够安全读取 CSV 文件并返回数据列表。要求：
- 处理 `FileNotFoundError`（文件不存在）
- 处理 `UnicodeDecodeError`（编码错误，尝试用 `'gbk'` 编码重新读取）
- 处理 `PermissionError`（无权限访问）
- 成功时返回 `(True, data_list)`，失败时返回 `(False, error_message)`

**答案提示**：
```python
def safe_read_csv(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = [line.strip().split(',') for line in f]
        return True, data
    except FileNotFoundError:
        return False, f"文件 {filepath} 不存在"
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='gbk') as f:
                data = [line.strip().split(',') for line in f]
            return True, data
        except Exception as e:
            return False, f"编码错误且无法用GBK读取: {e}"
    except PermissionError:
        return False, f"没有权限访问 {filepath}"
```