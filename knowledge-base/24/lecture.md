# 数据标准化与归一化
> 模块：数据清洗实战 | 编号：第24讲 | Python数据分析实战

## 1. 概念

数据标准化（Standardization）与归一化（Normalization）是数据预处理中两种最常用的**特征缩放（Feature Scaling）** 技术。它们的核心目的是消除不同特征之间因量纲（单位）和数量级差异带来的影响，使各特征在模型中具有同等的重要性。

- **归一化**：将数据缩放到一个固定的区间（通常是 `[0, 1]`），对数据的**分布形状**不敏感，适合数据有明显边界、需要保持稀疏性的场景（如图像像素值）。
- **标准化**：将数据转换为均值为 0、标准差为 1 的标准正态分布，对**异常值**的鲁棒性较好，适合数据近似服从正态分布、使用距离度量（如 SVM、KNN）或梯度下降优化算法的场景。

**生活化类比**：想象你要比较一个身高 180cm 的人和体重 70kg 的人谁"更大"。直接比较数字（180 vs 70）毫无意义，因为单位不同。归一化就像把两者都换算成百分制（身高 0.9 分、体重 0.7 分），标准化则像把两者都换算成"离平均水平的距离"（如身高 +2 个标准差、体重 -0.5 个标准差）。这样，不同量纲的数据才能放在同一个"坐标系"里比较。

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 | 原理说明 |
|-----|------|----------|--------|----------|
| `sklearn.preprocessing.MinMaxScaler` | `MinMaxScaler(feature_range=(0, 1), clip=False)` | `feature_range`：目标缩放区间，默认 `(0,1)`；`clip`：是否将超出范围的值裁剪到边界 | 一个缩放器实例，含 `fit_transform()`、`inverse_transform()` 方法 | 公式：`X_std = (X - X.min) / (X.max - X.min)`，再乘以区间宽度并加下界 |
| `sklearn.preprocessing.StandardScaler` | `StandardScaler(copy=True, with_mean=True, with_std=True)` | `with_mean`：是否中心化（减均值）；`with_std`：是否缩放（除标准差） | 一个缩放器实例，含 `fit_transform()`、`inverse_transform()` 方法 | 公式：`z = (X - μ) / σ`，其中 μ 为均值，σ 为标准差 |
| `sklearn.preprocessing.RobustScaler` | `RobustScaler(quantile_range=(25.0, 75.0))` | `quantile_range`：使用的分位数区间，默认用 IQR（四分位距） | 一个缩放器实例 | 公式：`(X - median) / IQR`，对异常值不敏感 |
| `sklearn.preprocessing.MaxAbsScaler` | `MaxAbsScaler()` | 无 | 一个缩放器实例 | 公式：`X / max(abs(X))`，将数据缩放到 `[-1, 1]`，适合稀疏数据 |
| `sklearn.preprocessing.normalize` | `normalize(X, norm='l2', axis=1)` | `norm`：`'l1'` 或 `'l2'`，指定范数类型；`axis`：按行(1)或按列(0)缩放 | 缩放后的数组（`ndarray`） | 将每个样本（行）缩放为单位范数（向量长度归一化），常用于文本分类 |

> **注意**：所有 Scikit-learn 缩放器都遵循 **fit → transform** 两阶段模式。`fit` 计算训练集的统计量（如均值、标准差、最小值、最大值），`transform` 应用这些统计量到数据上。**测试集必须使用训练集拟合好的参数进行 transform**，防止数据泄露。

## 3. 代码示例

### 示例 1：MinMaxScaler 基础用法（归一化到 [0,1]）

```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# 创建示例数据：两列特征，量纲差异巨大
data = pd.DataFrame({
    '年龄': [25, 30, 35, 40, 45],
    '收入': [30000, 50000, 80000, 120000, 200000]
})
print("原始数据：\n", data)

# 初始化缩放器并拟合转换
scaler = MinMaxScaler()  # 默认缩放到 [0, 1]
scaled_data = scaler.fit_transform(data)

# 转换为 DataFrame 方便查看
scaled_df = pd.DataFrame(scaled_data, columns=data.columns)
print("\n归一化后数据：\n", scaled_df)

# 查看每列的最小值和最大值
print("\n每列最小值：", scaled_df.min().values)
print("每列最大值：", scaled_df.max().values)

# 逆变换还原数据
original = scaler.inverse_transform(scaled_data)
print("\n逆变换还原：\n", original)

# 输出结果：
# 原始数据：
#     年龄      收入
# 0   25    30000
# 1   30    50000
# 2   35    80000
# 3   40   120000
# 4   45   200000
# 归一化后数据：
#      年龄  收入
# 0  0.00  0.00
# 1  0.25  0.12
# 2  0.50  0.29
# 3  0.75  0.53
# 4  1.00  1.00
```

### 示例 2：StandardScaler 标准化（转换为标准正态分布）

```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

# 生成带有异常值的数据
np.random.seed(42)
data = np.random.normal(loc=50, scale=10, size=(100, 2))
data[0, 0] = 200  # 人为添加一个异常值

# 标准化
scaler = StandardScaler()
scaled = scaler.fit_transform(data)

print("标准化后均值：", np.round(scaled.mean(axis=0), 6))  # 接近 0
print("标准化后标准差：", np.round(scaled.std(axis=0), 6))  # 接近 1

# 对比：MinMaxScaler 受异常值影响严重
from sklearn.preprocessing import MinMaxScaler
minmax = MinMaxScaler()
scaled_mm = minmax.fit_transform(data)
print("\nMinMaxScaler 缩放后最大值：", scaled_mm.max(axis=0))
print("MinMaxScaler 缩放后最小值：", scaled_mm.min(axis=0))

# 输出结果：
# 标准化后均值： [ 0. -0.]
# 标准化后标准差： [1. 1.]
# MinMaxScaler 缩放后最大值： [1. 1.]
# MinMaxScaler 缩放后最小值： [0. 0.]
# （注意：MinMaxScaler 中大部分数据被压缩到很小范围，因为异常值 200 拉大了范围）
```

### 示例 3：Pipeline 中集成标准化 + 交叉验证

```python
import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline

# 加载乳腺癌数据集（特征量纲差异大）
cancer = load_breast_cancer()
X, y = cancer.data, cancer.target

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

# 构建 Pipeline：先标准化，再训练 SVM
pipe = Pipeline([
    ('scaler', StandardScaler()),  # 标准化
    ('svm', SVC(kernel='rbf', C=1.0))  # RBF 核 SVM 对特征尺度敏感
])

# 交叉验证评估
scores = cross_val_score(pipe, X_train, y_train, cv=5)
print(f"交叉验证准确率：{scores.mean():.4f} ± {scores.std():.4f}")

# 在测试集上评估
pipe.fit(X_train, y_train)
test_acc = pipe.score(X_test, y_test)
print(f"测试集准确率：{test_acc:.4f}")

# 对比：不做标准化的效果
svm_raw = SVC(kernel='rbf', C=1.0)
svm_raw.fit(X_train, y_train)
raw_acc = svm_raw.score(X_test, y_test)
print(f"未标准化测试集准确率：{raw_acc:.4f}")

# 输出结果（示例）：
# 交叉验证准确率：0.9724 ± 0.0144
# 测试集准确率：0.9766
# 未标准化测试集准确率：0.9181
# （可见标准化显著提升了 SVM 的性能）
```

## 4. 常见错误

### 错误 1：对全数据集进行 fit_transform 导致数据泄露

```python
# 错误写法：先 fit_transform 再划分训练测试集
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)  # 用全部数据拟合
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.3)
```

**错误原因**：测试集的信息（均值、标准差）在训练阶段就被"偷看"了，导致评估结果过于乐观，模型泛化能力被高估。

**正确写法**：

```python
# 正确：先划分，再在训练集上 fit，在测试集上只 transform
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)  # 只在训练集上 fit
X_test_scaled = scaler.transform(X_test)        # 测试集只 transform
```

### 错误 2：混淆归一化和标准化的适用场景

```python
# 错误：对含有大量异常值的数据使用 MinMaxScaler
import numpy as np
from sklearn.preprocessing import MinMaxScaler

data = np.array([[1], [2], [3], [4], [100]])  # 100 是异常值
scaler = MinMaxScaler()
scaled = scaler.fit_transform(data)
print(scaled)  # 大部分数据被压缩到 0~0.03 之间，区分度极低
```

**错误原因**：MinMaxScaler 依赖最大值和最小值，异常值会严重压缩正常数据的分布范围。

**正确写法**：

```python
# 正确：有异常值时使用 RobustScaler 或 StandardScaler
from sklearn.preprocessing import RobustScaler, StandardScaler

robust_scaler = RobustScaler()
scaled_robust = robust_scaler.fit_transform(data)
print(scaled_robust)  # 使用中位数和 IQR，不受异常值影响

std_scaler = StandardScaler()
scaled_std = std_scaler.fit_transform(data)
print(scaled_std)
```

### 错误 3：对稀疏矩阵使用 StandardScaler（默认会破坏稀疏性）

```python
# 错误：直接对稀疏矩阵做标准化
from scipy.sparse import csr_matrix
from sklearn.preprocessing import StandardScaler

sparse_data = csr_matrix([[0, 1, 0], [1, 0, 0], [0, 0, 1]])
scaler = StandardScaler(with_mean=True)  # 默认 with_mean=True
# scaler.fit(sparse_data)  # 报错：ValueError: 稀疏矩阵不支持 with_mean=True
```

**错误原因**：`with_mean=True` 需要对稀疏矩阵进行中心化（减均值），这会破坏稀疏结构并导致内存爆炸。

**正确写法**：

```python
# 正确：稀疏矩阵使用 MaxAbsScaler 或 StandardScaler(with_mean=False)
from sklearn.preprocessing import MaxAbsScaler, StandardScaler

# 方案一：MaxAbsScaler 专为稀疏数据设计
scaler1 = MaxAbsScaler()
scaled1 = scaler1.fit_transform(sparse_data)

# 方案二：StandardScaler 关闭中心化
scaler2 = StandardScaler(with_mean=False)
scaled2 = scaler2.fit_transform(sparse_data)
```

## 5. 练习

### 练习 1：选择正确的缩放方法

给定以下场景，请选择最合适的缩放方法并说明理由：

- **场景 A**：图像像素值（0-255 整数），用于神经网络输入。
- **场景 B**：包含大量极端异常值的传感器数据，用于 KNN 分类。
- **场景 C**：文本 TF-IDF 特征矩阵（稀疏），用于逻辑回归。

**答案提示**：
- 场景 A：使用 `MinMaxScaler` 缩放到 `[0, 1]`，与神经网络激活函数的输入范围匹配。
- 场景 B：使用 `RobustScaler`，基于中位数和 IQR，不受异常值影响。
- 场景 C：使用 `MaxAbsScaler` 或 `normalize`，保持稀疏性，避免破坏稀疏结构。

### 练习 2：动手实现归一化

编写代码完成以下任务：

1. 生成 100 个服从正态分布 `N(50, 15)` 的随机数作为特征 A，以及 100 个服从均匀分布 `U(0, 1)` 的随机数作为特征 B。
2. 分别用 `MinMaxScaler` 和 `StandardScaler` 对这两个特征进行缩放。
3. 绘制原始数据和两种缩放后数据的散点图（使用 Matplotlib），观察分布变化。
4. 回答：哪种缩放方法使两个特征在图中"看起来"更接近？为什么？

**答案提示**：

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler, StandardScaler

np.random.seed(42)
feature_a = np.random.normal(50, 15, 100)
feature_b = np.random.uniform(0, 1, 100)
X = np.column_stack([feature_a, feature_b])

# 分别缩放
minmax_scaler = MinMaxScaler()
std_scaler = StandardScaler()
X_minmax = minmax_scaler.fit_transform(X)
X_std = std_scaler.fit_transform(X)

# 绘制三组散点图
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
axes[0].scatter(X[:, 0], X[:, 1], alpha=0.6)
axes[0].set_title('原始数据')
axes[1].scatter(X_minmax[:, 0], X_minmax[:, 1], alpha=0.6)
axes[1].set_title('MinMaxScaler')
axes[2].scatter(X_std[:, 0], X_std[:, 1], alpha=0.6)
axes[2].set_title('StandardScaler')
plt.show()

# 观察：MinMaxScaler 将两个特征都缩放到 [0,1]，但分布形状不变；
# StandardScaler 使两个特征都变为均值 0、标准差 1，但原始分布形状（正态 vs 均匀）仍然保留。
# 从"视觉接近度"看，StandardScaler 让两个特征在尺度上更可比。
```

---

**总结**：数据标准化与归一化是数据清洗中不可或缺的一步。选择哪种方法取决于数据分布、是否存在异常值、模型类型以及数据是否稀疏。记住核心原则：**训练集 fit，测试集只 transform**，这是防止数据泄露的底线。