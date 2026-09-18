# 流程控制与函数

> 模块：Python基础速成 | 编号：第2讲 | Python数据分析实战

## 1. 概念

流程控制（Flow Control）是程序设计中用于控制代码执行顺序和逻辑分支的机制，主要包括条件判断（`if`/`elif`/`else`）和循环（`for`/`while`）。函数（Function）则是将一段可复用的逻辑封装起来，通过参数传递输入、通过返回值输出结果的代码块。

在数据分析场景中，流程控制用于数据清洗时的条件筛选、异常值处理、分箱操作等；函数则用于封装重复的数据处理步骤（如缺失值填充、标准化），提高代码的复用性和可读性。

**生活化类比**：流程控制就像你在超市购物时的决策过程——"如果苹果打折就买两斤，否则买一斤"（条件判断）；"逐个检查购物清单上的每件商品是否已放入购物车"（循环）。函数则像超市的收银台——你只需把商品（参数）递过去，收银台（函数）就会按固定流程计算出总价（返回值），无需关心内部如何计算。

## 2. 核心API与原理

| API/语法 | 签名/格式 | 参数说明 | 返回值 | 说明 |
|-----------|-----------|----------|--------|------|
| `if` 语句 | `if condition: ... elif condition: ... else: ...` | `condition` 为布尔表达式 | 无（执行分支代码块） | 按顺序判断条件，执行第一个为 `True` 的分支 |
| `for` 循环 | `for item in iterable: ...` | `iterable` 为可迭代对象（列表、元组、字典、`range()` 等） | 无 | 遍历可迭代对象中的每个元素 |
| `while` 循环 | `while condition: ...` | `condition` 为布尔表达式 | 无 | 当条件为 `True` 时重复执行循环体，需注意更新条件避免死循环 |
| `range()` | `range(start, stop, step)` | `start` 起始值（含，默认0）；`stop` 结束值（不含，必填）；`step` 步长（默认1） | 返回 `range` 对象（惰性序列） | 常用于 `for` 循环中生成整数序列 |
| `def` 定义函数 | `def function_name(param1, param2=default): ... return value` | 参数支持位置参数、默认参数、关键字参数 | 由 `return` 指定；无 `return` 则返回 `None` | 定义可复用的代码块，支持默认参数和多种传参方式 |

## 3. 代码示例

### 示例 1：条件判断——根据成绩划分等级（入门）

```python
# 示例：根据分数划分等级
score = 85

if score >= 90:
    grade = "优秀"
elif score >= 80:
    grade = "良好"
elif score >= 60:
    grade = "及格"
else:
    grade = "不及格"

print(f"分数 {score} 对应的等级是：{grade}")
# 输出：分数 85 对应的等级是：良好
```

### 示例 2：循环与 `range()`——计算列表中的正数之和（进阶）

```python
# 示例：遍历列表，累加所有正数
numbers = [3, -1, 5, -7, 2, 0, 8]
positive_sum = 0

for num in numbers:
    if num > 0:
        positive_sum += num

print(f"正数之和为：{positive_sum}")
# 输出：正数之和为：18

# 使用 range() 生成 1-5 的平方
squares = []
for i in range(1, 6):
    squares.append(i ** 2)
print(f"1到5的平方：{squares}")
# 输出：1到5的平方：[1, 4, 9, 16, 25]
```

### 示例 3：定义函数——封装数据标准化逻辑（综合）

```python
# 示例：定义一个函数，对列表进行 Z-score 标准化（均值为0，标准差为1）
def zscore_normalize(data, ddof=0):
    """
    对数值列表进行 Z-score 标准化。
    参数：
        data: 数值列表
        ddof: 标准差计算时的自由度修正（0表示总体标准差，1表示样本标准差）
    返回：
        标准化后的列表
    """
    n = len(data)
    if n == 0:
        return []
    
    mean = sum(data) / n
    # 计算标准差
    variance = sum((x - mean) ** 2 for x in data) / (n - ddof)
    std = variance ** 0.5
    
    if std == 0:
        # 标准差为0时，所有值相同，返回全0列表
        return [0.0] * n
    
    return [(x - mean) / std for x in data]

# 测试函数
raw_data = [10, 20, 30, 40, 50]
normalized = zscore_normalize(raw_data, ddof=1)
print(f"原始数据：{raw_data}")
print(f"标准化后：{[round(x, 2) for x in normalized]}")
# 输出：原始数据：[10, 20, 30, 40, 50]
# 输出：标准化后：[-1.41, -0.71, 0.0, 0.71, 1.41]

# 使用 while 循环模拟重试机制
attempt = 0
while attempt < 3:
    attempt += 1
    print(f"第 {attempt} 次尝试...")
    if attempt == 2:
        print("成功！")
        break
# 输出：第 1 次尝试...
# 输出：第 2 次尝试...
# 输出：成功！
```

## 4. 常见错误

### 错误 1：忘记冒号或缩进错误

```python
# 错误写法：if 语句末尾缺少冒号
# if score > 60
#     print("及格")

# 错误写法：缩进不一致
# if score > 60:
#     print("及格")
#   print("继续执行")  # 缩进不一致会报错

# 正确写法
score = 75
if score > 60:
    print("及格")
    print("继续执行")
# 输出：及格
# 输出：继续执行
```

**原因**：Python 使用冒号和缩进（通常4个空格）来定义代码块，缺少冒号或不一致的缩进会导致 `IndentationError` 或 `SyntaxError`。

### 错误 2：`while` 循环条件永远为真，导致死循环

```python
# 错误写法：忘记更新循环变量
# count = 0
# while count < 5:
#     print(count)
#     # 缺少 count += 1，count 永远为0，无限循环

# 正确写法
count = 0
while count < 5:
    print(count, end=" ")
    count += 1
print()  # 换行
# 输出：0 1 2 3 4
```

**原因**：`while` 循环依赖条件变化退出循环。若循环体内没有修改条件中涉及的变量，条件永远为 `True`，程序将无限执行。使用 `Ctrl+C` 可强制中断。

### 错误 3：函数定义后忘记调用，或 `return` 位置错误

```python
# 错误写法：定义了函数但未调用，且 return 在循环内提前返回
# def find_max(nums):
#     for n in nums:
#         return n  # 错误！第一次循环就返回，只返回第一个元素

# 正确写法
def find_max(nums):
    max_val = nums[0]
    for n in nums:
        if n > max_val:
            max_val = n
    return max_val  # 循环结束后返回

result = find_max([3, 7, 2, 9, 5])
print(f"最大值是：{result}")
# 输出：最大值是：9
```

**原因**：`return` 会立即终止函数执行并返回结果。若放在循环内部，函数在第一次迭代时就退出，无法完成完整逻辑。另外，定义函数后必须显式调用（`函数名()`）才会执行。

## 5. 练习

### 练习 1：实现一个温度转换函数

编写一个函数 `convert_temperature(value, unit)`，当 `unit` 为 `'C'` 时将摄氏温度转换为华氏温度（公式：`F = C * 9/5 + 32`），当 `unit` 为 `'F'` 时将华氏温度转换为摄氏温度（公式：`C = (F - 32) * 5/9`）。要求使用 `if/elif/else` 处理单位判断，并处理无效单位的情况（返回 `None` 并打印提示）。

**答案提示**：
```python
def convert_temperature(value, unit):
    if unit == 'C':
        return value * 9 / 5 + 32
    elif unit == 'F':
        return (value - 32) * 5 / 9
    else:
        print("无效单位，请输入 'C' 或 'F'")
        return None

# 测试
print(convert_temperature(100, 'C'))  # 212.0
print(convert_temperature(32, 'F'))   # 0.0
```

### 练习 2：统计字符串中元音字母的个数

使用 `for` 循环遍历一个字符串，统计其中元音字母（`a, e, i, o, u`，不区分大小写）出现的次数。要求忽略非字母字符，并输出统计结果。

**答案提示**：
```python
def count_vowels(text):
    vowels = set('aeiouAEIOU')  # 使用集合便于快速判断
    count = 0
    for char in text:
        if char in vowels:
            count += 1
    return count

# 测试
sentence = "Hello, Python Data Analysis!"
print(f"元音字母个数：{count_vowels(sentence)}")
# 输出：元音字母个数：8
```

**进阶思考**：若需要同时统计每个元音字母分别出现的次数，可以使用字典（`dict`）来记录，尝试修改函数实现这一功能。