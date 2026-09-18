# Scrapy框架爬虫
> 模块：实战：网络数据采集 | 编号：第53讲 | Python数据分析实战

## 1. 概念

Scrapy 是一个用 Python 编写的开源协作爬虫框架，用于从网站中提取结构化数据。它基于 Twisted 异步网络引擎构建，能够同时发起大量并发请求，实现高效、可扩展的网络数据采集。Scrapy 的核心思想是将爬虫任务拆分为多个可复用的组件（引擎、调度器、下载器、爬虫、管道等），通过中间件机制实现高度定制化。

**生活化类比**：Scrapy 就像一个高效的快递分拣中心。你（爬虫）负责制定取件清单（请求），快递员（下载器）同时骑着多辆电动车（并发请求）去不同地址取件，取回包裹后由分拣员（解析器）拆包分类，最后通过传送带（管道）将不同类别的货物（数据）送到对应的仓库（存储文件或数据库）。

**适用场景**：大规模数据采集（如商品价格监控、新闻聚合、学术论文元数据抓取）、定期增量更新抓取、需要登录或处理复杂页面交互的站点采集。

## 2. 核心API与原理

| API/方法 | 签名 | 参数说明 | 返回值 | 用途 |
|---------|------|---------|--------|------|
| `scrapy.Spider` | `class scrapy.spiders.Spider` | `name`(str): 爬虫唯一名称; `start_urls`(list): 起始URL列表 | Spider对象 | 所有爬虫的基类，需继承并实现`parse()`方法 |
| `parse()` | `def parse(self, response)` | `response`(scrapy.http.Response): 下载器返回的响应对象 | 可迭代的`Request`或`Item`对象 | 默认回调函数，解析响应内容并提取数据 |
| `scrapy.Request` | `scrapy.http.Request(url, callback=None, method='GET', headers=None, body=None, cookies=None, meta=None)` | `url`(str): 目标URL; `callback`(callable): 响应处理函数; `meta`(dict): 传递数据 | Request对象 | 构造新的爬取请求 |
| `response.css()` | `response.css(selector)` | `selector`(str): CSS选择器表达式 | SelectorList对象 | 使用CSS选择器提取页面元素 |
| `response.xpath()` | `response.xpath(selector)` | `selector`(str): XPath表达式 | SelectorList对象 | 使用XPath提取页面元素 |
| `scrapy.Field()` | `scrapy.Field()` | 无参数 | Field对象 | 定义Item的字段，类似字典键的声明 |

**核心原理**：Scrapy 引擎控制整个数据流——引擎从调度器获取URL，交给下载器下载页面，下载完成后将响应交给爬虫的`parse()`方法解析。解析结果（Item或新Request）经过管道处理或再次进入调度器，形成循环。所有组件通过中间件（Middleware）实现钩子扩展。

## 3. 代码示例

### 示例1：基础爬虫——抓取名言网站

```python
# 在项目目录下创建文件 quotes_spider.py
import scrapy

class QuotesSpider(scrapy.Spider):
    name = "quotes"  # 爬虫唯一标识
    
    def start_requests(self):
        """重写起始请求方法，更灵活地控制请求头"""
        url = "https://quotes.toscrape.com/"
        yield scrapy.Request(url, callback=self.parse)
    
    def parse(self, response):
        """解析响应，提取名言文本和作者"""
        # 使用CSS选择器选取所有名言块
        for quote in response.css('div.quote'):
            yield {
                'text': quote.css('span.text::text').get(),
                'author': quote.css('small.author::text').get(),
                'tags': quote.css('div.tags a.tag::text').getall(),
            }
        
        # 提取下一页链接，继续爬取
        next_page = response.css('li.next a::attr(href)').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

# 运行命令：scrapy runspider quotes_spider.py -o quotes.json
# 输出示例（部分）：
# [{"text": "“The world as we have created it is a process of our thinking...”", 
#   "author": "Albert Einstein", 
#   "tags": ["abilities", "choices"]}]
```

### 示例2：使用Item和Pipeline——结构化数据存储

```python
# items.py
import scrapy

class QuoteItem(scrapy.Item):
    """定义结构化数据字段"""
    text = scrapy.Field()
    author = scrapy.Field()
    tags = scrapy.Field()

# pipelines.py
import json

class JsonWriterPipeline:
    """将Item写入JSON文件的管道"""
    def open_spider(self, spider):
        """爬虫启动时打开文件"""
        self.file = open('quotes_output.json', 'w', encoding='utf-8')
        self.file.write('[')
    
    def close_spider(self, spider):
        """爬虫关闭时关闭文件"""
        self.file.write(']')
        self.file.close()
    
    def process_item(self, item, spider):
        """处理每个Item，写入文件"""
        line = json.dumps(dict(item), ensure_ascii=False) + ',\n'
        self.file.write(line)
        return item  # 必须返回Item供后续管道使用

# 在settings.py中启用管道：
# ITEM_PIPELINES = {'myproject.pipelines.JsonWriterPipeline': 300}

# 运行后输出文件内容示例：
# [{"text": "“The world as we have created it is a process of our thinking...”", 
#   "author": "Albert Einstein", 
#   "tags": ["abilities", "choices"]},
#  {"text": "“It is our choices, Harry, that show what we truly are...”", 
#   "author": "J.K. Rowling", 
#   "tags": ["choices", "integrity"]}]
```

### 示例3：带登录和中间件的进阶爬虫

```python
# login_spider.py
import scrapy

class LoginSpider(scrapy.Spider):
    name = "login_spider"
    login_url = "https://httpbin.org/post"  # 测试用登录接口
    start_urls = ["https://httpbin.org/cookies"]
    
    def start_requests(self):
        """先发送登录POST请求"""
        yield scrapy.Request(
            url=self.login_url,
            method='POST',
            body='username=admin&password=123456',  # 表单数据
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            callback=self.after_login
        )
    
    def after_login(self, response):
        """登录成功后访问目标页面"""
        # 检查登录是否成功
        if "logged" in response.text:
            for url in self.start_urls:
                yield scrapy.Request(url, callback=self.parse)
        else:
            self.logger.error("登录失败！")
    
    def parse(self, response):
        """解析登录后的页面内容"""
        yield {
            'url': response.url,
            'cookies': response.css('pre::text').get()
        }

# 运行命令：scrapy runspider login_spider.py
# 输出示例：
# {'url': 'https://httpbin.org/cookies', 
#  'cookies': '{\n  "cookies": {\n    "username": "admin", \n    "password": "123456"\n  }\n}'}
```

## 4. 常见错误

### 错误1：忘记处理请求头导致被反爬

```python
# 错误写法
import scrapy

class BadSpider(scrapy.Spider):
    name = "bad"
    start_urls = ["https://example.com"]
    
    def parse(self, response):
        # 直接请求，没有设置User-Agent
        yield scrapy.Request("https://example.com/page2", callback=self.parse_page2)
```

**错误原因**：未设置`User-Agent`等请求头，网站可能返回403或验证码页面。  
**正确写法**：

```python
import scrapy

class GoodSpider(scrapy.Spider):
    name = "good"
    start_urls = ["https://example.com"]
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    def parse(self, response):
        yield scrapy.Request(
            "https://example.com/page2",
            callback=self.parse_page2,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
```

### 错误2：XPath/CSS选择器写错导致提取为空

```python
# 错误写法
def parse(self, response):
    # 错误：CSS选择器缺少空格或类名错误
    title = response.css('div.contenth2::text').get()  # 实际是 div.content h2
    yield {'title': title}  # 返回None
```

**错误原因**：选择器语法错误，或没有先检查页面结构。  
**正确写法**：

```python
def parse(self, response):
    # 先在Scrapy Shell中调试：scrapy shell "https://example.com"
    # 正确写法：使用空格表示后代选择器
    title = response.css('div.content h2::text').get()
    # 或者使用XPath更精确
    title = response.xpath('//div[@class="content"]//h2/text()').get()
    yield {'title': title}
```

### 错误3：未设置DOWNLOAD_DELAY导致IP被封

```python
# 错误写法
class FastSpider(scrapy.Spider):
    name = "fast"
    start_urls = ["https://example.com/page1", "https://example.com/page2", ...]
    # 没有设置下载延迟，并发请求过高
```

**错误原因**：请求频率过高，触发网站反爬机制。  
**正确写法**：

```python
class PoliteSpider(scrapy.Spider):
    name = "polite"
    start_urls = ["https://example.com/page1", "https://example.com/page2"]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,          # 每个请求间隔2秒
        'CONCURRENT_REQUESTS': 8,     # 限制并发数
        'RANDOMIZE_DOWNLOAD_DELAY': True,  # 随机化延迟
        'RETRY_TIMES': 3,             # 失败重试次数
    }
```

## 5. 练习

### 练习1：动态页面爬取

**题目**：使用 Scrapy 爬取一个使用 JavaScript 渲染内容的网站（如 quotes.toscrape.com/js/），观察直接使用 `response.css()` 能否提取到数据。如果提取不到，请设计解决方案（提示：考虑使用 Splash 或 Selenium 中间件，或寻找页面内嵌的 JSON 数据）。

**答案提示**：
- 先使用 `scrapy shell` 检查响应内容，确认数据是否在HTML源码中
- 查看页面源码，寻找 `script` 标签中的 JSON 数据（如 `var data = [...];`）
- 使用 `response.xpath('//script/text()').re(r'var data = (.*?);')` 提取JSON字符串
- 再用 `json.loads()` 解析为Python对象

### 练习2：增量爬虫设计

**题目**：设计一个爬虫，每天定时抓取新闻网站的最新文章。要求：只抓取当天发布的新文章，不重复抓取已入库的文章。请写出核心的 `parse()` 方法逻辑和去重方案。

**答案提示**：

```python
import scrapy
from datetime import datetime

class NewsSpider(scrapy.Spider):
    name = "news"
    
    def parse(self, response):
        # 假设文章列表在 div.news-item 中
        for article in response.css('div.news-item'):
            title = article.css('h2 a::text').get()
            date_str = article.css('span.date::text').get()
            article_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # 只处理当天的文章
            if article_date.date() == datetime.now().date():
                yield {
                    'title': title,
                    'date': date_str,
                    'url': article.css('h2 a::attr(href)').get()
                }
    
    # 去重方案：
    # 1. 使用Scrapy内置的RFPDupeFilter（基于URL指纹）
    # 2. 在Pipeline中检查数据库/文件是否已存在该URL
    # 3. 使用Redis去重（scrapy-redis库）
    # 4. 自定义去重中间件，基于文章标题哈希
```

**扩展思路**：使用 `scrapy-crawlspider` 的 `Rule` 配合 `LinkExtractor` 自动发现新链接，结合 `scrapy-scheduler` 实现定时调度。