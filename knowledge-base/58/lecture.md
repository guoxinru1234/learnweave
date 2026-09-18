# 多进程并行处理

> 模块：性能优化与部署 | 编号：第58讲 | Python数据分析实战

---

## 1. 概念

多进程并行处理是指在同一台机器的多个 CPU 核心上同时运行多个进程，每个进程拥有独立的 Python 解释器和内存空间，从而实现真正的并行计算。与多线程不同，多进程可以绕过 Python 的全局解释器锁（GIL）限制，让 CPU 密集型任务（如大规模矩阵运算、复杂数值模拟）真正同时执行。

**生活化类比**：想象你是一家餐厅的老板。单进程模式就像你一个人既点单又炒菜又结账，忙得不可开交；多线程就像你雇了多个服务员（线程）但只有一个厨房（GIL），大家抢同一个灶台；而多进程就像你开了多个厨房（进程），每个厨房有自己的厨师和灶台，可以同时烹饪多道菜。

**适用场景**：CPU 密集型任务（数值计算、图像处理、数据转换）、独立子任务的批量处理。**不适用**于 I/O 密集型任务（文件读写、网络请求），此时多线程或异步编程更合适。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 | 核心原理 |
|-----|------|----------|--------|----------|
| `multiprocessing.Pool` | `Pool(processes=None, initializer=None, initargs=())` | `processes`: 进程数，默认取 CPU 核心数；`initializer`: 每个进程启动时执行的初始化函数 | `Pool` 对象 | 创建一组工作进程，将任务分发到进程池中并行执行 |
| `Pool.map` | `map(func, iterable, chunksize=1)` | `func`: 要执行的函数；`iterable`: 可迭代对象；`chunksize`: 每个进程一次获取的任务数 | 列表，元素为 `func` 的返回值 | 将可迭代对象切分并分发给各进程，阻塞直到全部完成 |
| `Pool.apply_async` | `apply_async(func, args=(), kwds={}, callback=None)` | `func`: 目标函数；`args`: 位置参数元组；`kwds`: 关键字参数字典；`callback`: 完成回调函数 | `AsyncResult` 对象 | 异步提交单个任务，不阻塞主进程 |
| `multiprocessing.Process` | `Process(group=None, target=None, name=None, args=(), kwargs={})` | `target`: 进程执行的函数；`args`: 位置参数；`kwargs`: 关键字参数 | `Process` 对象 | 直接创建独立进程，需手动管理启动和结束 |
| `Pool.starmap` | `starmap(func, iterable, chunksize=1)` | `func`: 目标函数；`iterable`: 元素为参数元组的可迭代对象 | 列表 | `map` 的扩展，支持多参数函数 |

**关键原理**：`Pool` 底层使用进程间通信（IPC）机制（如管道或队列）进行任务分发和结果回收。每个工作进程独立执行任务，完成后将结果序列化回主进程。`chunksize` 参数影响任务分配粒度，过小增加通信开销，过大可能导致负载不均。

---

## 3. 代码示例

### 示例1：基础用法 —— 并行计算平方和

```python
import multiprocessing as mp
import time

def square(x):
    """计算平方并模拟耗时操作"""
    time.sleep(0.1)  # 模拟耗时计算
    return x * x

if __name__ == '__main__':
    data = list(range(10))
    
    # 串行计算（对照组）
    start = time.time()
    serial_result = [square(x) for x in data]
    serial_time = time.time() - start
    print(f"串行结果: {serial_result}")
    print(f"串行耗时: {serial_time:.2f}秒")
    
    # 多进程并行计算（使用4个进程）
    start = time.time()
    with mp.Pool(processes=4) as pool:
        parallel_result = pool.map(square, data)
    parallel_time = time.time() - start
    print(f"并行结果: {parallel_result}")
    print(f"并行耗时: {parallel_time:.2f}秒")
    print(f"加速比: {serial_time / parallel_time:.2f}x")

# 输出示例:
# 串行结果: [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
# 串行耗时: 1.01秒
# 并行结果: [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
# 并行耗时: 0.31秒
# 加速比: 3.26x
```

### 示例2：进阶用法 —— 多参数函数与异步提交

```python
import multiprocessing as mp
import time

def calculate_metrics(data, weight, bias):
    """计算加权指标"""
    time.sleep(0.05)
    return data * weight + bias

if __name__ == '__main__':
    data_list = [1, 2, 3, 4, 5, 6, 7, 8]
    
    # 使用 starmap 处理多参数函数
    with mp.Pool(processes=4) as pool:
        # 每个任务传入 (data, weight, bias) 参数元组
        tasks = [(d, 2.0, 1.0) for d in data_list]
        results = pool.starmap(calculate_metrics, tasks)
    print(f"starmap 结果: {results}")
    
    # 使用 apply_async 异步提交任务
    with mp.Pool(processes=4) as pool:
        async_results = [pool.apply_async(calculate_metrics, args=(d, 3.0, 0.5)) 
                        for d in data_list]
        # 主进程可在此做其他事情
        time.sleep(0.2)
        # 等待所有任务完成并获取结果
        async_results_data = [r.get() for r in async_results]
    print(f"apply_async 结果: {async_results_data}")

# 输出示例:
# starmap 结果: [3.0, 5.0, 7.0, 9.0, 11.0, 13.0, 15.0, 17.0]
# apply_async 结果: [3.5, 6.5, 9.5, 12.5, 15.5, 18.5, 21.5, 24.5]
```

### 示例3：实战 —— 并行处理大型数据集

```python
import multiprocessing as mp
import numpy as np
import pandas as pd

def process_chunk(chunk_data):
    """处理数据块：计算每列均值并标准化"""
    # 模拟复杂计算
    result = {}
    for col in chunk_data.columns:
        mean_val = chunk_data[col].mean()
        std_val = chunk_data[col].std()
        result[col] = {'mean': mean_val, 'std': std_val}
    return result

def parallel_dataframe_processing(df, n_processes=4):
    """并行处理 DataFrame：按行切分后分发给多个进程"""
    # 将 DataFrame 按行切分为 n_processes 个块
    chunk_size = len(df) // n_processes
    chunks = [df.iloc[i*chunk_size:(i+1)*chunk_size] 
              for i in range(n_processes)]
    # 处理剩余行
    if len(df) % n_processes != 0:
        chunks.append(df.iloc[n_processes*chunk_size:])
    
    with mp.Pool(processes=n_processes) as pool:
        results = pool.map(process_chunk, chunks)
    
    # 合并各进程的结果
    merged = {}
    for col in df.columns:
        means = [r[col]['mean'] for r in results]
        stds = [r[col]['std'] for r in results]
        merged[col] = {'mean': np.mean(means), 'std': np.mean(stds)}
    return merged

if __name__ == '__main__':
    # 创建大型模拟数据集
    np.random.seed(42)
    df = pd.DataFrame({
        'A': np.random.randn(100000),
        'B': np.random.randn(100000) * 2 + 1,
        'C': np.random.randn(100000) * 0.5 - 3
    })
    
    print("数据集大小:", df.shape)
    print("并行处理统计结果:")
    result = parallel_dataframe_processing(df, n_processes=4)
    for col, stats in result.items():
        print(f"  列 {col}: 均值={stats['mean']:.4f}, 标准差={stats['std']:.4f}")

# 输出示例:
# 数据集大小: (100000, 3)
# 并行处理统计结果:
#   列 A: 均值=0.0002, 标准差=1.0001
#   列 B: 均值=1.0005, 标准差=2.0003
#   列 C: 均值=-3.0001, 标准差=0.5002
```

---

## 4. 常见错误

### 错误1：在交互式环境或 Jupyter Notebook 中直接使用 `Pool`

```python
# 错误写法（在 Jupyter Notebook 中会报错）
import multiprocessing as mp
pool = mp.Pool(4)
result = pool.map(square, range(10))  # 报错: AttributeError

# 正确写法：将代码放入 .py 文件中，并用 if __name__ == '__main__' 保护
import multiprocessing as mp

def square(x):
    return x * x

if __name__ == '__main__':
    with mp.Pool(4) as pool:
        result = pool.map(square, range(10))
```

**错误原因**：在 Windows 或 Jupyter 环境中，`Pool` 需要可导入的主模块。未使用 `if __name__ == '__main__'` 保护会导致递归创建进程。

### 错误2：在进程间共享可变对象（如普通列表）

```python
# 错误写法：直接修改全局列表
shared_list = []
def add_item(x):
    shared_list.append(x)  # 每个进程有独立的副本，修改不会同步

# 正确写法：使用 Manager 或返回结果
from multiprocessing import Manager

def process_data(x):
    return x * 2

if __name__ == '__main__':
    with mp.Pool(4) as pool:
        results = pool.map(process_data, range(10))
    # 结果通过返回值收集，而非共享全局变量
    print(results)  # [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
```

**错误原因**：每个进程有独立的内存空间，修改全局变量不会影响其他进程。应通过返回值或 `Manager` 对象共享数据。

### 错误3：传递不可序列化的对象

```python
# 错误写法：传递 lambda 函数
with mp.Pool(4) as pool:
    result = pool.map(lambda x: x * 2, range(10))  # 报错: PicklingError

# 正确写法：使用模块级函数
def double(x):
    return x * 2

if __name__ == '__main__':
    with mp.Pool(4) as pool:
        result = pool.map(double, range(10))
    print(result)  # [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
```

**错误原因**：进程间通信需要序列化（pickle）对象，lambda 函数无法被 pickle。应使用模块顶层的普通函数。

---

## 5. 练习

### 练习1：并行质数计算

编写一个程序，使用 `multiprocessing.Pool` 计算 1 到 100000 之间所有质数的数量。要求：
- 将数字范围切分为多个子区间
- 每个进程计算一个子区间的质数数量
- 汇总所有进程的结果

**答案提示**：
```python
import multiprocessing as mp
import math

def count_primes_in_range(start, end):
    """计算 [start, end) 区间内的质数数量"""
    count = 0
    for num in range(start, end):
        if num < 2:
            continue
        is_prime = True
        for i in range(2, int(math.sqrt(num)) + 1):
            if num % i == 0:
                is_prime = False
                break
        if is_prime:
            count += 1
    return count

if __name__ == '__main__':
    n_processes = 4
    total_range = 100000
    chunk_size = total_range // n_processes
    
    with mp.Pool(n_processes) as pool:
        # 使用 starmap 传入多个参数
        tasks = [(i*chunk_size, (i+1)*chunk_size) for i in range(n_processes)]
        results = pool.starmap(count_primes_in_range, tasks)
    
    total = sum(results)
    print(f"1到100000之间的质数数量: {total}")  # 输出: 9592
```

### 练习2：并行数据标准化

给定一个包含 100 万行、5 列数值的 DataFrame，使用多进程对每列进行 Z-score 标准化（减去均值、除以标准差）。要求：
- 将数据按行切分为多个块
- 每个进程计算块的统计量并标准化
- 合并结果并验证标准化后的数据均值为 0，标准差为 1

**答案提示**：
```python
import multiprocessing as mp
import numpy as np
import pandas as pd

def standardize_chunk(chunk, col_stats):
    """对数据块进行标准化"""
    for col in chunk.columns:
        mean, std = col_stats[col]
        chunk[col] = (chunk[col] - mean) / std
    return chunk

if __name__ == '__main__':
    # 生成模拟数据
    np.random.seed(42)
    df = pd.DataFrame(np.random.randn(1000000, 5), 
                      columns=['A', 'B', 'C', 'D', 'E'])
    
    # 先计算全局统计量
    col_stats = {col: (df[col].mean(), df[col].std()) for col in df.columns}
    
    # 切分数据
    n_processes = 4
    chunk_size = len(df) // n_processes
    chunks = [df.iloc[i*chunk_size:(i+1)*chunk_size] 
              for i in range(n_processes)]
    
    # 并行标准化
    with mp.Pool(n_processes) as pool:
        # 使用 functools.partial 固定 col_stats 参数
        from functools import partial
        worker = partial(standardize_chunk, col_stats=col_stats)
        results = pool.map(worker, chunks)
    
    # 合并结果
    df_standardized = pd.concat(results)
    
    # 验证
    print(f"标准化后均值: {df_standardized.mean().round(6)}")
    print(f"标准化后标准差: {df_standardized.std().round(6)}")
    # 输出: 各列均值接近0，标准差接近1
```