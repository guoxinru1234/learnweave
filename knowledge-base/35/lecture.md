# Apache Airflow调度实战

> 模块：ETL数据管道 | 编号：第35讲 | Python数据分析实战

---

## 1. 概念

Apache Airflow 是一个开源的工作流调度与编排平台，用于以编程方式编写、调度和监控数据管道（即 DAG，有向无环图）。它将复杂的 ETL 流程拆解为多个有依赖关系的任务（Task），由调度器（Scheduler）按时间触发，由执行器（Executor）并行运行，并提供 Web UI 进行监控与日志查看。

**适用场景**：每日定时同步数据库、周期性训练机器学习模型、跨系统数据聚合、失败自动重试与告警等。

**生活化类比**：想象你是一家餐厅的主厨。你有一张"今日菜单"（DAG），上面写着：先洗菜（Task A），再切菜（Task B），然后炒菜（Task C），最后上菜（Task D）。每道工序有明确的先后顺序（依赖关系），你设定好"下午5点开始"（调度时间），后厨团队（执行器）就会按流程自动开工。如果切菜时发现刀坏了（任务失败），系统会提醒你重试或跳过，而你不会忘记任何一道菜。

---

## 2. 核心API与原理

Airflow 的核心是 `DAG` 类和 `BaseOperator`（及其子类）。以下是最常用的 4 个 API：

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `DAG` | `DAG(dag_id, description, schedule, start_date, catchup, default_args)` | `dag_id`: 唯一标识；`schedule`: 调度表达式（cron 或 `@daily`）；`start_date`: 起始时间；`catchup`: 是否补跑错过的任务；`default_args`: 默认参数（如重试次数） | `DAG` 对象 |
| `PythonOperator` | `PythonOperator(task_id, python_callable, op_kwargs, dag)` | `task_id`: 任务唯一标识；`python_callable`: 要执行的 Python 函数；`op_kwargs`: 传给函数的参数字典 | `BaseOperator` 对象 |
| `BashOperator` | `BashOperator(task_id, bash_command, dag)` | `bash_command`: 要执行的 Shell 命令字符串 | `BaseOperator` 对象 |
| `DAG.branch` 或 `BranchPythonOperator` | `BranchPythonOperator(task_id, python_callable, dag)` | 根据函数返回值（下游任务 ID）决定分支走向 | `BaseOperator` 对象 |

**核心原理**：Airflow 通过解析 Python 文件（默认在 `dags/` 目录）构建 DAG 对象，调度器周期性扫描 DAG 的 `schedule` 参数，生成 `DagRun` 实例。每个 `DagRun` 根据任务依赖关系生成 `TaskInstance`，由执行器分发到 Worker 执行。任务状态（成功/失败/重试）持久化在元数据库（默认 SQLite，生产环境常用 PostgreSQL）中。

---

## 3. 代码示例

### 示例 1：最简单的定时任务（入门）

```python
# dags/simple_dag.py
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

def print_hello():
    """简单的打印函数"""
    print("Hello from Airflow! 数据管道开始运行。")
    return "done"

# 定义 DAG：每天凌晨 2 点执行
default_args = {
    'owner': 'data_team',
    'retries': 1,          # 失败重试 1 次
    'retry_delay': 300,    # 重试间隔 300 秒
}

with DAG(
    dag_id='simple_hello_dag',
    default_args=default_args,
    description='一个最简单的定时任务',
    schedule='0 2 * * *',      # cron 表达式：每天 02:00
    start_date=datetime(2024, 1, 1),
    catchup=False,             # 不补跑历史任务
) as dag:
    
    task_hello = PythonOperator(
        task_id='print_hello_task',
        python_callable=print_hello,
    )

# 输出结果（在 Airflow 日志中可见）：
# [2024-xx-xx 02:00:00] Hello from Airflow! 数据管道开始运行。
```

### 示例 2：带依赖关系的 ETL 流程（进阶）

```python
# dags/etl_pipeline.py
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
import pandas as pd
import json

def extract_data(**context):
    """模拟从 API 提取数据"""
    data = {'user': ['Alice', 'Bob', 'Charlie'], 
            'amount': [100, 250, 180]}
    df = pd.DataFrame(data)
    # 将数据通过 XCom 传递给下游任务
    context['ti'].xcom_push(key='raw_data', value=df.to_json())
    print(f"提取完成，共 {len(df)} 条记录")
    return "extract_success"

def transform_data(**context):
    """数据清洗与转换：金额大于 150 的标记为 VIP"""
    ti = context['ti']
    df_json = ti.xcom_pull(key='raw_data', task_ids='extract_task')
    df = pd.read_json(df_json)
    df['is_vip'] = df['amount'] > 150
    ti.xcom_push(key='transformed_data', value=df.to_json())
    print(f"转换完成，VIP 用户数: {df['is_vip'].sum()}")
    return "transform_success"

def load_data(**context):
    """模拟加载到数据仓库"""
    ti = context['ti']
    df_json = ti.xcom_pull(key='transformed_data', task_ids='transform_task')
    df = pd.read_json(df_json)
    # 实际项目中这里会写入数据库，此处仅打印
    print(df.to_string())
    print("加载完成！数据已写入数据仓库。")
    return "load_success"

with DAG(
    dag_id='etl_pipeline_dag',
    schedule='@daily',           # 每天执行一次
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    
    extract_task = PythonOperator(
        task_id='extract_task',
        python_callable=extract_data,
    )
    
    transform_task = PythonOperator(
        task_id='transform_task',
        python_callable=transform_data,
    )
    
    load_task = PythonOperator(
        task_id='load_task',
        python_callable=load_data,
    )
    
    # 设置依赖关系：extract -> transform -> load
    extract_task >> transform_task >> load_task

# 输出结果（日志摘要）：
# [task:extract_task] 提取完成，共 3 条记录
# [task:transform_task] 转换完成，VIP 用户数: 2
# [task:load_task]    user  amount  is_vip
# 0     Alice     100    False
# 1       Bob     250     True
# 2   Charlie     180     True
# 加载完成！数据已写入数据仓库。
```

### 示例 3：条件分支与动态任务（高阶）

```python
# dags/branch_dag.py
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.dummy import DummyOperator
import random

def decide_branch():
    """随机决定走哪个分支"""
    value = random.randint(1, 10)
    if value > 5:
        return 'process_high_task'   # 返回下游任务 ID
    else:
        return 'process_low_task'

def process_high():
    print("处理高优先级数据...")

def process_low():
    print("处理低优先级数据...")

def generate_tasks():
    """动态生成多个任务"""
    return [f"dynamic_task_{i}" for i in range(3)]

with DAG(
    dag_id='branch_and_dynamic_dag',
    schedule='*/30 * * * *',       # 每 30 分钟
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    
    start = DummyOperator(task_id='start')
    
    branch = BranchPythonOperator(
        task_id='branch_task',
        python_callable=decide_branch,
    )
    
    process_high_task = PythonOperator(
        task_id='process_high_task',
        python_callable=process_high,
    )
    
    process_low_task = PythonOperator(
        task_id='process_low_task',
        python_callable=process_low,
    )
    
    end = DummyOperator(task_id='end')
    
    # 动态创建 3 个并行任务
    dynamic_tasks = []
    for i in range(3):
        task = PythonOperator(
            task_id=f'dynamic_task_{i}',
            python_callable=lambda i=i: print(f"动态任务 {i} 执行中"),
        )
        dynamic_tasks.append(task)
    
    # 设置依赖
    start >> branch
    branch >> [process_high_task, process_low_task]
    process_high_task >> end
    process_low_task >> end
    start >> dynamic_tasks >> end

# 输出结果（随机分支示例）：
# [task:branch_task] 随机数=7，走 process_high_task 分支
# [task:process_high_task] 处理高优先级数据...
# [task:dynamic_task_0] 动态任务 0 执行中
# [task:dynamic_task_1] 动态任务 1 执行中
# [task:dynamic_task_2] 动态任务 2 执行中
```

---

## 4. 常见错误

### 错误 1：忘记设置 `catchup=False`，导致大量历史任务补跑

**错误原因**：当 `start_date` 设置为过去时间且未指定 `catchup` 时，Airflow 默认会为从 `start_date` 到当前时间之间的每个调度周期创建任务实例，导致瞬间生成大量任务，拖垮系统。

**正确写法**：
```python
with DAG(
    dag_id='my_dag',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,          # 关键：禁止补跑
) as dag:
    pass
```

### 错误 2：任务间传递数据时直接使用全局变量

**错误原因**：Airflow 任务可能在多个 Worker 进程上执行，全局变量无法跨进程共享，导致下游任务获取不到上游数据。

**正确写法**：使用 XCom 传递数据：
```python
def upstream_task(**context):
    context['ti'].xcom_push(key='my_data', value=42)

def downstream_task(**context):
    value = context['ti'].xcom_pull(key='my_data', task_ids='upstream_task')
    print(f"接收到的数据: {value}")
```

### 错误 3：调度表达式写错，任务不触发

**错误原因**：Airflow 2.x 使用 `schedule` 参数（旧版为 `schedule_interval`），且 cron 表达式有 5 个字段（分 时 日 月 周）。新手常写成 6 个字段或漏掉分钟位。

**正确写法**：
```python
# 错误：schedule='0 0 2 * * *'  （6个字段，多了一个秒位）
# 正确：每天凌晨2点
schedule='0 2 * * *'

# 错误：schedule='daily'  （不是合法表达式）
# 正确：使用预设常量
schedule='@daily'   # 或 '0 0 * * *'
```

---

## 5. 练习

### 练习 1：设计一个"数据质量监控" DAG

**题目**：设计一个每小时执行的 DAG，包含以下任务：
1. 从 CSV 文件读取销售数据（模拟）
2. 检查数据中是否有空值或负数金额（数据质量检查）
3. 如果质量检查通过，则汇总数据并打印；如果失败，则发送告警（用打印模拟）

**答案提示**：
- 使用 `BranchPythonOperator` 实现条件分支
- 质量检查函数返回 `'process_ok_task'` 或 `'alert_task'`
- 使用 `pd.read_csv()` 读取数据，用 `df.isnull().sum()` 和 `df['amount'] < 0` 检查质量

### 练习 2：XCom 数据传递实战

**题目**：编写一个 DAG，包含 3 个任务：`task_1` 生成一个包含 10 个随机整数的列表，`task_2` 计算这些数的平均值，`task_3` 判断平均值是否大于 50 并打印结果。

**答案提示**：
- `task_1` 使用 `random.sample(range(100), 10)` 生成列表，通过 `xcom_push` 传递
- `task_2` 使用 `xcom_pull` 获取列表，用 `statistics.mean()` 计算均值，再次 `xcom_push`
- `task_3` 拉取均值，用 `if` 判断并打印
- 注意：XCom 传递复杂对象时建议转为 JSON 字符串（如 `json.dumps()`）