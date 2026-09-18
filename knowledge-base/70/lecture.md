# Pandas数据筛选与条件过滤

> 来源: Pandas 官方文档: Indexing and Selecting Data | source_type: curated | canonical_name: Pandas数据筛选与条件过滤

> aliases: 布尔索引, query, loc, isin, 条件组合

## 布尔索引

布尔索引 是 Python 数据分析中的核心概念。本节详细讲解其定义、用法和常见场景，帮助学习者掌握正确的使用方式。

### 基本概念

布尔索引 的基本概念包括其语法形式、适用场景和与其他概念的关联。正确理解和使用 布尔索引 可以显著提升代码的可读性和效率。

### 使用示例

```python
import pandas as pd
df = pd.DataFrame({"A":[1,2,3,4,5],"B":[10,20,30,40,50],"C":["a","b","a","c","b"]})
print(df[df["A"] > 2])
print(df.query("B >= 30"))
print(df.loc[df["C"].isin(["a","b"])])
print(df[(df["A"]>2) & (df["C"]=="a")])
```

### 常见错误

- 注意 布尔索引 与相似功能的区别，避免混淆
- 运行时常见报错：检查数据类型、导入模块和语法正确性

### 练习要点

- 动手实践：修改上述示例代码并观察输出变化
- 思考题：Pandas数据筛选与条件过滤 在实际数据分析项目中的应用场景

---
*本知识库内容来自 Pandas 官方文档: Indexing and Selecting Data 及 LearnMate 教学团队整理。*
## query

query 是 Python 数据分析中的核心概念。本节详细讲解其定义、用法和常见场景，帮助学习者掌握正确的使用方式。

### 基本概念

query 的基本概念包括其语法形式、适用场景和与其他概念的关联。正确理解和使用 query 可以显著提升代码的可读性和效率。

### 使用示例

```python
import pandas as pd
df = pd.DataFrame({"A":[1,2,3,4,5],"B":[10,20,30,40,50],"C":["a","b","a","c","b"]})
print(df[df["A"] > 2])
print(df.query("B >= 30"))
print(df.loc[df["C"].isin(["a","b"])])
print(df[(df["A"]>2) & (df["C"]=="a")])
```

### 常见错误

- 注意 query 与相似功能的区别，避免混淆
- 运行时常见报错：检查数据类型、导入模块和语法正确性

### 练习要点

- 动手实践：修改上述示例代码并观察输出变化
- 思考题：Pandas数据筛选与条件过滤 在实际数据分析项目中的应用场景

---
*本知识库内容来自 Pandas 官方文档: Indexing and Selecting Data 及 LearnMate 教学团队整理。*
## loc

loc 是 Python 数据分析中的核心概念。本节详细讲解其定义、用法和常见场景，帮助学习者掌握正确的使用方式。

### 基本概念

loc 的基本概念包括其语法形式、适用场景和与其他概念的关联。正确理解和使用 loc 可以显著提升代码的可读性和效率。

### 使用示例

```python
import pandas as pd
df = pd.DataFrame({"A":[1,2,3,4,5],"B":[10,20,30,40,50],"C":["a","b","a","c","b"]})
print(df[df["A"] > 2])
print(df.query("B >= 30"))
print(df.loc[df["C"].isin(["a","b"])])
print(df[(df["A"]>2) & (df["C"]=="a")])
```

### 常见错误

- 注意 loc 与相似功能的区别，避免混淆
- 运行时常见报错：检查数据类型、导入模块和语法正确性

### 练习要点

- 动手实践：修改上述示例代码并观察输出变化
- 思考题：Pandas数据筛选与条件过滤 在实际数据分析项目中的应用场景

---
*本知识库内容来自 Pandas 官方文档: Indexing and Selecting Data 及 LearnMate 教学团队整理。*
