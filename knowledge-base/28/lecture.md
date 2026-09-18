# Pyecharts交互图表

> 模块：数据可视化 | 编号：第28讲 | Python数据分析实战

---

## 1. 概念

Pyecharts 是一个基于 ECharts（百度开源的前端可视化库）的 Python 封装库，它允许数据分析师用纯 Python 代码生成**交互式**网页图表。与 Matplotlib 生成的静态图片不同，Pyecharts 生成的图表支持鼠标悬停提示（Tooltip）、数据缩放（DataZoom）、图例切换（Legend Select）等交互功能，且输出为 HTML 文件，可直接在浏览器中打开或嵌入 Web 应用。

**适用场景**：需要向非技术团队展示动态数据报告、构建数据看板（Dashboard）、制作带有时间轴（Timeline）的动态趋势图，或需要在 Jupyter Notebook 中快速生成可交互探索的图表。

**生活化类比**：如果把 Matplotlib 比作**拍照片**（画面固定，信息一次性呈现），那么 Pyecharts 就是**拍视频**（观看者可以暂停、放大、点击查看细节，甚至切换不同视角）。它让数据"活"起来，观看者不再是被动接收信息，而是主动探索数据。

---

## 2. 核心API与原理

Pyecharts 的核心设计模式是**链式调用**：先创建一个图表对象，然后通过 `.add()` 方法添加数据系列，最后用 `.render()` 生成 HTML 文件。其底层原理是将 Python 数据结构序列化为 ECharts 所需的 JSON 配置，再由前端 JavaScript 引擎渲染。

| API 名称 | 签名 | 参数说明 | 返回值 |
|---------|------|---------|--------|
| `Bar` | `Bar(init_opts=opts.InitOpts())` | `init_opts`: 初始化选项（如宽度、高度、主题） | 柱状图对象 |
| `add_xaxis` | `add_xaxis(xaxis_data)` | `xaxis_data`: 列表，X 轴类目数据 | 图表对象自身（支持链式调用） |
| `add_yaxis` | `add_yaxis(series_name, y_axis)` | `series_name`: 系列名称；`y_axis`: 列表，Y 轴数值数据 | 图表对象自身 |
| `set_global_opts` | `set_global_opts(title_opts=None, tooltip_opts=None, ...)` | 接受 `opts.TitleOpts`、`opts.TooltipOpts` 等全局配置对象 | 图表对象自身 |
| `render` | `render(path="render.html")` | `path`: 输出 HTML 文件路径 | 无（生成文件） |

**核心原理说明**：Pyecharts 将 Python 的 `list`、`dict` 等数据结构转换为 ECharts 能识别的 JavaScript 对象。例如，`add_yaxis("销量", [5, 20, 36])` 会被序列化为 `{"name": "销量", "type": "bar", "data": [5, 20, 36]}` 这样的配置项。图表的所有交互行为（如 Tooltip 显示、缩放）均由 ECharts 前端引擎处理，Pyecharts 只负责生成配置。

---

## 3. 代码示例

### 示例 1：基础交互柱状图（入门）

```python
# 导入 pyecharts 相关模块
from pyecharts.charts import Bar
from pyecharts import options as opts

# 创建柱状图对象，设置宽度和高度
bar = (
    Bar(init_opts=opts.InitOpts(width="800px", height="500px"))
    .add_xaxis(["苹果", "香蕉", "橙子", "葡萄", "西瓜"])  # X轴类目
    .add_yaxis("销量", [120, 200, 150, 80, 170])          # Y轴数据
    .set_global_opts(
        title_opts=opts.TitleOpts(title="水果销量对比"),   # 图表标题
        tooltip_opts=opts.TooltipOpts(trigger="axis"),     # 鼠标悬停显示提示
    )
)

# 生成 HTML 文件
bar.render("fruit_sales.html")
print("图表已生成：fruit_sales.html")
# 输出结果：图表已生成：fruit_sales.html
# （在浏览器中打开该文件，鼠标悬停可查看每个柱子的具体数值）
```

### 示例 2：多系列折线图 + 数据缩放（进阶）

```python
from pyecharts.charts import Line
from pyecharts import options as opts
import random

# 生成模拟数据：2023年1-12月
months = [f"{i}月" for i in range(1, 13)]
product_a = [random.randint(100, 500) for _ in range(12)]  # 产品A销量
product_b = [random.randint(80, 450) for _ in range(12)]   # 产品B销量

line = (
    Line(init_opts=opts.InitOpts(width="1000px", height="600px"))
    .add_xaxis(months)
    .add_yaxis("产品A", product_a, is_smooth=True)   # 平滑曲线
    .add_yaxis("产品B", product_b, is_smooth=True)
    .set_global_opts(
        title_opts=opts.TitleOpts(title="2023年产品销售趋势"),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
        datazoom_opts=[opts.DataZoomOpts()],          # 添加缩放组件
        legend_opts=opts.LegendOpts(pos_top="5%"),    # 图例位置
    )
)

line.render("sales_trend.html")
print("图表已生成：sales_trend.html")
# 输出结果：图表已生成：sales_trend.html
# （图表下方有缩放滑块，可拖动查看不同时间段的数据；点击图例可隐藏/显示对应系列）
```

### 示例 3：多图表组合 Dashboard（高级）

```python
from pyecharts.charts import Bar, Line, Pie, Grid
from pyecharts import options as opts

# 准备数据
categories = ["北京", "上海", "广州", "深圳", "杭州"]
values = [150, 230, 180, 290, 210]

# 创建柱状图
bar = (
    Bar()
    .add_xaxis(categories)
    .add_yaxis("GDP（亿元）", values)
    .set_global_opts(title_opts=opts.TitleOpts(title="城市GDP柱状图"))
)

# 创建饼图
pie = (
    Pie()
    .add("", [list(z) for z in zip(categories, values)])
    .set_global_opts(title_opts=opts.TitleOpts(title="城市GDP占比"))
)

# 使用 Grid 组合图表（左右布局）
grid = (
    Grid(init_opts=opts.InitOpts(width="1200px", height="500px"))
    .add(bar, grid_opts=opts.GridOpts(pos_left="55%"))   # 柱状图放右侧
    .add(pie, grid_opts=opts.GridOpts(pos_left="10%"))   # 饼图放左侧
)

grid.render("dashboard.html")
print("Dashboard 已生成：dashboard.html")
# 输出结果：Dashboard 已生成：dashboard.html
# （一个页面同时展示两个交互图表，饼图点击扇区可高亮，柱状图悬停显示数值）
```

---

## 4. 常见错误

### 错误 1：忘记调用 `render()` 方法
```python
# 错误写法：只创建了对象，没有生成文件
from pyecharts.charts import Bar
bar = Bar()
bar.add_xaxis(["A", "B"])
bar.add_yaxis("值", [1, 2])
# 此时没有任何输出文件！

# 正确写法：必须调用 render()
bar.render("output.html")
```

### 错误 2：X 轴和 Y 轴数据长度不匹配
```python
# 错误写法：X轴有3个类目，Y轴只有2个数据
from pyecharts.charts import Bar
bar = Bar()
bar.add_xaxis(["A", "B", "C"])
bar.add_yaxis("销量", [100, 200])  # 长度不一致，图表渲染异常

# 正确写法：确保长度一致
bar.add_yaxis("销量", [100, 200, 300])
```

### 错误 3：在 Jupyter Notebook 中未使用 `render_notebook()`
```python
# 错误写法：在 Notebook 中调用 render() 会生成文件，但不会在单元格内显示
from pyecharts.charts import Bar
bar = Bar()
bar.add_xaxis(["A", "B"])
bar.add_yaxis("值", [1, 2])
bar.render()  # 只在当前目录生成 HTML，Notebook 里看不到图表

# 正确写法：在 Notebook 环境中使用 render_notebook()
bar.render_notebook()  # 直接在单元格内显示交互图表
```

---

## 5. 练习

### 练习 1：动态时间轴图表
**题目**：使用 `Timeline` 组件（`from pyecharts.charts import Timeline`），创建 2020-2023 年每年各季度销售额的柱状图，要求：
- 每年一个柱状图（4 个季度为 X 轴）
- 通过时间轴滑块切换不同年份
- 添加标题"年度季度销售额分析"

**答案提示**：
```python
from pyecharts.charts import Bar, Timeline
from pyecharts import options as opts

timeline = Timeline()
for year in [2020, 2021, 2022, 2023]:
    bar = (
        Bar()
        .add_xaxis(["Q1", "Q2", "Q3", "Q4"])
        .add_yaxis("销售额", [random.randint(100, 500) for _ in range(4)])
        .set_global_opts(title_opts=opts.TitleOpts(title=f"{year}年销售额"))
    )
    timeline.add(bar, time_point=str(year))
timeline.render("timeline_sales.html")
```

### 练习 2：交互式数据探索
**题目**：使用 `Scatter`（散点图）绘制 50 个随机点的分布，要求：
- 点的颜色根据数值大小渐变（使用 `VisualMapOpts`）
- 鼠标悬停显示每个点的具体坐标
- 添加数据缩放组件，支持框选放大

**答案提示**：
```python
from pyecharts.charts import Scatter
from pyecharts import options as opts
import random

x_data = [random.randint(0, 100) for _ in range(50)]
y_data = [random.randint(0, 100) for _ in range(50)]

scatter = (
    Scatter()
    .add_xaxis(x_data)
    .add_yaxis("数据点", y_data)
    .set_global_opts(
        title_opts=opts.TitleOpts(title="散点图交互探索"),
        visualmap_opts=opts.VisualMapOpts(max_=100),  # 颜色映射
        datazoom_opts=[opts.DataZoomOpts(type_="inside")],  # 内部缩放
        tooltip_opts=opts.TooltipOpts(formatter="{c}"),  # 自定义提示
    )
)
scatter.render("scatter_interactive.html")
```

---

**学习建议**：Pyecharts 的官方文档（https://pyecharts.org）提供了丰富的图表类型和配置示例。建议在掌握基础柱状图、折线图后，逐步探索 `Geo`（地理图表）、`Graph`（关系图）等高级图表，并结合 `Flask` 或 `Django` 将图表嵌入 Web 应用，实现真正的数据产品化。