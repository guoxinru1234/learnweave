# HTTP协议与Requests库
> 模块：实战：网络数据采集 | 编号：第51讲 | Python数据分析实战

## 1. 概念

HTTP（HyperText Transfer Protocol，超文本传输协议）是互联网上应用最为广泛的一种网络传输协议，它定义了客户端（如浏览器、Python脚本）与服务器之间请求和响应的标准格式。当我们使用Python进行网络数据采集时，本质上是模拟浏览器向目标服务器发送HTTP请求，并接收服务器返回的HTML、JSON、XML等格式的数据。

**生活化类比**：HTTP协议就像你去餐厅点餐的过程。你（客户端）向服务员（服务器）说出你的需求（发送请求），服务员根据你的需求去后厨准备，然后把菜端给你（返回响应）。请求中包含了你要什么菜（URL路径）、你的特殊要求（请求头Headers）、以及你可能要提交的表单（请求体Body）。而状态码就像是服务员给你的反馈——"200"表示"好的，马上上菜"，"404"表示"不好意思，这道菜我们菜单上没有"。

**适用场景**：爬取静态网页数据、调用RESTful API接口（如天气、股票、社交媒体数据）、自动化测试、数据采集管道的第一步——获取原始数据。

## 2. 核心API与原理

Requests库是Python中最流行的HTTP客户端库，基于urllib3封装，提供了更简洁、更人性化的API。以下是核心方法：

| 方法/属性 | 签名 | 参数说明 | 返回值 |
|-----------|------|----------|--------|
| `requests.get()` | `get(url, params=None, headers=None, timeout=None)` | `url`: 请求地址；`params`: 字典或元组列表，自动编码为查询字符串；`headers`: 请求头字典；`timeout`: 超时秒数（元组可分别指定连接和读取超时） | `Response` 对象 |
| `requests.post()` | `post(url, data=None, json=None, headers=None, timeout=None)` | `data`: 表单数据（字典）；`json`: JSON数据（自动序列化并设置Content-Type为application/json）；其余同`get()` | `Response` 对象 |
| `Response.status_code` | 属性 | 无 | 整数，HTTP状态码（200成功，404未找到，500服务器错误） |
| `Response.text` | 属性 | 无 | 字符串，服务器返回的响应体（自动根据编码解码） |
| `Response.json()` | 方法 | 无 | 将响应体解析为Python字典/列表（要求响应体为合法JSON） |
| `Response.headers` | 属性 | 无 | 字典，响应头信息（大小写不敏感） |

**核心原理**：Requests库封装了TCP连接、HTTP报文构建、SSL/TLS握手（HTTPS）、重定向处理、Cookie持久化等底层细节。当你调用`get()`时，它构建一个HTTP请求报文，通过socket发送到服务器，然后接收响应报文并解析为`Response`对象。`params`参数会自动进行URL编码（如空格转为`%20`），`json`参数会自动调用`json.dumps()`序列化。

## 3. 代码示例

### 示例1：基础GET请求与状态码检查（入门）

```python
import requests

# 发送GET请求到示例API
url = "https://httpbin.org/get"  # httpbin.org是常用的HTTP测试服务
response = requests.get(url, timeout=5)

# 检查状态码
print(f"状态码: {response.status_code}")  # 输出: 状态码: 200

# 查看响应头中的服务器信息
print(f"服务器: {response.headers.get('Server')}")  # 输出: 服务器: gunicorn

# 解析JSON响应
data = response.json()
print(f"请求来源IP: {data['origin']}")  # 输出: 请求来源IP: xxx.xxx.xxx.xxx（你的公网IP）
print(f"请求URL: {data['url']}")  # 输出: 请求URL: https://httpbin.org/get
```

### 示例2：带参数和请求头的GET请求（进阶）

```python
import requests

# 定义查询参数和请求头
params = {
    "q": "python 数据分析",
    "page": 1,
    "per_page": 10
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",  # 模拟浏览器
    "Accept-Language": "zh-CN,zh;q=0.9"
}

# 发送带参数的请求
url = "https://httpbin.org/get"
response = requests.get(url, params=params, headers=headers, timeout=10)

# 验证参数是否正确编码
data = response.json()
print(f"实际请求的URL: {data['url']}")
# 输出: 实际请求的URL: https://httpbin.org/get?q=python+%E6%95%B0%E6%8D%AE%E5%88%86%E6%9E%90&page=1&per_page=10
# 注意中文被URL编码为%E6%95%B0%E6%8D%AE%E5%88%86%E6%9E%90

print(f"请求头User-Agent: {data['headers']['User-Agent']}")
# 输出: 请求头User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

### 示例3：POST请求提交JSON数据（实战）

```python
import requests
import json

# 模拟向API提交数据
url = "https://httpbin.org/post"

# 准备要提交的数据（字典）
payload = {
    "name": "张三",
    "age": 28,
    "skills": ["Python", "SQL", "Excel"]
}

# 方式一：使用json参数（自动序列化并设置Content-Type）
response1 = requests.post(url, json=payload, timeout=10)
data1 = response1.json()
print(f"方式一 - 服务器收到的JSON: {data1['json']}")
# 输出: 方式一 - 服务器收到的JSON: {'name': '张三', 'age': 28, 'skills': ['Python', 'SQL', 'Excel']}

# 方式二：使用data参数手动序列化
headers = {"Content-Type": "application/json"}
response2 = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
data2 = response2.json()
print(f"方式二 - 服务器收到的JSON: {data2['json']}")
# 输出: 方式二 - 服务器收到的JSON: {'name': '张三', 'age': 28, 'skills': ['Python', 'SQL', 'Excel']}

# 验证两种方式的Content-Type
print(f"方式一 Content-Type: {response1.request.headers['Content-Type']}")
# 输出: 方式一 Content-Type: application/json
print(f"方式二 Content-Type: {response2.request.headers['Content-Type']}")
# 输出: 方式二 Content-Type: application/json
```

## 4. 常见错误

### 错误1：忘记处理超时导致程序卡死

```python
# 错误写法：没有设置timeout，如果服务器无响应，程序会一直挂起
import requests
response = requests.get("https://example.com/slow-api")  # 可能卡住几分钟

# 正确写法：始终设置timeout
import requests
try:
    response = requests.get("https://example.com/slow-api", timeout=(3, 5))  # (连接超时, 读取超时)
except requests.exceptions.Timeout:
    print("请求超时，请检查网络或服务器状态")
```

### 错误2：忽略状态码直接解析内容

```python
# 错误写法：不检查状态码，直接解析JSON
import requests
response = requests.get("https://httpbin.org/status/404")  # 返回404
data = response.json()  # 会抛出json.decoder.JSONDecodeError

# 正确写法：先检查状态码
import requests
response = requests.get("https://httpbin.org/status/404")
if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"请求失败，状态码: {response.status_code}")
    # 输出: 请求失败，状态码: 404
```

### 错误3：被反爬机制拦截（缺少User-Agent）

```python
# 错误写法：使用默认的User-Agent（python-requests/x.x.x），很多网站会拒绝
import requests
response = requests.get("https://httpbin.org/headers")
print(response.json()['headers'].get('User-Agent'))
# 输出: python-requests/2.31.0  <- 容易被识别为爬虫

# 正确写法：设置浏览器User-Agent
import requests
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
response = requests.get("https://httpbin.org/headers", headers=headers)
print(response.json()['headers'].get('User-Agent'))
# 输出: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...
```

## 5. 练习

### 练习1：获取并解析公开API数据

**题目**：使用`https://api.github.com/users/{username}`这个GitHub公开API，编写代码完成以下任务：
1. 获取用户名为`octocat`的用户信息
2. 检查请求是否成功，如果成功则提取并打印用户的`public_repos`（公开仓库数）和`followers`（粉丝数）
3. 如果请求失败（如用户不存在），打印友好的错误信息

**答案提示**：
```python
import requests

username = "octocat"
url = f"https://api.github.com/users/{username}"
response = requests.get(url, timeout=10)

if response.status_code == 200:
    user_data = response.json()
    print(f"用户: {user_data['login']}")
    print(f"公开仓库数: {user_data['public_repos']}")
    print(f"粉丝数: {user_data['followers']}")
elif response.status_code == 404:
    print(f"用户 {username} 不存在")
else:
    print(f"请求失败，状态码: {response.status_code}")
```

### 练习2：处理分页数据采集

**题目**：GitHub API对搜索结果进行分页，每页最多返回30条。请编写代码获取`https://api.github.com/search/repositories?q=language:python&sort=stars`（按星标排序的Python仓库）的前3页数据（共90条），并找出星标数最高的仓库名称。

**答案提示**：
```python
import requests

base_url = "https://api.github.com/search/repositories"
all_items = []

for page in range(1, 4):  # 获取前3页
    params = {
        "q": "language:python",
        "sort": "stars",
        "page": page,
        "per_page": 30
    }
    response = requests.get(base_url, params=params, timeout=10)
    if response.status_code == 200:
        data = response.json()
        all_items.extend(data['items'])
    else:
        print(f"第{page}页请求失败，状态码: {response.status_code}")

# 找出星标最高的仓库
top_repo = max(all_items, key=lambda x: x['stargazers_count'])
print(f"星标最高的Python仓库: {top_repo['full_name']}，星标数: {top_repo['stargazers_count']}")
# 注意：GitHub API有速率限制（未认证60次/小时），如果超限会返回403
```