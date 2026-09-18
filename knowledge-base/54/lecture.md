# 反爬策略应对(UserAgent/IP池)

> 模块：实战：网络数据采集 | 编号：第54讲 | Python数据分析实战

---

## 1. 概念

**反爬策略应对**是指在网络数据采集过程中，通过技术手段规避目标网站对自动化请求的检测与限制，从而顺利完成数据获取的一系列方法。其中，**UserAgent轮换**和**IP代理池**是最基础、最常用的两种手段。

**UserAgent（用户代理）** 是HTTP请求头中的一个字段，用于标识客户端类型（如浏览器版本、操作系统等）。网站常通过检测同一UserAgent的请求频率来识别爬虫。**IP池**则是一组可用的代理IP地址，通过轮流切换IP来避免因同一IP请求过于频繁而被封禁。

**生活化类比**：这就像你去图书馆查阅资料——如果你每次都穿着同一件显眼的红衣服（固定UserAgent）坐在同一个位置（固定IP）连续借阅几百本书，管理员很快会注意到你并限制你的行为。而如果你每次换不同的衣服、坐在不同的位置，管理员就很难判断你是否在批量查阅。

**适用场景**：大规模数据采集、搜索引擎爬虫、电商价格监控、社交媒体数据分析等需要高频请求的场合。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 | 说明 |
|-----|------|----------|--------|------|
| `requests.get()` | `requests.get(url, params=None, headers=None, proxies=None, timeout=None)` | `url`: 请求地址；`headers`: 请求头字典；`proxies`: 代理字典；`timeout`: 超时时间(秒) | `Response` 对象 | 发送GET请求，支持自定义请求头和代理 |
| `fake_useragent.UserAgent()` | `UserAgent().random` | 无参数 | `str` | 随机生成一个真实的浏览器UserAgent字符串 |
| `requests.Session()` | `Session()` | 无参数 | `Session` 对象 | 维持会话，复用TCP连接，可批量设置headers |
| `random.choice()` | `random.choice(seq)` | `seq`: 非空序列（如列表） | 序列中的随机元素 | 从序列中随机选取一个元素 |
| `time.sleep()` | `time.sleep(seconds)` | `seconds`: 休眠秒数 | 无 | 暂停程序执行指定时间 |

**原理说明**：`fake_useragent`库内置了真实浏览器的UserAgent数据库，每次调用`.random`属性都会随机返回一个真实存在的浏览器标识。`requests`库的`proxies`参数接受一个字典，格式为`{"http": "http://ip:port", "https": "https://ip:port"}`，请求会通过该代理转发。`Session`对象可以保持Cookie等状态信息，同时可以统一设置headers。

---

## 3. 代码示例

### 示例1：基础UserAgent伪装（入门）

```python
import requests
from fake_useragent import UserAgent

# 创建UserAgent对象
ua = UserAgent()

# 生成一个随机的UserAgent
random_ua = ua.random
print(f"本次使用的UserAgent: {random_ua}")

# 构造请求头
headers = {
    'User-Agent': random_ua,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

# 发送请求
url = "https://httpbin.org/headers"  # 该网站会返回请求头信息
response = requests.get(url, headers=headers, timeout=5)

# 解析返回结果
import json
result = json.loads(response.text)
print(f"服务器接收到的User-Agent: {result['headers']['User-Agent']}")
print(f"请求头伪装成功: {result['headers']['User-Agent'] == random_ua}")

# 输出示例:
# 本次使用的UserAgent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...
# 服务器接收到的User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...
# 请求头伪装成功: True
```

### 示例2：UserAgent轮换 + 请求间隔（进阶）

```python
import requests
import random
import time
from fake_useragent import UserAgent

# 准备一个UserAgent池（也可以直接用fake_useragent动态生成）
ua = UserAgent()
ua_pool = [ua.chrome, ua.firefox, ua.safari, ua.random]  # 混合使用

# 目标URL（以httpbin为例，它会回显请求信息）
url = "https://httpbin.org/ip"

# 模拟连续采集5个页面
for i in range(5):
    # 随机选择一个UserAgent
    current_ua = random.choice(ua_pool)
    headers = {'User-Agent': current_ua}
    
    # 发送请求
    response = requests.get(url, headers=headers, timeout=5)
    print(f"第{i+1}次请求 | UA: {current_ua[:50]}... | 状态码: {response.status_code}")
    
    # 随机休眠1-3秒，模拟人类浏览行为
    sleep_time = random.uniform(1, 3)
    time.sleep(sleep_time)

# 输出示例:
# 第1次请求 | UA: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36... | 状态码: 200
# 第2次请求 | UA: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Gecko/20100101... | 状态码: 200
# 第3次请求 | UA: Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) ... | 状态码: 200
# 第4次请求 | UA: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36... | 状态码: 200
# 第5次请求 | UA: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36... | 状态码: 200
```

### 示例3：IP代理池 + Session复用（综合）

```python
import requests
import random
from fake_useragent import UserAgent

# 模拟一个IP代理池（实际使用中可从代理服务商API获取）
proxy_pool = [
    {"http": "http://123.45.67.89:8080", "https": "http://123.45.67.89:8080"},
    {"http": "http://98.76.54.32:3128", "https": "http://98.76.54.32:3128"},
    # 注意：以上为示例IP，实际使用时需替换为真实可用代理
]

# 创建Session对象，复用连接
session = requests.Session()
ua = UserAgent()

def fetch_with_proxy(url, max_retries=3):
    """带代理和UA伪装的请求函数"""
    for attempt in range(max_retries):
        # 随机选择代理和UA
        proxy = random.choice(proxy_pool)
        session.headers.update({'User-Agent': ua.random})
        
        try:
            response = session.get(url, proxies=proxy, timeout=10)
            if response.status_code == 200:
                return response
            else:
                print(f"尝试{attempt+1}失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"尝试{attempt+1}异常: {e}")
    
    return None

# 测试请求
url = "https://httpbin.org/ip"
result = fetch_with_proxy(url)

if result:
    print(f"请求成功，返回IP信息: {result.text}")
else:
    print("所有代理尝试均失败")

# 输出示例（代理可用时）:
# 请求成功，返回IP信息: {
#   "origin": "123.45.67.89"
# }
# 注：origin字段显示的是代理IP而非本机IP，说明代理生效
```

---

## 4. 常见错误

### 错误1：忘记设置超时时间导致程序卡死

```python
# 错误写法
import requests
response = requests.get("https://example.com")  # 如果网站无响应，程序会一直挂起

# 正确写法
import requests
try:
    response = requests.get("https://example.com", timeout=5)  # 5秒超时
except requests.exceptions.Timeout:
    print("请求超时，请检查网络或代理")
```

### 错误2：代理格式错误导致连接失败

```python
# 错误写法
proxies = {"http": "123.45.67.89:8080"}  # 缺少协议前缀
response = requests.get("https://httpbin.org/ip", proxies=proxies)

# 正确写法
proxies = {"http": "http://123.45.67.89:8080", "https": "http://123.45.67.89:8080"}
# 注意：https请求需要对应的https代理，且代理地址需带协议前缀
response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=5)
```

### 错误3：频繁使用同一个UserAgent和IP

```python
# 错误写法
import requests
headers = {'User-Agent': 'Mozilla/5.0'}  # 固定UA
for i in range(100):
    requests.get("https://example.com/page", headers=headers)  # 高频、固定UA、无间隔

# 正确写法
import requests, random, time
from fake_useragent import UserAgent

ua = UserAgent()
for i in range(100):
    headers = {'User-Agent': ua.random}  # 每次随机UA
    # 使用代理池轮换IP
    proxies = random.choice(proxy_pool)
    requests.get("https://example.com/page", headers=headers, proxies=proxies, timeout=5)
    time.sleep(random.uniform(1, 5))  # 随机间隔
```

---

## 5. 练习

### 练习1：实现一个带完整反爬策略的采集函数

**题目**：编写一个函数 `smart_fetch(url, max_retries=3)`，要求：
- 每次请求随机使用不同的UserAgent（来自fake_useragent）
- 使用Session保持会话
- 支持代理池轮换（代理列表自行定义）
- 请求失败时自动重试，最多重试`max_retries`次
- 每次请求间隔1-2秒

**答案提示**：
```python
def smart_fetch(url, max_retries=3):
    import requests, random, time
    from fake_useragent import UserAgent
    
    session = requests.Session()
    ua = UserAgent()
    proxy_pool = [...]  # 定义代理列表
    
    for i in range(max_retries):
        try:
            session.headers.update({'User-Agent': ua.random})
            proxies = random.choice(proxy_pool)
            resp = session.get(url, proxies=proxies, timeout=10)
            if resp.status_code == 200:
                return resp
        except:
            pass
        time.sleep(random.uniform(1, 2))
    return None
```

### 练习2：分析反爬检测机制

**题目**：访问 `https://httpbin.org/headers` 和 `https://httpbin.org/ip`，分别观察：
1. 不设置任何headers时，服务器能检测到哪些客户端信息？
2. 设置UserAgent后，`headers`接口返回的User-Agent字段有什么变化？
3. 思考：除了UserAgent和IP，网站还可能通过哪些字段识别爬虫？（提示：查看`Accept-Language`、`Accept-Encoding`等字段）

**答案提示**：
- 不设置headers时，`httpbin.org/headers`会显示`User-Agent: python-requests/2.x.x`，暴露了Python爬虫身份
- 设置UserAgent后，该字段变为伪造的浏览器标识
- 其他可检测字段包括：`Accept`（爬虫通常不会设置）、`Accept-Language`（爬虫通常是默认值）、`Referer`（爬虫通常为空）、请求频率、Cookie一致性等。完整模拟浏览器行为需要同时设置这些字段。