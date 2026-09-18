# Scikit-learn数据划分训练测试集

> 来源: Scikit-learn 官方文档: Model Selection | source_type: curated | canonical_name: Scikit-learn数据划分训练测试集

> aliases: train_test_split, 随机种子, 分层抽样, 数据泄漏

## train_test_split

train_test_split 是 Python 数据分析中的核心概念。本节详细讲解其定义、用法和常见场景，帮助学习者掌握正确的使用方式。

### 基本概念

train_test_split 的基本概念包括其语法形式、适用场景和与其他概念的关联。正确理解和使用 train_test_split 可以显著提升代码的可读性和效率。

### 使用示例

```python
import numpy as np
from sklearn.model_selection import train_test_split
X=np.arange(100).reshape(50,2)
y=np.array([0]*25+[1]*25)
X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.2,random_state=42,stratify=y)
print(f"Train:{X_train.shape},Test:{X_test.shape}")
```

### 常见错误

- 注意 train_test_split 与相似功能的区别，避免混淆
- 运行时常见报错：检查数据类型、导入模块和语法正确性

### 练习要点

- 动手实践：修改上述示例代码并观察输出变化
- 思考题：Scikit-learn数据划分训练测试集 在实际数据分析项目中的应用场景

---
*本知识库内容来自 Scikit-learn 官方文档: Model Selection 及 LearnMate 教学团队整理。*
## 随机种子

随机种子 是 Python 数据分析中的核心概念。本节详细讲解其定义、用法和常见场景，帮助学习者掌握正确的使用方式。

### 基本概念

随机种子 的基本概念包括其语法形式、适用场景和与其他概念的关联。正确理解和使用 随机种子 可以显著提升代码的可读性和效率。

### 使用示例

```python
import numpy as np
from sklearn.model_selection import train_test_split
X=np.arange(100).reshape(50,2)
y=np.array([0]*25+[1]*25)
X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.2,random_state=42,stratify=y)
print(f"Train:{X_train.shape},Test:{X_test.shape}")
```

### 常见错误

- 注意 随机种子 与相似功能的区别，避免混淆
- 运行时常见报错：检查数据类型、导入模块和语法正确性

### 练习要点

- 动手实践：修改上述示例代码并观察输出变化
- 思考题：Scikit-learn数据划分训练测试集 在实际数据分析项目中的应用场景

---
*本知识库内容来自 Scikit-learn 官方文档: Model Selection 及 LearnMate 教学团队整理。*
## 分层抽样

分层抽样 是 Python 数据分析中的核心概念。本节详细讲解其定义、用法和常见场景，帮助学习者掌握正确的使用方式。

### 基本概念

分层抽样 的基本概念包括其语法形式、适用场景和与其他概念的关联。正确理解和使用 分层抽样 可以显著提升代码的可读性和效率。

### 使用示例

```python
import numpy as np
from sklearn.model_selection import train_test_split
X=np.arange(100).reshape(50,2)
y=np.array([0]*25+[1]*25)
X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.2,random_state=42,stratify=y)
print(f"Train:{X_train.shape},Test:{X_test.shape}")
```

### 常见错误

- 注意 分层抽样 与相似功能的区别，避免混淆
- 运行时常见报错：检查数据类型、导入模块和语法正确性

### 练习要点

- 动手实践：修改上述示例代码并观察输出变化
- 思考题：Scikit-learn数据划分训练测试集 在实际数据分析项目中的应用场景

---
*本知识库内容来自 Scikit-learn 官方文档: Model Selection 及 LearnMate 教学团队整理。*
