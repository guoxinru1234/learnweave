# Dask分布式计算入门

> 模块：性能优化与部署 | 编号：第59讲 | Python数据分析实战

---

## 1. 概念

Dask 是一个开源的并行计算库，它将 NumPy、Pandas 和 Scikit-learn 等熟悉的接口扩展到更大规模的数据集，支持多核并行和分布式集群计算。其核心思想是**惰性求值（Lazy Evaluation）**：构建一个任务图（Task Graph），描述计算步骤，直到调用 `.compute()` 时才真正执行，从而能够智能地调度计算、优化内存使用。

**适用场景**：单机内存放不下的大数据集（如超过 10GB 的 CSV）、需要利用多核 CPU 加速的复杂计算、以及从单机向集群扩展的过渡阶段。

**生活化类比**：Dask 就像一家餐厅的"总调度员"。你（用户）把菜单（计算任务）交给它，它不会立刻让厨师（CPU）去做，而是先规划好每道菜需要哪些食材、哪个厨师空闲、哪个灶台可用，然后统一安排，最后一次性把一桌菜（结果）端上来。这样既避免了厨师手忙脚乱，也最大化利用了厨房资源。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 | 核心原理 |
|-----|------|----------|--------|----------|
| `dask.dataframe.read_csv` | `dd.read_csv(path, blocksize=None, ...)` | `path`: 文件路径或通配符；`blocksize`: 每个分块字节数（默认按文件切分） | `dask.dataframe.DataFrame` | 将大文件拆分为多个 Pandas DataFrame 分块，构建惰性任务图 |
| `DataFrame.compute` | `df.compute(scheduler=None)` | `scheduler`: 调度器类型（`'threads'`、`'processes'`、`'distributed'`），默认自动选择 | Pandas DataFrame 或标量 | 触发实际计算，执行任务图并汇总结果 |
| `dask.delayed` | `dask.delayed(obj)` | `obj`: 任意 Python 函数或对象 | `Delayed` 对象 | 将普通函数包装为惰性任务，构建自定义任务图 |
| `dask.array.from_array` | `da.from_array(x, chunks='auto')` | `x`: 类数组对象；`chunks`: 分块大小（如 `(1000, 1000)`） | `dask.array.Array` | 将数组按块划分，支持并行数值计算 |
| `dask.distributed.Client` | `Client(n_workers=2, threads_per_worker=2)` | `n_workers`: 进程数；`threads_per_worker`: 每进程线程数 | `Client` 对象 | 创建分布式集群，提供实时仪表盘和高效调度 |

---

## 3. 代码示例

### 示例1：使用 Dask DataFrame 读取并聚合大文件（入门）

```python
import dask.dataframe as dd

# 读取多个 CSV 文件（假设 data 文件夹下有 part1.csv, part2.csv...）
# blocksize 控制每个分块大小，这里设为 5MB
df = dd.read_csv('data/part*.csv', blocksize='5MB')

# 惰性构建计算图：按类别分组求和
result = df.groupby('category')['amount'].sum()

# 触发实际计算，返回 Pandas Series
result_pd = result.compute()
print(result_pd)
# 输出示例（假设数据含 A/B 两类）：
# category
# A    15230.50
# B    9876.25
# Name: amount, dtype: float64
```

### 示例2：使用 `dask.delayed` 并行化自定义函数（进阶）

```python
import dask
from dask.delayed import delayed
import time

def process_file(filename):
    """模拟耗时处理：读取文件并返回行数"""
    time.sleep(1)  # 模拟 I/O 延迟
    with open(filename, 'r') as f:
        return sum(1 for _ in f)

# 创建 4 个延迟任务
filenames = [f'data/file_{i}.txt' for i in range(4)]
delayed_results = [delayed(process_file)(fn) for fn in filenames]

# 将所有结果求和（也是惰性的）
total_lines = delayed(sum)(delayed_results)

# 使用多线程调度器执行（4 个文件并行处理，总耗时约 1 秒而非 4 秒）
start = time.time()
print(f"总行数: {total_lines.compute(scheduler='threads')}")
print(f"耗时: {time.time() - start:.2f} 秒")
# 输出示例：
# 总行数: 1200
# 耗时: 1.05 秒
```

### 示例3：Dask Array 并行数值计算（进阶）

```python
import dask.array as da
import numpy as np

# 创建一个 10000x10000 的随机数组，分块为 2000x2000
x = da.random.random((10000, 10000), chunks=(2000, 2000))

# 惰性定义计算：矩阵乘以其转置，再计算每列均值
y = x @ x.T
col_means = y.mean(axis=0)

# 查看任务图规模（不执行计算）
print(f"任务图包含 {len(col_means.dask)} 个任务")
# 输出示例：任务图包含 125 个任务

# 执行计算并获取前 5 个均值
result = col_means.compute()
print(f"前5个列均值: {result[:5]}")
# 输出示例：前5个列均值: [5000.01 4999.98 5000.02 4999.99 5000.00]

# 对比 NumPy 单机计算（内存占用对比）
# np_x = np.random.random((10000, 10000))  # 需要 800MB 内存
# 而 Dask 分块后每块仅需 32MB
```

---

## 4. 常见错误

### 错误1：忘记调用 `.compute()`

```python
import dask.dataframe as dd

df = dd.read_csv('data.csv')
result = df['value'].mean()
print(result)  # ❌ 输出的是 Dask 表达式，不是数值！
# 输出: dd.Scalar<mean-aggregate-future-..., dtype=float64>
```

**原因**：Dask 采用惰性求值，未调用 `compute()` 前只是构建了任务图。
**正确写法**：
```python
result = df['value'].mean().compute()
print(result)  # ✅ 输出实际均值，如 42.5
```

### 错误2：在 Dask DataFrame 上使用 Pandas 专属方法

```python
df = dd.read_csv('data.csv')
# 假设想按行遍历
for index, row in df.iterrows():  # ❌ AttributeError
    pass
```

**原因**：`iterrows()` 是 Pandas 方法，Dask DataFrame 不支持逐行迭代（数据分散在多个分区中）。
**正确写法**：使用 `map_partitions` 或先 `compute()` 再遍历（仅当数据量小时）：
```python
# 对每个分区应用 Pandas 函数
def process_partition(pdf):
    return pdf[pdf['value'] > 0]  # pdf 是 Pandas DataFrame

filtered = df.map_partitions(process_partition)
result = filtered.compute()
```

### 错误3：忽视 `shuffle` 带来的性能开销

```python
df = dd.read_csv('data/*.csv')
# 频繁的 groupby 或 join 操作会触发数据重排
result = df.groupby('user_id').agg({'amount': 'sum'}).compute()
# 如果 user_id 分布不均匀，可能极慢甚至内存溢出
```

**原因**：`groupby` 需要将相同 key 的数据汇聚到同一分区，涉及跨分区数据洗牌（shuffle），开销远大于简单映射操作。
**正确写法**：预先按分组键设置分区索引，减少 shuffle：
```python
df = dd.read_csv('data/*.csv').set_index('user_id', sorted=True)
# 现在 groupby 操作只需在分区内进行，无需全局 shuffle
result = df.groupby('user_id').agg({'amount': 'sum'}).compute()
```

---

## 5. 练习

### 练习1：大文件并行处理（动手题）

你有 20 个 CSV 文件，每个约 500MB，结构相同（含 `date`, `product_id`, `sales` 三列）。请使用 Dask 完成以下任务：
1. 读取所有文件并计算每天的总销售额；
2. 找出销售额最高的前 3 个产品；
3. 将结果保存为单个 CSV 文件。

**答案提示**：
```python
import dask.dataframe as dd

df = dd.read_csv('sales_*.csv', blocksize='100MB')
daily_sales = df.groupby('date')['sales'].sum().compute()
top_products = df.groupby('product_id')['sales'].sum().nlargest(3).compute()
daily_sales.to_frame().to_csv('daily_sales.csv', single_file=True)
# 注意：nlargest 在 Dask 中可用，但需先 groupby 再调用
```

### 练习2：概念思考题

解释为什么以下代码在 Dask 中效率低下，并提出改进方案：
```python
df = dd.read_csv('large.csv')
for i in range(100):
    df['new_col'] = df['col'] * i  # 循环中反复添加列
result = df.compute()
```

**答案提示**：每次循环都会重建整个任务图，且 `df['new_col'] = ...` 会覆盖之前的列，最终只保留最后一次赋值。正确做法是使用 `assign` 一次性添加所有列，或使用 `map_partitions` 在分区内完成多次运算。改进方案：
```python
df = dd.read_csv('large.csv')
df = df.assign(**{f'new_col_{i}': lambda x, i=i: x['col'] * i for i in range(100)})
result = df.compute()
```

---

**延伸学习**：Dask 官方文档（docs.dask.org）提供了完整的 API 参考和调度器配置指南。当数据量超过单机内存时，可进一步学习 `dask.distributed` 集群部署，结合 `Client` 仪表盘实时监控任务执行状态。