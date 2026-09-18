# NumPy随机数生成

> 来源: NumPy 官方文档: Random Sampling | source_type: curated | canonical_name: NumPy随机数生成

> aliases: random, seed, 分布, 可复现性, Generator

## random

random 是 Python 数据分析中的核心概念。本节详细讲解其定义、用法和常见场景，帮助学习者掌握正确的使用方式。

### 基本概念

random 的基本概念包括其语法形式、适用场景和与其他概念的关联。正确理解和使用 random 可以显著提升代码的可读性和效率。

### 使用示例

```python
import numpy as np
rng = np.random.default_rng(42)
print(rng.normal(0, 1, 5))
print(rng.uniform(0, 10, 5))
print(rng.integers(1, 100, 5))
rng2 = np.random.default_rng(42)
assert (rng.normal(0,1,5) == rng2.normal(0,1,5)).all()
```

### 常见错误

- 注意 random 与相似功能的区别，避免混淆
- 运行时常见报错：检查数据类型、导入模块和语法正确性

### 练习要点

- 动手实践：修改上述示例代码并观察输出变化
- 思考题：NumPy随机数生成 在实际数据分析项目中的应用场景

---
*本知识库内容来自 NumPy 官方文档: Random Sampling 及 LearnMate 教学团队整理。*
## seed

seed 是 Python 数据分析中的核心概念。本节详细讲解其定义、用法和常见场景，帮助学习者掌握正确的使用方式。

### 基本概念

seed 的基本概念包括其语法形式、适用场景和与其他概念的关联。正确理解和使用 seed 可以显著提升代码的可读性和效率。

### 使用示例

```python
import numpy as np
rng = np.random.default_rng(42)
print(rng.normal(0, 1, 5))
print(rng.uniform(0, 10, 5))
print(rng.integers(1, 100, 5))
rng2 = np.random.default_rng(42)
assert (rng.normal(0,1,5) == rng2.normal(0,1,5)).all()
```

### 常见错误

- 注意 seed 与相似功能的区别，避免混淆
- 运行时常见报错：检查数据类型、导入模块和语法正确性

### 练习要点

- 动手实践：修改上述示例代码并观察输出变化
- 思考题：NumPy随机数生成 在实际数据分析项目中的应用场景

---
*本知识库内容来自 NumPy 官方文档: Random Sampling 及 LearnMate 教学团队整理。*
## 分布

分布 是 Python 数据分析中的核心概念。本节详细讲解其定义、用法和常见场景，帮助学习者掌握正确的使用方式。

### 基本概念

分布 的基本概念包括其语法形式、适用场景和与其他概念的关联。正确理解和使用 分布 可以显著提升代码的可读性和效率。

### 使用示例

```python
import numpy as np
rng = np.random.default_rng(42)
print(rng.normal(0, 1, 5))
print(rng.uniform(0, 10, 5))
print(rng.integers(1, 100, 5))
rng2 = np.random.default_rng(42)
assert (rng.normal(0,1,5) == rng2.normal(0,1,5)).all()
```

### 常见错误

- 注意 分布 与相似功能的区别，避免混淆
- 运行时常见报错：检查数据类型、导入模块和语法正确性

### 练习要点

- 动手实践：修改上述示例代码并观察输出变化
- 思考题：NumPy随机数生成 在实际数据分析项目中的应用场景

---
*本知识库内容来自 NumPy 官方文档: Random Sampling 及 LearnMate 教学团队整理。*
