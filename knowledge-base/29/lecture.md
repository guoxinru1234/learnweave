# 多子图与Dashboard布局

> 模块：数据可视化 | 编号：第29讲 | Python数据分析实战

---

## 1. 概念

多子图（Multiple Subplots）是指在同一个图形窗口（Figure）中创建多个独立的坐标系（Axes），每个坐标系可以绘制不同的图表，从而实现信息的并排对比或组合展示。Dashboard（仪表盘）则是在此基础上，将多个图表按照业务逻辑进行排版布局，形成一屏总览的可视化面板。

**适用场景**：数据对比分析（如不同产品的月度销量对比）、多维度指标监控（如电商后台的GMV、订单量、转化率同屏展示）、数据关系探索（如散点图矩阵）等。

**生活化类比**：想象你正在装修一套房子（Figure）。每个房间（Axes）有不同的功能——客厅放沙发（折线图）、厨房放餐桌（柱状图）、卧室放床（散点图）。你通过合理的户型设计（布局参数），让每个房间既独立又协调地组合在一起，最终形成一个功能完整的家（Dashboard）。而 `plt.subplots()` 就像请了一位设计师，帮你一次性规划好所有房间的位置和大小。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `plt.subplots()` | `plt.subplots(nrows=1, ncols=1, figsize=None, sharex=False, sharey=False, squeeze=True)` | `nrows`/`ncols`：子图行数/列数；`figsize`：画布尺寸(宽,高)，单位英寸；`sharex`/`sharey`：是否共享x/y轴刻度；`squeeze`：是否压缩单元素维度 | 返回 `(fig, ax)` 元组。`fig` 为 `Figure` 对象；`ax` 为 `Axes` 对象或 `numpy.ndarray`（当多子图时） |
| `fig.add_subplot()` | `fig.add_subplot(nrows, ncols, index)` | `nrows`/`ncols`：网格行数/列数；`index`：子图编号（从1开始，按行优先） | 返回单个 `Axes` 对象，适合动态逐个添加子图 |
| `fig.subplots_adjust()` | `fig.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=None)` | `left`/`bottom`/`right`/`top`：子图区域距画布边缘的比例（0~1）；`wspace`/`hspace`：子图之间水平/垂直间距 | 无返回值，直接修改 `Figure` 对象 |
| `plt.subplot_mosaic()` | `plt.subplot_mosaic(mosaic, figsize=None)` | `mosaic`：字符串列表或字典，用ASCII字符定义复杂布局，如 `[['A','A'],['B','C']]` | 返回 `(fig, dict)`，字典的键为标签名，值为对应的 `Axes` 对象 |

**核心原理**：Matplotlib 的图形体系分为三层——`Figure`（画布）→ `Axes`（坐标系）→ `Artist`（图形元素）。创建多子图本质是在一个 `Figure` 上划分区域并实例化多个 `Axes`。`subplots()` 通过内部网格管理器（`GridSpec`）自动计算每个 `Axes` 的位置坐标（以画布宽高的比例表示），`subplots_adjust()` 则手动微调这些比例值。

---

## 3. 代码示例

### 示例1：基础多子图 — 2×2 网格展示不同图表类型

```python
import matplotlib.pyplot as plt
import numpy as np

# 生成模拟数据
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)
categories = ['A', 'B', 'C', 'D']
values = [25, 40, 15, 30]

# 创建 2×2 的子图网格，画布尺寸 10×8 英寸
fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(10, 8))

# axes 是形状为 (2, 2) 的 ndarray，通过索引访问每个子图
axes[0, 0].plot(x, y1, color='blue')
axes[0, 0].set_title('正弦曲线')
axes[0, 0].set_xlabel('x')
axes[0, 0].set_ylabel('sin(x)')

axes[0, 1].plot(x, y2, color='red', linestyle='--')
axes[0, 1].set_title('余弦曲线')
axes[0, 1].set_xlabel('x')
axes[0, 1].set_ylabel('cos(x)')

axes[1, 0].bar(categories, values, color='green')
axes[1, 0].set_title('分类柱状图')
axes[1, 0].set_ylabel('数值')

# 散点图：随机数据
np.random.seed(42)
scatter_x = np.random.randn(50)
scatter_y = np.random.randn(50)
axes[1, 1].scatter(scatter_x, scatter_y, alpha=0.7, color='purple')
axes[1, 1].set_title('随机散点图')
axes[1, 1].set_xlabel('X')
axes[1, 1].set_ylabel('Y')

# 自动调整子图间距，避免标题重叠
fig.tight_layout()
plt.show()

# 输出结果：显示一个 2×2 的图形窗口，左上为蓝色正弦曲线，
# 右上为红色虚线余弦曲线，左下为绿色柱状图，右下为紫色散点图。
```

### 示例2：共享坐标轴与间距调整 — 多序列对比

```python
import matplotlib.pyplot as plt
import numpy as np

# 生成三组趋势数据
months = np.arange(1, 13)
sales_a = np.random.randint(80, 150, size=12).cumsum()
sales_b = np.random.randint(60, 120, size=12).cumsum()
sales_c = np.random.randint(100, 180, size=12).cumsum()

# 创建 3 行 1 列的子图，共享 x 轴（刻度对齐便于对比）
fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(8, 10), sharex=True)

# 数据列表和标签
datasets = [(sales_a, '产品A', 'blue'), (sales_b, '产品B', 'orange'), (sales_c, '产品C', 'green')]

for i, (data, label, color) in enumerate(datasets):
    axes[i].plot(months, data, color=color, marker='o', label=label)
    axes[i].set_ylabel('累计销量')
    axes[i].legend(loc='upper left')
    axes[i].grid(True, alpha=0.3)

# 只在最下方的子图设置 x 轴标签
axes[2].set_xlabel('月份')

# 手动调整间距：上下子图间距设为 0.5（默认约为 0.2）
fig.subplots_adjust(hspace=0.5)
plt.show()

# 输出结果：三个垂直排列的折线图，x轴刻度完全对齐（共享），
# 每个子图有自己的y轴刻度和图例，子图之间有较大的空白间隔。
```

### 示例3：复杂Dashboard布局 — 使用 `subplot_mosaic`

```python
import matplotlib.pyplot as plt
import numpy as np

# 生成模拟业务数据
np.random.seed(7)
dates = np.arange('2024-01-01', '2024-04-01', dtype='datetime64[W]')
gmv = np.random.randint(5000, 15000, size=len(dates))
orders = np.random.randint(100, 300, size=len(dates))
conversion = np.random.uniform(0.02, 0.08, size=len(dates))

# 使用 ASCII 艺术定义布局：
# 第一行：A 占两列（宽图）；第二行：B 和 C 各占一列
mosaic = """
AA
BC
"""

fig, axes_dict = plt.subplot_mosaic(mosaic, figsize=(12, 8))

# axes_dict 是字典，键为 'A'、'B'、'C'
# 图A：GMV 面积图
axes_dict['A'].fill_between(dates, gmv, alpha=0.4, color='steelblue')
axes_dict['A'].plot(dates, gmv, color='navy', linewidth=2)
axes_dict['A'].set_title('GMV 趋势（周）')
axes_dict['A'].set_ylabel('GMV（元）')

# 图B：订单量柱状图
axes_dict['B'].bar(dates, orders, color='coral', width=4)
axes_dict['B'].set_title('订单量')
axes_dict['B'].set_ylabel('订单数')

# 图C：转化率折线图
axes_dict['C'].plot(dates, conversion * 100, color='teal', marker='s')
axes_dict['C'].set_title('转化率')
axes_dict['C'].set_ylabel('转化率（%）')
axes_dict['C'].set_ylim(0, 10)

# 统一设置 x 轴标签旋转，避免日期重叠
for ax in axes_dict.values():
    for label in ax.get_xticklabels():
        label.set_rotation(45)

fig.suptitle('电商运营 Dashboard', fontsize=16, fontweight='bold')
fig.tight_layout()
plt.show()

# 输出结果：一个 12×8 英寸的 Dashboard。顶部是跨两列的 GMV 面积图，
# 左下是订单量柱状图，右下是转化率折线图。所有日期标签旋转45度避免重叠。
```

---

## 4. 常见错误

### 错误1：索引 `axes` 时维度错误

**错误代码**：
```python
fig, axes = plt.subplots(nrows=2, ncols=2)
axes[0].plot([1, 2, 3], [1, 4, 9])  # TypeError: 'AxesSubplot' object is not subscriptable
```

**错误原因**：当 `nrows` 和 `ncols` 都大于1时，`axes` 是形状为 `(2, 2)` 的二维 `ndarray`，需要用两个索引 `axes[行, 列]` 访问。只用 `axes[0]` 取到的是第一行（一个包含两个 `Axes` 对象的数组），而不是单个子图。

**正确写法**：
```python
fig, axes = plt.subplots(nrows=2, ncols=2)
axes[0, 0].plot([1, 2, 3], [1, 4, 9])  # 正确：访问第1行第1列的子图
```

### 错误2：忘记调用 `tight_layout()` 导致标题重叠

**错误代码**：
```python
fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(6, 6))
axes[0].set_title('上图标题')
axes[1].set_title('下图标题')
plt.show()  # 显示时两个标题挤在一起，甚至被裁剪
```

**错误原因**：Matplotlib 默认不会自动调整子图之间的间距。当子图较多或标题较长时，相邻子图的标题和刻度标签会发生重叠。

**正确写法**：
```python
fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(6, 6))
axes[0].set_title('上图标题')
axes[1].set_title('下图标题')
fig.tight_layout()  # 自动调整间距，防止重叠
plt.show()
```

### 错误3：在 `subplot_mosaic` 中使用了不存在的键

**错误代码**：
```python
mosaic = """
AB
CD
"""
fig, axes_dict = plt.subplot_mosaic(mosaic)
axes_dict['E'].plot([1, 2, 3], [1, 2, 3])  # KeyError: 'E'
```

**错误原因**：`subplot_mosaic` 返回的字典键完全由 `mosaic` 字符串中的字符决定。代码中定义了 A、B、C、D 四个区域，却尝试访问 'E'，导致 `KeyError`。

**正确写法**：
```python
mosaic = """
AB
CD
"""
fig, axes_dict = plt.subplot_mosaic(mosaic)
# 只能访问 'A'、'B'、'C'、'D' 这四个键
axes_dict['A'].plot([1, 2, 3], [1, 2, 3])
# 或者修改 mosaic 字符串加入 'E'
```

---

## 5. 练习

### 练习1：多子图数据对比

**题目**：使用 `plt.subplots()` 创建一个 2×2 的子图网格，分别绘制：
- 左上：`y = x²` 在 [-5, 5] 区间的曲线
- 右上：`y = 2ˣ` 在 [0, 5] 区间的曲线
- 左下：`y = log(x)` 在 [1, 10] 区间的曲线（注意使用 `np.log`）
- 右下：`y = sin(x) / x` 在 [-10, 10] 区间的曲线（注意 x=0 处的处理）

要求：每个子图设置标题、坐标轴标签，整体使用 `fig.suptitle('数学函数图像')` 添加总标题，最后调用 `fig.tight_layout()`。

**答案提示**：
```python
x1 = np.linspace(-5, 5, 100)
x2 = np.linspace(0, 5, 100)
x3 = np.linspace(1, 10, 100)
x4 = np.linspace(-10, 10, 500)
y4 = np.sin(x4) / np.where(x4 == 0, 1e-10, x4)  # 避免除零

fig, axes = plt.subplots(2, 2, figsize=(10, 8))
axes[0, 0].plot(x1, x1**2)
axes[0, 1].plot(x2, 2**x2)
axes[1, 0].plot(x3, np.log(x3))
axes[1, 1].plot(x4, y4)
# ... 设置标题和标签
fig.suptitle('数学函数图像')
fig.tight_layout()
plt.show()
```

### 练习2：构建迷你Dashboard

**题目**：使用 `plt.subplot_mosaic()` 构建一个 3 区域的 Dashboard，模拟股票分析页面：
- 区域 'price'（顶部，跨两列）：某股票 60 天的收盘价折线图（用 `np.cumsum` 生成随机游走数据）
- 区域 'volume'（左下）：对应 60 天的成交量柱状图
- 区域 'return'（右下）：每日收益率（价格变化百分比）的直方图

要求：三个子图共享 x 轴的时间范围（用 `np.arange(60)` 模拟天数），设置合适的标题和颜色。

**答案提示**：
```python
np.random.seed(2024)
prices = 100 + np.cumsum(np.random.randn(60))
volumes = np.random.randint(1000, 5000, 60)
returns = np.diff(prices) / prices[:-1] * 100

mosaic = """
PP
VR
"""
fig, axd = plt.subplot_mosaic(mosaic, figsize=(12, 8))
axd['P'].plot(prices, color='darkblue')
axd['V'].bar(np.arange(60), volumes, color='gray', alpha=0.7)
axd['R'].hist(returns, bins=20, color='orange', edgecolor='white')
# 设置标题、标签，最后 tight_layout()
```

**核心要点**：`subplot_mosaic` 中相同字母出现多次表示该子图跨多个单元格；不同字母代表不同子图。布局字符串的每一行代表一行，空格会被忽略。