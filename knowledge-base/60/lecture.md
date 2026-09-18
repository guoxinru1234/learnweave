# Flask/FastAPI部署数据分析API

> 模块：性能优化与部署 | 编号：第60讲 | Python数据分析实战

---

## 1. 概念

将数据分析结果通过 Web API 对外提供服务，是数据产品落地的关键一步。**Flask** 和 **FastAPI** 是 Python 生态中最主流的两个 Web 框架：Flask 轻量灵活、生态成熟，适合快速搭建原型；FastAPI 基于 ASGI 异步协议，自带数据校验和交互式文档，性能更高，适合生产环境。

**生活化类比**：把数据分析模型想象成一家餐厅的后厨，而 API 就是服务员。顾客（前端应用）不直接进后厨，而是通过服务员点餐（发送 HTTP 请求），服务员把菜单（API 文档）递给顾客，后厨做好菜（模型推理/数据计算）再由服务员端上桌（返回 JSON 响应）。Flask 像传统餐厅的人工服务员，FastAPI 则像智能机器人服务员——更快、更规范、自带菜单说明。

**适用场景**：实时预测、数据查询服务、模型上线、数据仪表盘后端、微服务架构中的数据处理节点。

---

## 2. 核心API与原理

| API/方法 | 签名 | 参数说明 | 返回值 | 说明 |
|---------|------|---------|--------|------|
| `Flask(__name__)` | `Flask(import_name)` | `import_name`：模块名，通常传 `__name__` | Flask 应用实例 | 创建 Flask 应用核心对象 |
| `@app.route(rule, methods)` | 装饰器 | `rule`：URL 路径字符串；`methods`：允许的 HTTP 方法列表 | 装饰后的视图函数 | 将 URL 绑定到处理函数 |
| `app.run(host, port, debug)` | `app.run(host=None, port=None, debug=None)` | `host`：监听地址，`0.0.0.0` 表示所有接口；`port`：端口号；`debug`：调试模式 | 阻塞运行服务器 | 启动开发服务器 |
| `FastAPI()` | `FastAPI(title=None, version=None)` | `title`：API 标题；`version`：版本号 | FastAPI 应用实例 | 创建 FastAPI 应用 |
| `@app.get(path)` / `@app.post(path)` | 装饰器 | `path`：URL 路径 | 装饰后的异步/同步函数 | 声明 GET/POST 端点 |
| `uvicorn.run(app, host, port)` | `uvicorn.run(app, host='127.0.0.1', port=8000)` | `app`：ASGI 应用；`host`/`port`：监听地址和端口 | 阻塞运行 ASGI 服务器 | 启动 FastAPI 应用 |

---

## 3. 代码示例

### 示例 1：Flask 基础数据分析 API（简单）

```python
# flask_basic_api.py
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np

app = Flask(__name__)

# 模拟一份销售数据
sales_data = pd.DataFrame({
    'product': ['A', 'B', 'C', 'D'],
    'price': [100, 200, 150, 300],
    'quantity': [5, 3, 8, 2]
})

@app.route('/api/summary', methods=['GET'])
def get_summary():
    """返回销售数据的统计摘要"""
    summary = {
        'total_revenue': float((sales_data['price'] * sales_data['quantity']).sum()),
        'avg_price': float(sales_data['price'].mean()),
        'max_quantity': int(sales_data['quantity'].max()),
        'product_count': int(len(sales_data))
    }
    return jsonify(summary)

@app.route('/api/product/<name>', methods=['GET'])
def get_product(name):
    """按产品名查询"""
    result = sales_data[sales_data['product'] == name.upper()]
    if result.empty:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(result.to_dict(orient='records')[0])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# 输出（访问 http://127.0.0.1:5000/api/summary）：
# {"avg_price":187.5,"max_quantity":8,"product_count":4,"total_revenue":2600.0}
```

### 示例 2：FastAPI 带数据校验的预测 API（进阶）

```python
# fastapi_ml_api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import uvicorn

app = FastAPI(title="房价预测 API", version="1.0.0")

# 模拟训练好的模型（实际应用中用 joblib.load 加载）
class DummyModel:
    def predict(self, X):
        return X @ np.array([3.5, -1.2, 0.8]) + 10

model = DummyModel()

class HouseFeatures(BaseModel):
    """请求体数据模型，自动进行类型校验"""
    area: float       # 面积（平方米）
    age: int          # 房龄（年）
    rooms: int        # 房间数

class PredictionResponse(BaseModel):
    """响应数据模型"""
    predicted_price: float
    currency: str = "万元"

@app.post("/api/predict", response_model=PredictionResponse)
async def predict_price(features: HouseFeatures):
    """
    房价预测接口
    请求体示例: {"area": 120.5, "age": 5, "rooms": 3}
    """
    try:
        X = np.array([[features.area, features.age, features.rooms]])
        price = float(model.predict(X)[0])
        return PredictionResponse(predicted_price=round(price, 2))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预测失败: {str(e)}")

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)

# 测试命令（终端执行）：
# curl -X POST http://127.0.0.1:8000/api/predict \
#   -H "Content-Type: application/json" \
#   -d '{"area": 120.5, "age": 5, "rooms": 3}'
# 输出: {"predicted_price": 427.35, "currency": "万元"}
```

### 示例 3：Flask 上传 CSV 并返回分析结果（综合）

```python
# flask_upload_analysis.py
from flask import Flask, request, jsonify
import pandas as pd
import io

app = Flask(__name__)

@app.route('/api/analyze', methods=['POST'])
def analyze_csv():
    """
    接收上传的 CSV 文件，返回描述性统计
    使用 Postman 或 curl -F "file=@data.csv" 测试
    """
    if 'file' not in request.files:
        return jsonify({'error': '未找到文件字段，请使用 file 字段上传'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名不能为空'}), 400
    
    try:
        # 读取上传的 CSV 到 DataFrame
        df = pd.read_csv(io.BytesIO(file.read()))
        
        # 只选择数值列进行分析
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if not numeric_cols:
            return jsonify({'error': 'CSV 中没有数值列'}), 400
        
        # 生成描述性统计
        stats = df[numeric_cols].describe().to_dict()
        
        # 转换为可 JSON 序列化的格式
        clean_stats = {}
        for col, metrics in stats.items():
            clean_stats[col] = {k: (None if pd.isna(v) else float(v)) 
                               for k, v in metrics.items()}
        
        return jsonify({
            'filename': file.filename,
            'rows': len(df),
            'numeric_columns': numeric_cols,
            'statistics': clean_stats
        })
    
    except Exception as e:
        return jsonify({'error': f'文件解析失败: {str(e)}'}), 400

if __name__ == '__main__':
    app.run(port=5001, debug=True)

# 测试命令：
# curl -F "file=@sales.csv" http://127.0.0.1:5001/api/analyze
# 输出示例: {"filename":"sales.csv","rows":100,"numeric_columns":["price","quantity"],"statistics":{...}}
```

---

## 4. 常见错误

### 错误 1：返回 NumPy 类型导致 JSON 序列化失败

**错误原因**：`jsonify` 无法直接序列化 `numpy.int64`、`numpy.float32` 等类型。

```python
# 错误写法
@app.route('/api/mean')
def get_mean():
    arr = np.array([1, 2, 3])
    return jsonify({'mean': arr.mean()})  # TypeError: Object of type float64 is not JSON serializable
```

**正确写法**：显式转换类型。

```python
@app.route('/api/mean')
def get_mean():
    arr = np.array([1, 2, 3])
    return jsonify({'mean': float(arr.mean())})  # 强制转为 Python 原生 float
```

### 错误 2：忘记处理 CORS 导致前端无法访问

**错误原因**：浏览器跨域安全策略阻止前端 JavaScript 调用 API。

```python
# 错误写法：未处理跨域
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/api/data')
def get_data():
    return jsonify({'data': [1, 2, 3]})
# 前端 fetch 调用会报 CORS 错误
```

**正确写法**：使用 `flask-cors` 扩展。

```python
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许所有域名跨域访问

@app.route('/api/data')
def get_data():
    return jsonify({'data': [1, 2, 3]})
```

### 错误 3：在请求处理中加载大模型导致超时

**错误原因**：每次请求都重新加载模型文件，耗时且浪费资源。

```python
# 错误写法：每次请求都加载模型
from flask import Flask, request, jsonify
import joblib

app = Flask(__name__)

@app.route('/api/predict', methods=['POST'])
def predict():
    model = joblib.load('model.pkl')  # 每次请求都加载，极慢！
    data = request.get_json()
    result = model.predict([data['features']])
    return jsonify({'result': result.tolist()})
```

**正确写法**：模块加载时加载一次，全局复用。

```python
from flask import Flask, request, jsonify
import joblib

app = Flask(__name__)
model = joblib.load('model.pkl')  # 应用启动时加载一次

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.get_json()
    result = model.predict([data['features']])
    return jsonify({'result': result.tolist()})
```

---

## 5. 练习

### 练习 1：实现一个带缓存的数据分析 API

**题目**：使用 Flask 实现一个 `/api/statistics` 接口，接收一个数据集 ID，返回该数据集的均值、中位数、标准差。要求使用 `functools.lru_cache` 对计算结果进行缓存（假设数据集不经常变化），并说明缓存对性能的提升。

**答案提示**：

```python
from functools import lru_cache
import pandas as pd

@lru_cache(maxsize=32)
def compute_stats(dataset_id):
    """缓存计算结果，避免重复计算"""
    df = pd.read_csv(f'data_{dataset_id}.csv')
    return {
        'mean': float(df.mean().mean()),
        'median': float(df.median().median()),
        'std': float(df.std().mean())
    }

@app.route('/api/statistics/<dataset_id>')
def get_statistics(dataset_id):
    return jsonify(compute_stats(dataset_id))
```

### 练习 2：FastAPI 异步并发优化

**题目**：某数据分析接口需要同时查询多个外部数据源（模拟为 sleep 延迟），请用 FastAPI 的异步特性优化，将串行 3 秒的响应时间降低到约 1 秒。要求使用 `asyncio.gather` 实现并发请求，并解释异步与同步的性能差异。

**答案提示**：

```python
import asyncio
from fastapi import FastAPI
import time

app = FastAPI()

async def fetch_data(source_id: int):
    """模拟异步请求外部数据源"""
    await asyncio.sleep(1)  # 模拟网络延迟
    return {"source": source_id, "data": source_id * 10}

@app.get("/api/async-data")
async def get_async_data():
    """并发获取 3 个数据源，总耗时约 1 秒"""
    results = await asyncio.gather(
        fetch_data(1), fetch_data(2), fetch_data(3)
    )
    return {"results": results}

# 对比：如果使用同步 def 和 time.sleep(1)，串行执行需 3 秒
# 异步版本利用 await 让出控制权，3 个请求并行执行，仅需 1 秒
```

---

> **延伸阅读**：官方文档 — Flask: https://flask.palletsprojects.com/ | FastAPI: https://fastapi.tiangolo.com/ | Uvicorn: https://www.uvicorn.org/