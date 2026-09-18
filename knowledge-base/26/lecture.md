# Matplotlib基础图表

> 模块：数据可视化 | 编号：第26讲 | Python数据分析实战

---

## 1. 概念

Matplotlib 是 Python 最核心的 2D 绘图库，它提供了一套面向对象的绘图接口，能够将数据以折线图、散点图、柱状图等可视化形式呈现，帮助数据分析师快速洞察数据分布、趋势与异常。其核心思想是"**Figure（画布）→ Axes（坐标系）→ Artist（图形元素）**"的三层结构：Figure 是整张画布，Axes 是画布上的一个子图区域，而折线、点、坐标轴标签等均为 Artist 对象。

**生活化类比**：Matplotlib 就像一位画师。Figure 是画师手中的整张画纸，Axes 是画纸上用铅笔框出的一个绘图区（可以框多个），而 `plot()`、`scatter()` 等函数则是画师手中的画笔，在绘图区上画出不同的图形元素。`show()` 则是画师把画作展示给观众。

**适用场景**：数据探索阶段的趋势分析（折线图）、相关性分析（散点图）、类别对比（柱状图），以及报告中的静态图表输出。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 |
|-----|------|----------|--------|
| `matplotlib.pyplot.plot` | `plot(*args, **kwargs)` | `*args`：x 数据、y 数据（可只传 y，x 默认索引）；`**kwargs`：`color`（颜色）、`linestyle`（线型）、`linewidth`（线宽）、`marker`（标记点样式）、`label`（图例标签） | `list[Line2D]`：绘制的线对象列表 |
| `matplotlib.pyplot.scatter` | `scatter(x, y, s=None, c=None, marker=None, alpha=None)` | `x, y`：数据点坐标；`s`：点大小（数值或数组）；`c`：颜色（字符串或数组）；`marker`：点样式；`alpha`：透明度（0~1） | `PathCollection`：散点集合对象 |
| `matplotlib.pyplot.bar` | `bar(x, height, width=0.8, bottom=None, color=None, label=None)` | `x`：x 轴刻度位置；`height`：柱子的高度；`width`：柱子宽度；`bottom`：柱底位置（堆叠图用）；`color`：颜色；`label`：图例标签 | `BarContainer`：柱状图容器对象 |
| `matplotlib.pyplot.xlabel / ylabel / title` | `xlabel(xlabel, fontsize=None)` 等 | 接受字符串文本，`fontsize` 控制字号 | `Text`：文本对象 |
| `matplotlib.pyplot.legend` | `legend(loc='best', frameon=True)` | `loc`：图例位置（如 `'upper right'`、`'lower left'`）；`frameon`：是否显示图例边框 | `Legend`：图例对象 |

**核心原理**：所有绘图函数最终都会在当前 Axes 上创建对应的 Artist 对象，并返回该对象供进一步修改。调用 `plt.show()` 时，Matplotlib 将 Figure 渲染为图形窗口或保存到文件（`plt.savefig()`）。

---

## 3. 代码示例

### 示例 1：基础折线图（入门）

```python
import matplotlib.pyplot as plt

# 准备数据：某城市一周最高气温（单位：°C）
days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
temps = [22, 25, 24, 28, 30, 31, 29]

# 创建画布和坐标系（figsize 控制画布宽高，单位英寸）
fig, ax = plt.subplots(figsize=(8, 5))

# 绘制折线图：marker='o' 表示在数据点画圆点，linestyle='--' 表示虚线
ax.plot(days, temps, marker='o', linestyle='--', color='crimson', linewidth=2, label='最高气温')

# 添加标题和轴标签
ax.set_title('一周最高气温变化趋势', fontsize=14)
ax.set_xlabel('星期')
ax.set_ylabel('气温 (°C)')

# 显示图例（根据 label 参数自动生成）
ax.legend()

# 显示网格线，便于读数
ax.grid(True, linestyle=':', alpha=0.6)

# 展示图形
plt.show()

# 输出结果：弹出窗口显示带网格的红色虚线折线图，数据点上有圆点标记
```

### 示例 2：散点图与柱状图（进阶）

```python
import matplotlib.pyplot as plt

# 准备数据：学生学习时长 vs 考试成绩
study_hours = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
scores = [55, 60, 62, 70, 75, 78, 82, 85, 88, 92]

# 创建 1 行 2 列的子图布局
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# 左子图：散点图，点大小随成绩变化（s 参数），颜色用蓝色
ax1.scatter(study_hours, scores, s=scores, c='steelblue', alpha=0.7)
ax1.set_title('学习时长 vs 成绩散点图')
ax1.set_xlabel('学习时长 (小时)')
ax1.set_ylabel('考试成绩')

# 右子图：柱状图，展示不同科目的平均分
subjects = ['数学', '语文', '英语', '物理', '化学']
avg_scores = [85, 78, 90, 72, 88]
# 用 range(len(subjects)) 生成 x 轴刻度位置
ax2.bar(range(len(subjects)), avg_scores, color=['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC'])
ax2.set_title('各科目平均分')
ax2.set_xlabel('科目')
ax2.set_ylabel('平均分')
# 将 x 轴刻度替换为科目名称
ax2.set_xticks(range(len(subjects)))
ax2.set_xticklabels(subjects)

# 自动调整子图间距，避免重叠
plt.tight_layout()
plt.show()

# 输出结果：左侧为点大小随成绩增大的蓝色散点图，右侧为五色柱状图
```

### 示例 3：多数据系列与图例定制（综合）

```python
import matplotlib.pyplot as plt

# 准备数据：两个城市 1-6 月降水量（单位：mm）
months = ['1月', '2月', '3月', '4月', '5月', '6月']
city_a = [50, 60, 80, 120, 150, 200]
city_b = [30, 40, 55, 70, 90, 110]

fig, ax = plt.subplots(figsize=(9, 5))

# 绘制两条折线，一条实线一条点划线
ax.plot(months, city_a, marker='s', color='darkorange', linewidth=2, label='A市')
ax.plot(months, city_b, marker='^', linestyle='-.', color='seagreen', linewidth=2, label='B市')

# 在数据点上方添加数值标注（zip 同时遍历两个列表）
for x, y in zip(months, city_a):
    ax.annotate(f'{y}', (x, y), textcoords='offset points', xytext=(0, 10), ha='center', fontsize=9)

ax.set_title('两城市月降水量对比', fontsize=15)
ax.set_xlabel('月份')
ax.set_ylabel('降水量 (mm)')

# 定制图例：右上角，带阴影边框
ax.legend(loc='upper left', shadow=True, frameon=True)

# 设置 y 轴范围，留出标注空间
ax.set_ylim(0, 250)

plt.show()

# 输出结果：两条不同颜色和线型的折线图，A市每个数据点上方标注数值，图例带阴影
```

---

## 4. 常见错误

### 错误 1：忘记调用 `plt.show()` 导致图形不显示

```python
# 错误写法
import matplotlib.pyplot as plt
plt.plot([1, 2, 3], [4, 5, 6])
# 在脚本中运行时不会弹出图形窗口

# 正确写法
import matplotlib.pyplot as plt
plt.plot([1, 2, 3], [4, 5, 6])
plt.show()  # 必须显式调用才显示
```

**原因**：在非交互式环境（如脚本文件）中，Matplotlib 默认不自动显示图形，必须调用 `show()` 触发渲染。

### 错误 2：x 轴和 y 轴数据长度不一致

```python
# 错误写法
import matplotlib.pyplot as plt
x = [1, 2, 3, 4]
y = [10, 20, 30]
plt.plot(x, y)  # 报错：x and y must have same first dimension

# 正确写法
import matplotlib.pyplot as plt
x = [1, 2, 3, 4]
y = [10, 20, 30, 40]
plt.plot(x, y)
plt.show()
```

**原因**：`plot()` 要求 x 和 y 数组长度一致，否则无法建立一一对应的映射关系。

### 错误 3：绘制柱状图时 x 轴标签直接传字符串导致报错

```python
# 错误写法
import matplotlib.pyplot as plt
subjects = ['数学', '语文', '英语']
scores = [85, 78, 90]
plt.bar(subjects, scores)  # 某些版本会报错或显示异常

# 正确写法
import matplotlib.pyplot as plt
subjects = ['数学', '语文', '英语']
scores = [85, 78, 90]
plt.bar(range(len(subjects)), scores)  # 用数值位置
plt.xticks(range(len(subjects)), subjects)  # 再替换标签
plt.show()
```

**原因**：`bar()` 的 `x` 参数要求数值型刻度位置，字符串需要先用 `range()` 生成位置，再通过 `xticks()` 替换显示标签。

---

## 5. 练习

### 练习 1：绘制双轴折线图

**题目**：某公司 2023 年 1-6 月的销售额（万元）为 `[120, 135, 128, 150, 165, 180]`，利润率（%）为 `[15, 18, 16, 20, 22, 25]`。请在同一张图上用双 y 轴（左侧销售额、右侧利润率）绘制两条折线图。

**答案提示**：使用 `ax.twinx()` 创建共享 x 轴的第二个 y 轴。左侧轴用 `ax.plot()` 画销售额（蓝色实线），右侧轴用 `ax2.plot()` 画利润率（红色虚线）。注意设置 `ax2.set_ylabel()` 区分轴标签。

### 练习 2：堆叠柱状图

**题目**：某班级男生和女生在四个社团（篮球、音乐、绘画、编程）的报名人数如下：男生 `[12, 8, 6, 10]`，女生 `[5, 10, 9, 7]`。请绘制堆叠柱状图（每个社团一根柱子，男生在下方、女生在上方），并添加图例。

**答案提示**：第一次调用 `bar()` 绘制男生数据，第二次调用 `bar()` 时设置 `bottom=boys` 参数将女生数据堆叠在男生上方。`bottom` 参数接收一个与 `height` 等长的数组，表示每根柱子的起始高度。最后用 `legend()` 添加图例，`xticks()` 设置社团名称。