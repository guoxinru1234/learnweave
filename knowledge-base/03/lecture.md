# 列表推导式与生成器

> 模块：Python基础速成 | 编号：第3讲 | Python数据分析实战

---

## 1. 概念

列表推导式（List Comprehension）是 Python 中一种**基于现有可迭代对象快速创建新列表**的简洁语法。它由方括号 `[]` 包裹，内部包含一个表达式、一个或多个 `for` 子句以及可选的 `if` 条件。生成器（Generator）则是通过生成器表达式（Generator Expression，使用圆括号 `()`）或包含 `yield` 关键字的函数来创建**惰性求值**的迭代器，它不会一次性将所有元素载入内存，而是按需逐个生成。

**适用场景**：列表推导式适合数据量适中、需要立即使用全部结果的场景（如数据清洗、批量转换）；生成器适合处理海量数据（如读取大文件、流式处理）或需要节省内存的流水线操作。

**生活化类比**：列表推导式就像在超市一次性买齐一周的菜，所有食材立刻装进购物袋（内存）；而生成器则像在菜市场按需挑选，买一个吃一个，袋子始终很轻（内存占用小），但需要多次“跑腿”（迭代）。

---

## 2. 核心API与原理

| API / 语法 | 签名 / 写法 | 参数说明 | 返回值 | 原理简述 |
|---|---|---|---|---|
| **列表推导式** | `[expression for item in iterable if condition]` | `expression`：对 `item` 的运算表达式；`iterable`：任何可迭代对象；`condition`（可选）：过滤条件 | 新的 `list` 对象 | 对 `iterable` 中的每个元素依次执行 `condition` 判断，若为 `True` 则计算 `expression` 并收集结果 |
| **生成器表达式** | `(expression for item in iterable if condition)` | 参数含义与列表推导式相同 | 生成器对象（`generator`） | 惰性求值，仅在迭代时计算下一个值，不预先生成完整列表 |
| **`next()`** | `next(generator[, default])` | `generator`：生成器对象；`default`（可选）：迭代结束时的返回值 | 生成器的下一个元素；若无元素且未提供 `default` 则抛出 `StopIteration` | 手动驱动生成器前进一个元素 |
| **`yield`** | 在函数体内使用 `yield value` | `value`：每次迭代产出的值 | 生成器对象（当函数被调用时） | 函数执行到 `yield` 时暂停并返回值，下次 `next()` 调用时从暂停处继续 |

---

## 3. 代码示例

### 示例 1：基础列表推导式——数据清洗

```python
# 原始数据：包含字符串形式的数字和空字符串
raw_data = ['12', '34', '', '56', '78', 'abc']

# 使用列表推导式：过滤空字符串和非数字，转为整数
cleaned = [int(x) for x in raw_data if x.isdigit()]
print(cleaned)  # 输出: [12, 34, 56, 78]

# 等价于传统 for 循环写法（便于理解）
cleaned_loop = []
for x in raw_data:
    if x.isdigit():
        cleaned_loop.append(int(x))
print(cleaned_loop == cleaned)  # 输出: True
```

### 示例 2：生成器表达式——处理大文件

```python
# 模拟一个大型日志文件（实际场景中为真实文件对象）
def fake_log_file():
    for i in range(10):
        yield f"line_{i}: value={i * 2}"

# 使用生成器表达式逐行提取数字（惰性求值，内存占用恒定）
log_gen = fake_log_file()
numbers = (int(line.split('=')[1]) for line in log_gen if 'value=' in line)

# 逐个消费生成器
print(next(numbers))  # 输出: 0
print(next(numbers))  # 输出: 2
print(next(numbers))  # 输出: 4

# 也可以一次性转为列表（但会失去惰性优势）
all_numbers = list(numbers)
print(all_numbers)  # 输出: [6, 8, 10, 12, 14, 16, 18]
```

### 示例 3：进阶——嵌套推导式与 `yield` 生成器函数

```python
# 嵌套列表推导式：生成 3x3 乘法表
multiplication_table = [[i * j for j in range(1, 4)] for i in range(1, 4)]
print(multiplication_table)  # 输出: [[1, 2, 3], [2, 4, 6], [3, 6, 9]]

# 使用 yield 创建斐波那契数列生成器
def fibonacci(n):
    """生成前 n 个斐波那契数"""
    a, b = 0, 1
    count = 0
    while count < n:
        yield a
        a, b = b, a + b
        count += 1

# 消费生成器并求和
fib_gen = fibonacci(10)
fib_sum = sum(fib_gen)
print(fib_sum)  # 输出: 88（前10个斐波那契数之和）

# 生成器只能迭代一次，再次迭代为空
print(list(fibonacci(5)))  # 输出: [0, 1, 1, 2, 3]
print(list(fibonacci(5)))  # 输出: [0, 1, 1, 2, 3]（每次调用创建新生成器）
```

---

## 4. 常见错误

### 错误 1：混淆列表推导式与生成器表达式的括号

```python
# 错误写法：误用圆括号，得到生成器而非列表
wrong = (x * 2 for x in range(5))
print(type(wrong))  # <class 'generator'>，不是列表！

# 正确写法：需要列表时使用方括号
right = [x * 2 for x in range(5)]
print(type(right))  # <class 'list'>
```

**原因**：圆括号创建生成器表达式，方括号创建列表。若后续需要索引访问或多次遍历，应使用列表。

### 错误 2：在列表推导式中使用 `print` 或赋值语句

```python
# 错误写法：在推导式中执行副作用操作
# [print(x) for x in range(3)]  # 虽然能运行，但违背了推导式的纯函数原则

# 正确写法：用普通循环执行副作用
for x in range(3):
    print(x)  # 输出: 0 1 2

# 若确实需要收集结果，应返回表达式值
result = [x for x in range(3)]
print(result)  # 输出: [0, 1, 2]
```

**原因**：列表推导式用于**生成新列表**，不应包含 `print`、赋值等副作用语句。这会导致代码可读性差且难以调试。

### 错误 3：生成器被“用完”后仍尝试迭代

```python
# 错误写法：重复使用同一个生成器
gen = (x for x in range(3))
print(list(gen))  # 输出: [0, 1, 2]
print(list(gen))  # 输出: []，生成器已耗尽！

# 正确写法：需要多次遍历时，每次重新创建生成器
gen1 = (x for x in range(3))
gen2 = (x for x in range(3))
print(list(gen1))  # 输出: [0, 1, 2]
print(list(gen2))  # 输出: [0, 1, 2]
```

**原因**：生成器是**一次性**迭代器，迭代结束后即耗尽。若需重复使用，应重新创建或改用列表。

---

## 5. 练习

### 练习 1：数据转换与过滤

给定一个包含温度字符串的列表 `temps = ['23.5', '18', '30.2', 'invalid', '27']`，请使用列表推导式完成以下任务：
- 将所有有效温度转换为浮点数；
- 过滤掉无法转换的字符串；
- 将高于 25 度的温度标记为 `'hot'`，否则标记为 `'cool'`。

**答案提示**：可使用 `try...except` 或 `float(x)` 配合 `str.replace` 验证有效性。核心思路：`[('hot' if float(x) > 25 else 'cool') for x in temps if is_float(x)]`，其中 `is_float` 可用 `try: float(x); return True except ValueError: return False` 实现。

### 练习 2：生成器实现分块读取

编写一个生成器函数 `read_chunks(file_path, chunk_size=1024)`，用于逐块读取文件内容，每次返回指定大小的字节数据。要求：
- 使用 `with open(file_path, 'rb')` 打开文件；
- 循环中调用 `file.read(chunk_size)`，若返回空字节串则结束；
- 使用 `yield` 返回每个数据块。

**答案提示**：核心代码为 `while True: chunk = f.read(chunk_size); if not chunk: break; yield chunk`。此生成器可配合 `for chunk in read_chunks('data.bin'):` 使用，内存占用始终不超过 `chunk_size` 大小。