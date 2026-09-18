# Python环境搭建与Jupyter入门
> 模块：Python基础速成 | 编号：第0讲 | Python数据分析实战

## 1. 概念

### 1.1 Python 解释器与运行方式

- **Python 解释器**：执行 `.py` 源文件的程序，把源码逐行翻译为机器指令。Python 是**解释型语言**，不像 C/Java 需要先编译成可执行文件，改完直接跑。
- **REPL 交互模式**：命令行输入 `python` 进入的「读取-求值-输出-循环」（Read-Eval-Print Loop），逐条输入、即时出结果，适合快速验证语法。
- **脚本执行模式**：`python script.py` 一次性运行整个文件，适合正式的数据分析任务。
- **Python 3 与 Python 2**：Python 2 已于 2020 年停止维护，数据分析全部使用 **Python 3**（3.8+ 均可）。

### 1.2 环境变量 PATH

- **PATH 是什么**：操作系统维护的一个目录列表，当你在命令行输入 `python` 时，系统按顺序在这些目录里查找 `python.exe`，找到就执行。
- **为什么需要配置**：不配置 PATH，就必须每次输入 Python 的完整路径（如 `C:\Python311\python.exe`）。安装时勾选「Add Python to PATH」就是自动完成这一步。
- **查找顺序**：PATH 中排在前面的目录优先；若多个目录都有同名命令，前面的生效。

### 1.3 虚拟环境与依赖管理

- **虚拟环境（venv）**：为每个项目创建一套**相互隔离**的 Python 运行环境，各自拥有独立的解释器副本和包目录，解决「A 项目要 pandas 1.x、B 项目要 pandas 2.x」的冲突。
- **隔离原理**：每个 venv 有一个独立的 `site-packages` 目录（第三方库安装位置）。激活后，`python`/`pip` 命令指向该环境自己的目录，与全局环境互不影响。
- **conda 与 pip 的区别**：`pip` 只装 Python 包；`conda` 除 Python 包外还能装**非 Python 依赖**（如底层 C 库），且自带环境管理。新手用 Anaconda（conda），进阶用 venv + pip 更轻量。
- **pip 镜像源**：默认从国外 PyPI 下载慢，国内可配置清华/阿里镜像加速（如 `https://pypi.tuna.tsinghua.edu.cn/simple`）。
- **requirements.txt 依赖锁定**：用 `pip freeze > requirements.txt` 把当前环境的所有包及版本导出，换机器后 `pip install -r requirements.txt` 一键还原，保证环境一致。

### 1.4 Jupyter 与开发工具

- **Jupyter Notebook / JupyterLab**：基于浏览器的交互式编程环境，代码分块（Cell）运行、结果即时显示，特别适合数据分析的"边写边跑边看"。
- **Cell 类型**：`Code`（代码，可运行）、`Markdown`（文字说明，写思路）、`Raw`（原样文本）。数据分析报告 = Markdown 写结论 + Code 写操作。
- **两种模式**：**命令模式**（边框蓝色，按 `Esc` 进入，管理 Cell）与**编辑模式**（边框绿色，按 `Enter` 进入，写代码）。
- **Magic Commands 魔法命令**：以 `%` 开头的 Jupyter 内置命令，如 `%matplotlib inline`（图表内嵌显示）、`%time`（计时）、`%pwd`（查看路径）、`%run 文件`（运行脚本）。
- **Anaconda**：集成 Python + 250+ 科学计算库 + 包管理器的发行版，自带 conda，新手免去逐个装库的麻烦（另有更精简的 Miniconda）。
- **IDE 选择**：Jupyter 适合探索性分析；**VS Code / PyCharm** 适合写完整项目（代码补全、调试、版本管理更强），二者按场景配合使用。

**生活化类比**：解释器是"翻译机"；REPL 是"当面对话"，脚本执行是"发一封完整邮件"；PATH 是"通讯录"，系统按它找人；虚拟环境是每间项目独立的"厨房"（锅碗瓢盆互不串味）；pip 是"外卖员"，conda 是"带厨房装修的全包公司"；requirements.txt 是"采购清单"；Jupyter 是"能边写边算的草稿本"，Markdown 单元格是"旁批"，魔法命令是"快捷键"。

## 2. 核心命令与原理

| 命令 | 用法 | 作用 |
|------|------|------|
| `python` | `python script.py` | 运行脚本 / 进入 REPL |
| `python -m venv` | `python -m venv 环境名` | 创建虚拟环境 |
| `pip install` | `pip install 库名` | 安装第三方库 |
| `pip install -r` | `pip install -r requirements.txt` | 按清单批量还原依赖 |
| `pip freeze` | `pip freeze > requirements.txt` | 导出当前依赖清单 |
| `pip list` | `pip list` | 列出已安装的包 |
| `jupyter` | `jupyter notebook` | 启动 Jupyter Notebook |

**原理说明**：`python` 命令能被系统找到，靠的是环境变量 PATH——系统按其中的目录顺序查找 `python.exe`。`pip` 本质上是在指定环境里下载包并解压到 `site-packages` 目录；虚拟环境就是一套独立的 Python 解释器 + `site-packages`，激活后 `python`/`pip` 命令就指向这个独立环境。

## 3. 代码示例

### 示例1：验证 Python 安装（入门）

```bash
# 查看 Python 版本（能打印版本号说明安装成功）
python --version
# 输出示例: Python 3.11.9

# 进入交互式解释器，逐条执行
python
>>> print("Hello, 数据分析")
Hello, 数据分析
>>> 1 + 1
2
>>> exit()   # 退出解释器
```

### 示例2：创建虚拟环境并安装库（进阶）

```bash
# 1. 创建名为 myenv 的虚拟环境
python -m venv myenv

# 2. 激活虚拟环境（Windows）
myenv\Scripts\activate
# macOS / Linux 用: source myenv/bin/activate
# 激活后命令行前缀出现 (myenv)

# 3. 安装数据分析核心库
pip install numpy pandas matplotlib

# 4. 验证安装
python -c "import numpy, pandas; print('numpy', numpy.__version__, '| pandas', pandas.__version__)"
# 输出示例: numpy 1.26.4 | pandas 2.2.2

# 5. 退出虚拟环境
deactivate
```

### 示例3：启动 Jupyter 并跑第一段代码（数据分析场景）

```bash
# 安装并启动 Jupyter
pip install jupyterlab
jupyter notebook    # 浏览器会自动打开 http://localhost:8888
```

在 Jupyter 的代码单元格（Cell）里输入并运行（`Shift + Enter`）：

```python
# 在 Jupyter 单元格中运行，结果直接显示在下方
import pandas as pd

data = {"姓名": ["张三", "李四", "王五"],
        "成绩": [85, 92, 78]}
df = pd.DataFrame(data)

df["成绩"].mean()   # 直接返回平均分: 85.0
```

## 4. 常见错误

### 错误1：提示「python 不是内部或外部命令」
```bash
C:\> python --version
'python' 不是内部或外部命令，也不是可运行的程序或批处理文件。
```
**原因**：安装 Python 时**没有勾选「Add Python to PATH」**，系统在 PATH 里找不到 `python.exe`。
**解决**：重新运行安装包 → 勾选「Add Python to PATH」→ 重装；或手动把 Python 安装目录加入系统环境变量 PATH。

### 错误2：pip 安装报「Permission denied」
```bash
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied
```
**原因**：把包装进了系统全局目录，而当前用户没有写入权限。
**解决**：先用 `python -m venv myenv` 创建虚拟环境并激活，再执行 `pip install`，装进属于自己的环境里（推荐做法）。

### 错误3：忘了激活虚拟环境，库装错地方
```bash
python -m venv myenv
pip install pandas          # ← 没激活就装，装进了全局环境而不是 myenv
```
**原因**：`pip` 总是把包装进「当前激活的」环境；没激活就装进了全局环境，导致不同项目互相污染。
**解决**：先 `myenv\Scripts\activate`（Windows）再 `pip install`。

### 错误4：pip install 极慢或超时
**原因**：用了国外默认源。
**解决**：配置国内镜像源（清华 `https://pypi.tuna.tsinghua.edu.cn/simple` 或阿里）。

### 错误5：不同项目 pandas 版本冲突
**原因**：都装在全局环境，没有隔离。
**解决**：每个项目用独立 venv + `requirements.txt` 锁定版本。

## 5. 练习

### 练习1：搭建自己的环境
请在本机完成以下步骤，并记录每一步的返回结果：
1. 确认 `python --version` 能正常打印版本号
2. 创建名为 `analysis_env` 的虚拟环境并激活
3. 在环境里安装 `numpy`、`pandas`、`jupyterlab`
4. 用 `pip list` 确认三个包已安装
5. 启动 `jupyter notebook`，新建一个 notebook

### 练习2：第一个 Jupyter 数据任务
在 Jupyter 中创建一个单元格，完成：
- 用 pandas 创建一个包含 3 行 2 列（姓名、成绩）的 DataFrame
- 计算成绩的平均值并打印

**答案提示**：
```python
import pandas as pd
df = pd.DataFrame({"姓名": ["A", "B", "C"], "成绩": [70, 80, 90]})
print(df["成绩"].mean())   # 输出: 80.0
```
