# XPath/CSS选择器解析

> 模块：实战：网络数据采集 | 编号：第52讲 | Python数据分析实战

## 1. 概念

XPath（XML Path Language）是一种在 XML/HTML 文档中定位和选择节点的查询语言，而 CSS 选择器（CSS Selector）则是源自 Web 样式表、用于匹配 HTML 元素的标准语法。在网络数据采集中，我们通过 `lxml` 库的 `xpath()` 方法或 `parsel` 库的 `css()` 方法，将网页源码解析为可查询的树形结构，从而精准提取所需数据。

**适用场景**：爬虫中提取商品价格、新闻标题、链接列表；数据清洗中从 HTML 表格抽取结构化数据；自动化测试中定位页面元素。

**生活化类比**：想象你在一个巨大的图书馆（网页）中找一本书（数据）。XPath 就像图书馆的索书号系统——"三楼东区第2排第5格"（绝对路径），也支持"找到所有红色封面的书"（条件筛选）。CSS 选择器则像图书标签系统——"所有贴着'科幻'标签的书"（类名）或"所有作者是刘慈欣的书"（属性匹配）。两者都是定位信息的"导航语言"，只是语法风格不同。

---

## 2. 核心API与原理

| API | 所属库 | 签名 | 参数说明 | 返回值 |
|-----|--------|------|----------|--------|
| `lxml.html.fromstring()` | lxml | `fromstring(html: str) -> HtmlElement` | `html`: 网页源码字符串 | 可查询的 HTML 元素树根节点 |
| `HtmlElement.xpath()` | lxml | `xpath(xpath_expr: str) -> list` | `xpath_expr`: XPath 表达式字符串 | 匹配的节点或值列表（无匹配时为空列表） |
| `parsel.Selector()` | parsel | `Selector(text: str, type: str = 'html') -> Selector` | `text`: 文档字符串；`type`: 文档类型（'html'/'xml'） | Selector 对象，支持链式查询 |
| `Selector.css()` | parsel | `css(query: str) -> SelectorList` | `query`: CSS 选择器字符串 | 匹配的 SelectorList 对象 |
| `Selector.xpath()` | parsel | `xpath(query: str) -> SelectorList` | `query`: XPath 表达式字符串 | 匹配的 SelectorList 对象 |
| `SelectorList.extract()` | parsel | `extract() -> list` | 无 | 提取所有匹配结果的字符串列表 |
| `SelectorList.get()` | parsel | `get(default=None) -> str` | `default`: 无匹配时的默认值 | 提取第一个匹配结果的字符串 |

**原理说明**：`lxml` 将 HTML 解析为 ElementTree（元素树），每个标签成为树中的一个节点，XPath 通过路径表达式（如 `//div[@class='price']`）在树中导航。`parsel` 封装了 lxml，提供更友好的 CSS 选择器语法，并自动处理编码和命名空间。

---

## 3. 代码示例

### 示例1：基础 XPath 提取（lxml 入门）

```python
# 导入 lxml 的 html 解析模块
from lxml import html

# 模拟一个简单的 HTML 页面（实际爬虫中来自 requests.get().text）
html_str = """
<html>
  <body>
    <div class="product">
      <h2 class="title">Python数据分析实战</h2>
      <span class="price">¥89.00</span>
    </div>
    <div class="product">
      <h2 class="title">机器学习入门</h2>
      <span class="price">¥69.50</span>
    </div>
  </body>
</html>
"""

# 将 HTML 字符串解析为元素树
tree = html.fromstring(html_str)

# 使用 XPath 提取所有商品标题（// 表示任意层级）
titles = tree.xpath('//h2[@class="title"]/text()')
print("商品标题:", titles)
# 输出: 商品标题: ['Python数据分析实战', '机器学习入门']

# 提取所有价格文本
prices = tree.xpath('//span[@class="price"]/text()')
print("价格:", prices)
# 输出: 价格: ['¥89.00', '¥69.50']

# 提取第一个商品的完整文本（.// 表示当前节点下的所有文本）
first_product = tree.xpath('//div[@class="product"][1]')[0]
full_text = first_product.xpath('.//text()')
print("第一个商品内容:", full_text)
# 输出: 第一个商品内容: ['Python数据分析实战', '¥89.00']
```

### 示例2：CSS 选择器提取（parsel 进阶）

```python
# 导入 parsel 选择器库
from parsel import Selector

# 模拟一个带链接的 HTML 片段
html_doc = """
<html>
  <body>
    <ul id="nav">
      <li class="item"><a href="/home">首页</a></li>
      <li class="item active"><a href="/products">产品</a></li>
      <li class="item"><a href="/about">关于</a></li>
    </ul>
    <div class="content" data-type="article">
      <p>第一段文字</p>
      <p class="highlight">第二段高亮文字</p>
    </div>
  </body>
</html>
"""

# 创建 Selector 对象
sel = Selector(text=html_doc)

# CSS 选择器：提取所有链接的 href 属性
hrefs = sel.css('a::attr(href)').extract()
print("链接地址:", hrefs)
# 输出: 链接地址: ['/home', '/products', '/about']

# CSS 选择器：提取 class 包含 "active" 的 li 元素中的链接文本
active_text = sel.css('li.active a::text').get()
print("激活项文本:", active_text)
# 输出: 激活项文本: 产品

# 混合使用：先 CSS 定位到 content 区域，再 XPath 提取段落
content_sel = sel.css('div.content')
paragraphs = content_sel.xpath('./p/text()').extract()
print("段落内容:", paragraphs)
# 输出: 段落内容: ['第一段文字', '第二段高亮文字']

# 提取属性值：获取 data-type 属性
data_type = sel.css('div.content::attr(data-type)').get()
print("数据类型:", data_type)
# 输出: 数据类型: article
```

### 示例3：实战——从表格中提取结构化数据

```python
# 导入所需库
from parsel import Selector
import pandas as pd

# 模拟一个股票行情表格页面
html_table = """
<html>
  <body>
    <table id="stock-table">
      <thead>
        <tr><th>代码</th><th>名称</th><th>收盘价</th><th>涨跌幅</th></tr>
      </thead>
      <tbody>
        <tr><td>600519</td><td>贵州茅台</td><td>1685.00</td><td>+1.25%</td></tr>
        <tr><td>000858</td><td>五粮液</td><td>152.30</td><td>-0.87%</td></tr>
        <tr><td>601318</td><td>中国平安</td><td>48.75</td><td>+0.42%</td></tr>
      </tbody>
    </table>
  </body>
</html>
"""

# 解析 HTML
sel = Selector(text=html_table)

# 使用 CSS 选择器提取所有表格行（跳过表头）
rows = sel.css('tbody tr').extract()
print(f"共找到 {len(rows)} 行数据")
# 输出: 共找到 3 行数据

# 逐行提取单元格数据
stock_data = []
for row in sel.css('tbody tr'):
    # 提取每行中的所有 td 文本
    cells = row.css('td::text').extract()
    stock_data.append(cells)

# 转换为 DataFrame 便于分析
columns = ['代码', '名称', '收盘价', '涨跌幅']
df = pd.DataFrame(stock_data, columns=columns)
print(df)
# 输出:
#        代码     名称      收盘价    涨跌幅
# 0  600519  贵州茅台  1685.00  +1.25%
# 1  000858   五粮液   152.30  -0.87%
# 2  601318  中国平安    48.75  +0.42%

# 使用 XPath 提取所有涨跌幅数据并转为数值
change_pct = sel.xpath('//tbody/tr/td[4]/text()').extract()
change_numeric = [float(c.replace('%', '').replace('+', '')) for c in change_pct]
print("涨跌幅数值:", change_numeric)
# 输出: 涨跌幅数值: [1.25, -0.87, 0.42]
```

---

## 4. 常见错误

### 错误1：XPath 索引从 0 开始

```python
# 错误写法：试图取第一个 div
from lxml import html
tree = html.fromstring('<div>a</div><div>b</div>')
first = tree.xpath('//div[0]')  # ❌ 返回空列表！
```

**原因**：XPath 的索引从 1 开始，与 Python 的 0 索引不同。

```python
# 正确写法
first = tree.xpath('//div[1]')  # ✅ 返回第一个 div
print(first[0].text)  # 输出: a
```

### 错误2：忘记 `.extract()` 或 `.get()`

```python
# 错误写法：直接打印 Selector 对象
from parsel import Selector
sel = Selector(text='<p>hello</p>')
result = sel.css('p::text')
print(result)  # ❌ 输出: [<Selector xpath='descendant-or-self::p/text()' data='hello'>]
```

**原因**：`css()` 返回的是 SelectorList 对象，不是字符串。

```python
# 正确写法
result = sel.css('p::text').get()  # ✅ 使用 .get() 或 .extract()
print(result)  # 输出: hello
```

### 错误3：XPath 属性值引号冲突

```python
# 错误写法：属性值包含双引号时与外层引号冲突
tree = html.fromstring('<div class="a">x</div>')
result = tree.xpath('//div[@class="a"]')  # ✅ 这个没问题

# 但当属性值本身含双引号时：
tree2 = html.fromstring('<div data-info="say "hi"">x</div>')
# 错误: tree2.xpath('//div[@data-info="say "hi""]')  # ❌ 语法错误
```

**原因**：XPath 表达式中引号嵌套混乱。

```python
# 正确写法：交替使用单双引号
result = tree2.xpath('//div[@data-info=\'say "hi"\']')  # ✅ 外层单引号
```

---

## 5. 练习

### 练习1：提取嵌套列表数据

给定以下 HTML 片段，请使用 XPath 提取所有 `ul` 下 `li` 中的文本，并区分每个 `ul` 的数据：

```html
<div class="categories">
  <ul><li>水果</li><li>蔬菜</li></ul>
  <ul><li>苹果</li><li>香蕉</li><li>橙子</li></ul>
</div>
```

**答案提示**：先定位 `div.categories` 下的所有 `ul`，再对每个 `ul` 使用 `./li/text()` 提取。注意 `//ul/li` 会合并所有结果，需用 `//div[@class='categories']/ul` 逐层处理。

### 练习2：CSS 选择器实战——翻页链接提取

假设一个新闻列表页包含多个分页链接，HTML 结构如下：

```html
<div class="pagination">
  <a href="/news?page=1">1</a>
  <a href="/news?page=2">2</a>
  <a href="/news?page=3" class="current">3</a>
  <a href="/news?page=4">4</a>
</div>
```

请使用 CSS 选择器完成：
1. 提取所有分页链接的 `href` 属性值；
2. 提取当前页（class="current"）的页码文本；
3. 构建下一页的 URL（假设当前在第 3 页）。

**答案提示**：使用 `a::attr(href)` 提取链接；使用 `a.current::text` 获取当前页码；解析 URL 中的 `page` 参数并加 1，用 `urljoin` 或字符串拼接生成新 URL。注意 `parsel` 的 `Selector` 配合 `response.urljoin()` 可以处理相对路径。