# 图表配色与商业报告排版

> 模块：数据可视化 | 编号：第30讲 | Python数据分析实战

---

## 1. 概念

图表配色与商业报告排版，是指通过科学、系统的色彩搭配与版面布局，使数据可视化作品不仅准确传达信息，还具备专业、美观、易读的视觉呈现。其核心目标是**减少读者的认知负担**，让数据"自己说话"。

在商业场景中，一份配色混乱、排版随意的图表会严重削弱数据的说服力；反之，精心设计的配色与排版能迅速抓住读者的注意力，引导视线聚焦关键信息。本讲涵盖三大核心内容：**色彩理论基础**（色相、饱和度、明度）、**Matplotlib 配色体系**（内置 colormap、自定义颜色、色盲友好方案），以及**商业报告排版规范**（画布尺寸、字体层级、网格布局、留白原则）。

**生活化类比**：想象你在做一道菜——食材（数据）本身很新鲜，但如果没有合理的摆盘（排版）和诱人的色泽（配色），食客（读者）的食欲（理解力）就会大打折扣。好的配色与排版，就像米其林大厨的摆盘艺术，让美味（洞察）一目了然。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `matplotlib.pyplot.colormaps()` | `colormaps()` | 无参数 | `list[str]` — 所有内置 colormap 名称列表 |
| `matplotlib.colormaps.get_cmap(name)` | `get_cmap(name)` | `name: str` — colormap 名称（如 `'viridis'`、`'plasma'`） | `Colormap` 对象，可传入 `cmap` 参数 |
| `matplotlib.pyplot.subplots(nrows, ncols, figsize)` | `subplots(nrows=1, ncols=1, figsize=None)` | `nrows, ncols: int` — 子图行列数；`figsize: tuple[float, float]` — 画布尺寸（英寸） | `(fig, axes)` — `Figure` 对象和 `Axes` 对象（或数组） |
| `matplotlib.pyplot.tight_layout()` | `tight_layout(pad=1.08)` | `pad: float` — 子图间距（英寸） | `None` — 自动调整子图间距，避免重叠 |
| `matplotlib.rc_context(rcparams)` | `rc_context(rc=None)` | `rc: dict` — 全局绘图参数（如字体、颜色、网格） | 上下文管理器，退出后自动恢复默认设置 |

**配色原理**：Matplotlib 的 colormap 分为三类——**顺序型**（sequential，如 `'viridis'`、`'Blues'`，适合连续数据）、**发散型**（diverging，如 `'RdBu'`、`'coolwarm'`，适合有正负中心的数据）、**定性型**（qualitative，如 `'Set2'`、`'tab10'`，适合分类数据）。商业报告推荐使用色盲友好的 `'viridis'` 或 `'plasma'`。

---

## 3. 代码示例

### 示例 1：基础配色 — 使用内置 colormap 与自定义颜色

```python
import matplotlib.pyplot as plt
import numpy as np

# 生成示例数据
categories = ['A', 'B', 'C', 'D', 'E']
values = [23, 45, 56, 78, 32]

# 方式一：使用内置定性 colormap 'Set2'
colors = plt.colormaps['Set2'](np.linspace(0, 1, len(categories)))
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# 左图：内置 colormap
ax1.bar(categories, values, color=colors, edgecolor='white', linewidth=1.2)
ax1.set_title('使用 Set2 colormap', fontsize=14, fontweight='bold')
ax1.set_ylabel('数值')

# 方式二：自定义十六进制颜色（商业报告常用）
custom_colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B']
ax2.bar(categories, values, color=custom_colors, edgecolor='white', linewidth=1.2)
ax2.set_title('自定义商业配色', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.show()
# 输出：两张并排的柱状图，左侧为柔和粉彩色调，右侧为深色商务色调
```

### 示例 2：进阶 — 使用 rc_context 统一报告风格

```python
import matplotlib.pyplot as plt
import numpy as np

# 生成时间序列数据
np.random.seed(42)
months = ['1月', '2月', '3月', '4月', '5月', '6月']
sales = np.random.randint(80, 200, size=6)
profit = sales * np.random.uniform(0.2, 0.35, size=6)

# 使用 rc_context 统一全局风格（商业报告标准配置）
with plt.rc_context({
    'font.family': 'sans-serif',          # 无衬线字体，更现代
    'font.size': 11,                       # 全局字号
    'axes.titlesize': 16,                  # 标题字号
    'axes.titleweight': 'bold',            # 标题加粗
    'axes.grid': True,                     # 开启网格
    'grid.alpha': 0.3,                     # 网格透明度
    'grid.linestyle': '--',                # 虚线网格
    'axes.spines.top': False,              # 去掉上边框
    'axes.spines.right': False,            # 去掉右边框
    'figure.dpi': 120                      # 高分辨率输出
}):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 双轴图：柱状图（销售额）+ 折线图（利润率）
    bars = ax.bar(months, sales, color='#2E86AB', alpha=0.8, label='销售额')
    ax.set_ylabel('销售额（万元）', fontsize=12)
    ax.set_ylim(0, 250)
    
    ax2 = ax.twinx()  # 创建共享 x 轴的第二个 y 轴
    ax2.plot(months, profit, color='#C73E1D', marker='o', linewidth=2.5, 
             markersize=8, label='利润')
    ax2.set_ylabel('利润（万元）', fontsize=12)
    ax2.set_ylim(0, 80)
    
    # 添加数据标签
    for bar, val in zip(bars, sales):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                f'{val}', ha='center', fontsize=10)
    
    # 合并图例
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=False)
    
    ax.set_title('2024年上半年销售业绩报告', pad=15)
    plt.tight_layout()
    plt.show()
# 输出：一张商业风格的双轴组合图，包含柱状图与折线图，网格虚线、无上右边框、带数据标签
```

### 示例 3：高级 — 多子图商业看板排版

```python
import matplotlib.pyplot as plt
import numpy as np

# 生成模拟数据
np.random.seed(7)
dates = np.arange('2024-01', '2024-07', dtype='datetime64[M]')
revenue = np.random.randint(100, 300, size=6)
cost = revenue * np.random.uniform(0.4, 0.6, size=6)
regions = ['华东', '华北', '华南', '西部']
region_sales = np.random.randint(50, 150, size=4)

# 创建 2x2 子图布局，指定画布尺寸与间距
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('2024 上半年商业数据看板', fontsize=20, fontweight='bold', y=0.98)

# 子图1：营收与成本趋势（顺序型 colormap）
ax1 = axes[0, 0]
ax1.plot(dates, revenue, color='#2E86AB', marker='s', linewidth=2, label='营收')
ax1.plot(dates, cost, color='#C73E1D', marker='^', linewidth=2, label='成本')
ax1.fill_between(dates, revenue, cost, alpha=0.15, color='#2E86AB')
ax1.set_title('营收与成本趋势', fontsize=14)
ax1.legend(frameon=False)
ax1.grid(alpha=0.3, linestyle='--')

# 子图2：区域销售占比（饼图，使用发散型 colormap）
ax2 = axes[0, 1]
colors = plt.colormaps['coolwarm'](np.linspace(0.2, 0.8, len(regions)))
wedges, texts, autotexts = ax2.pie(
    region_sales, labels=regions, colors=colors, autopct='%1.1f%%',
    startangle=90, explode=(0.05, 0, 0, 0), textprops={'fontsize': 12}
)
ax2.set_title('区域销售占比', fontsize=14)

# 子图3：月度营收柱状图（带渐变效果）
ax3 = axes[1, 0]
month_labels = [str(d)[:7] for d in dates]
gradient_colors = plt.colormaps['viridis'](np.linspace(0.2, 0.9, len(dates)))
bars = ax3.bar(month_labels, revenue, color=gradient_colors, edgecolor='white')
ax3.set_title('月度营收分布', fontsize=14)
ax3.set_ylim(0, 350)
for bar, val in zip(bars, revenue):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 8, 
             f'{val}', ha='center', fontsize=10)

# 子图4：成本率散点图（展示利润率与规模关系）
ax4 = axes[1, 1]
profit_rate = (revenue - cost) / revenue * 100
scatter = ax4.scatter(revenue, profit_rate, s=revenue*3, c=profit_rate, 
                      cmap='plasma', alpha=0.7, edgecolors='white')
ax4.set_xlabel('营收（万元）')
ax4.set_ylabel('利润率（%）')
ax4.set_title('规模与利润率关系', fontsize=14)
plt.colorbar(scatter, ax=ax4, label='利润率')

plt.tight_layout(rect=[0, 0, 1, 0.95])  # 为总标题预留空间
plt.show()
# 输出：2x2 商业看板，包含趋势图、饼图、渐变柱状图、散点图，配色统一协调
```

---

## 4. 常见错误

### 错误 1：滥用默认彩虹色（`'jet'`）
**错误原因**：`'jet'` colormap 虽然色彩丰富，但存在两个问题——颜色过渡不均匀（会在数据中间产生视觉"假边界"），且对色盲读者极不友好（红绿色无法区分）。
```python
# 错误写法
plt.imshow(data, cmap='jet')

# 正确写法：使用感知均匀且色盲友好的 colormap
plt.imshow(data, cmap='viridis')  # 或 'plasma'、'cividis'
```

### 错误 2：子图标题与标签重叠
**错误原因**：创建多个子图后直接绘图，未调用 `tight_layout()` 或未设置 `figsize`，导致标题、轴标签互相挤压。
```python
# 错误写法
fig, axes = plt.subplots(2, 2)  # 默认 figsize=(6.4, 4.8) 太小
axes[0, 0].set_title('很长的标题文字')
# ... 绘图后未调整布局，标题重叠

# 正确写法
fig, axes = plt.subplots(2, 2, figsize=(12, 10))  # 指定足够大的画布
# ... 绘图
plt.tight_layout()  # 自动调整子图间距
plt.show()
```

### 错误 3：忽略配色一致性
**错误原因**：同一报告中不同图表分别使用不同 colormap 表示同一类别变量，导致读者混淆。
```python
# 错误写法：同一类别在不同图中颜色不同
ax1.bar(categories, values1, color=['red', 'blue', 'green', 'yellow', 'purple'])
ax2.bar(categories, values2, color=['#FF0000', '#0000FF', '#00FF00', '#FFFF00', '#800080'])

# 正确写法：定义统一的颜色映射字典
category_colors = {'A': '#2E86AB', 'B': '#A23B72', 'C': '#F18F01', 
                   'D': '#C73E1D', 'E': '#3B1F2B'}
ax1.bar(categories, values1, color=[category_colors[c] for c in categories])
ax2.bar(categories, values2, color=[category_colors[c] for c in categories])
```

---

## 5. 练习

### 练习 1：设计一个色盲友好的双变量对比图
**题目**：使用 `'cividis'` colormap 创建一张热力图，展示某公司 12 个月 × 4 个区域的销售数据。要求：使用 `numpy.random.randint` 生成 12×4 的模拟数据，添加颜色条（colorbar），设置合适的 `figsize`，并确保标题和轴标签清晰可读。

**答案提示**：
```python
# 关键步骤：
# 1. data = np.random.randint(50, 200, size=(12, 4))
# 2. plt.imshow(data, cmap='cividis', aspect='auto')
# 3. plt.colorbar(label='销售额（万元）')
# 4. 设置 x 轴为区域名，y 轴为月份，使用 plt.xticks/plt.yticks
# 5. 添加注释：plt.title('区域月度销售热力图', fontweight='bold')
```

### 练习 2：商业报告排版优化
**题目**：给定以下代码，它生成了一个包含 3 个子图的报告，但存在排版混乱、配色不统一的问题。请重写代码，要求：①统一使用 `'Set2'` colormap 的配色；②调整 `figsize` 使子图不重叠；③使用 `rc_context` 统一字体和网格风格；④为每个子图添加清晰的数据标签。

```python
# 原始问题代码
fig, axes = plt.subplots(1, 3)
axes[0].bar(['A', 'B', 'C'], [10, 20, 15], color=['red', 'green', 'blue'])
axes[1].plot([1, 2, 3], [5, 8, 6], color='purple')
axes[2].pie([30, 40, 30], labels=['X', 'Y', 'Z'])
plt.show()
```

**答案提示**：
- 使用 `plt.colormaps['Set2'](np.linspace(0, 1, 3))` 生成统一配色
- 设置 `figsize=(15, 5)` 并调用 `plt.tight_layout()`
- 用 `with plt.rc_context({...})` 包裹绘图代码，设置 `axes.grid: True`、`font.size: 12` 等
- 柱状图添加数值标签（`ax.text`），折线图添加数据点标记（`marker='o'`），饼图使用 `autopct='%1.1f%%'`