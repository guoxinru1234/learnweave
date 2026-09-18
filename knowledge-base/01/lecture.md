# Python数据类型与运算符
> 模块：Python基础速成 | 编号：第1讲 | Python数据分析实战

## 1. 概念

Python 数据类型（Data Types）是变量在内存中存储数据的格式规范，它决定了数据可以执行哪些操作以及如何被存储。Python 是**动态类型**语言，变量无需显式声明类型，解释器会根据赋值自动推断。核心内置类型包括：`int`（整数）、`float`（浮点数）、`str`（字符串）、`bool`（布尔值）、`list`（列表）、`tuple`（元组）、`dict`（字典）和 `set`（集合）。

运算符（Operators）是用于对数据进行运算的符号，Python 提供了算术（`+ - * / // % **`）、比较（`== != > < >= <=`）、逻辑（`and or not`）、赋值（`=`、`+=` 等）和成员（`in`）等运算符。

**生活化类比**：把数据类型想象成不同形状的容器——整数是"方盒"（只能装整数），字符串是"长条袋"（装文本），列表是"多层抽屉"（可装任意物品且可增减）。运算符则是"加工工具"——加法像"合并两堆物品"，比较像"用秤称重判断哪个更重"。选对容器和工具，才能高效完成数据加工任务。

## 2. 核心API与原理

| API/函数 | 签名 | 参数说明 | 返回值 | 用途 |
|---------|------|---------|--------|------|
| `type()` | `type(object)` | `object`：任意 Python 对象 | 返回对象的类型对象（如 `<class 'int'>`） | 查看变量数据类型 |
| `int()` | `int(x, base=10)` | `x`：数字或字符串；`base`：进制（默认10） | 返回整数 | 将字符串/浮点数转为整数 |
| `float()` | `float(x)` | `x`：数字或字符串 | 返回浮点数 | 将其他类型转为浮点数 |
| `str()` | `str(object='')` | `object`：任意对象 | 返回字符串 | 将对象转为字符串 |
| `len()` | `len(s)` | `s`：序列（字符串、列表、元组等） | 返回元素个数（整数） | 获取序列长度 |
| `isinstance()` | `isinstance(obj, classinfo)` | `obj`：对象；`classinfo`：类型或类型元组 | 返回 `True`/`False` | 判断对象是否属于指定类型 |

**原理说明**：Python 中一切皆对象，每个对象都有类型。`type()` 和 `isinstance()` 是类型检查的两把"尺子"，前者返回精确类型，后者支持继承关系判断（在数据分析中常用于校验 DataFrame 列类型）。类型转换函数（`int`/`float`/`str`）不会修改原对象，而是**返回新对象**——这体现了 Python 数据类型的不可变性（对不可变类型而言）。

## 3. 代码示例

### 示例1：基础类型与运算符（入门）

```python
# 示例1：基础类型与运算符
age = 25                # int 类型
price = 19.99           # float 类型
name = "Alice"          # str 类型
is_student = True       # bool 类型

# 查看类型
print(type(age))        # 输出: <class 'int'>
print(type(price))      # 输出: <class 'float'>

# 算术运算
total = age + 5         # 加法: 30
remainder = 10 % 3      # 取余: 1
power = 2 ** 3          # 幂运算: 8
floor_div = 7 // 2      # 整除: 3

# 字符串拼接与重复
greeting = "Hello, " + name   # 拼接: "Hello, Alice"
laugh = "ha" * 3              # 重复: "hahaha"

# 比较与逻辑运算
print(age > 18 and is_student)  # 输出: True
print(price == 20 or age < 20)  # 输出: False
```

**输出结果**：
```
<class 'int'>
<class 'float'>
True
False
```

### 示例2：类型转换与列表操作（进阶）

```python
# 示例2：类型转换与列表操作
# 字符串转数字（数据分析中读取CSV后常用）
num_str = "42"
num_int = int(num_str)          # 字符串转整数
num_float = float("3.14")       # 字符串转浮点数
print(num_int + 8)              # 输出: 50

# 数字转字符串（用于拼接输出）
score = 95
message = "你的分数是: " + str(score)
print(message)                  # 输出: 你的分数是: 95

# 列表的基本操作
fruits = ["apple", "banana", "cherry"]
fruits.append("orange")         # 添加元素
fruits.remove("banana")         # 删除元素
print(len(fruits))              # 输出: 3
print(fruits[0])                # 输出: apple（索引从0开始）

# 类型检查
print(isinstance(age, int))     # 输出: True
print(isinstance(price, int))   # 输出: False
```

**输出结果**：
```
50
你的分数是: 95
3
apple
True
False
```

### 示例3：字典与集合（数据分析场景）

```python
# 示例3：字典与集合（数据分析场景）
# 字典：存储键值对（类似数据库记录）
student = {
    "name": "Bob",
    "age": 22,
    "scores": [85, 92, 78]      # 值可以是列表
}

# 访问与修改字典
print(student["name"])          # 输出: Bob
student["age"] = 23             # 修改值
student["major"] = "Math"       # 新增键值对
print(student.keys())           # 输出: dict_keys(['name', 'age', 'scores', 'major'])

# 集合：去重与集合运算
course_a = {"Math", "Physics", "CS"}
course_b = {"CS", "Biology", "Chemistry"}
common = course_a & course_b    # 交集: {"CS"}
all_courses = course_a | course_b  # 并集
print(common)                   # 输出: {'CS'}
print(len(all_courses))         # 输出: 5

# 成员运算符
print("Math" in course_a)       # 输出: True
print("CS" in course_a)         # 输出: True
```

**输出结果**：
```
Bob
dict_keys(['name', 'age', 'scores', 'major'])
{'CS'}
5
True
True
```

## 4. 常见错误

### 错误1：类型不匹配导致运算失败
```python
# 错误写法
age = "25"          # 字符串类型
total = age + 5     # TypeError: can only concatenate str (not "int") to str

# 正确写法
age = "25"
total = int(age) + 5    # 先转换再运算
print(total)            # 输出: 30
```
**原因**：Python 不会自动将字符串转为数字进行算术运算，需要显式调用 `int()` 或 `float()` 转换。

### 错误2：混淆 `=` 与 `==`
```python
# 错误写法
x = 10
if x = 5:           # SyntaxError: invalid syntax
    print("x is 5")

# 正确写法
x = 10
if x == 5:          # 使用双等号进行比较
    print("x is 5")
else:
    print("x is not 5")   # 输出: x is not 5
```
**原因**：`=` 是赋值运算符，`==` 是比较运算符。新手常将两者混淆，导致语法错误或逻辑错误。

### 错误3：列表索引越界
```python
# 错误写法
fruits = ["apple", "banana"]
print(fruits[2])    # IndexError: list index out of range

# 正确写法
fruits = ["apple", "banana"]
if len(fruits) > 2:     # 先检查长度
    print(fruits[2])
else:
    print("索引超出范围")   # 输出: 索引超出范围
```
**原因**：列表索引从 0 开始，最大索引为 `len(list) - 1`。访问不存在的索引会抛出 `IndexError`，应先用 `len()` 检查长度或使用负数索引（如 `fruits[-1]` 访问最后一个元素）。

## 5. 练习

### 练习1：温度转换器
编写一个程序，将摄氏温度转换为华氏温度。要求：
- 使用 `input()` 接收用户输入的摄氏温度（字符串类型）
- 转换为 `float` 类型后，用公式 `F = C * 9/5 + 32` 计算
- 输出结果保留 2 位小数

**答案提示**：
```python
celsius_str = input("请输入摄氏温度: ")
celsius = float(celsius_str)
fahrenheit = celsius * 9/5 + 32
print(f"华氏温度: {fahrenheit:.2f}")  # 使用 f-string 格式化
```

### 练习2：学生成绩统计
给定一个字典 `grades = {"Alice": [85, 90, 92], "Bob": [78, 82, 80], "Carol": [95, 88, 91]}`，完成以下任务：
1. 计算每个学生的平均分，存入新字典
2. 找出平均分最高的学生姓名
3. 统计所有成绩中大于等于 90 分的个数

**答案提示**：
```python
grades = {"Alice": [85, 90, 92], "Bob": [78, 82, 80], "Carol": [95, 88, 91]}
averages = {}
for name, scores in grades.items():
    averages[name] = sum(scores) / len(scores)

best_student = max(averages, key=averages.get)  # 获取平均分最高的键

all_scores = [s for scores in grades.values() for s in scores]
count_90 = sum(1 for s in all_scores if s >= 90)

print(f"平均分: {averages}")
print(f"最高分学生: {best_student}")
print(f"90分以上个数: {count_90}")
```