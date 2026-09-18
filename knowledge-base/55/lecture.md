# 数据清洗存储与可视化

> 模块：实战：网络数据采集 | 编号：第55讲 | Python数据分析实战

---

## 1. 概念

数据清洗、存储与可视化是网络数据采集流程的"最后一公里"。当我们通过爬虫（如 Requests、Scrapy）获取到原始网页数据后，这些数据往往包含 HTML 标签、缺失值、重复记录、格式不一致等问题，无法直接用于分析。**数据清洗（Data Cleaning）** 就是通过检测和修正数据中的错误、不完整、不一致之处，将"脏数据"转化为整洁、规范、可分析的"干净数据"的过程。**数据存储（Data Storage）** 则是将清洗后的结构化数据持久化到文件（如 CSV、Excel）或数据库（如 SQLite）中，以便后续读取和复用。**数据可视化（Data Visualization）** 是利用图表将数据中的模式、趋势和异常直观呈现，辅助决策和洞察。

**生活化类比**：这就像厨师收到一批刚从菜市场买回的蔬菜（原始数据）——先要摘掉烂叶、洗去泥土（清洗），再按类别分装进冰箱（存储），最后摆盘上桌让食客一眼看出菜品特色（可视化）。没有清洗的菜不能直接下锅，没有存储的菜下次还得重新买，没有摆盘的菜则难以吸引食客。

---

## 2. 核心API与原理

| API | 签名 | 参数说明 | 返回值 | 核心原理 |
|-----|------|----------|--------|----------|
| `DataFrame.dropna()` | `df.dropna(axis=0, how='any', thresh=None, subset=None, inplace=False)` | `axis`: 0按行删，1按列删；`how`: 'any'任一缺失即删，'all'全部缺失才删；`thresh`: 每行/列至少需保留的非空值个数；`subset`: 指定列名列表；`inplace`: 是否原地修改 | 删除缺失值后的新 DataFrame（若 `inplace=True` 返回 None） | 基于布尔掩码筛选，将满足缺失条件的行/列剔除 |
| `DataFrame.fillna()` | `df.fillna(value=None, method=None, axis=None, inplace=False, limit=None)` | `value`: 填充值（标量或字典）；`method`: 'ffill'前向填充，'bfill'后向填充；`limit`: 最大连续填充次数 | 填充后的新 DataFrame | 用指定值或相邻值替换 NaN 位置 |
| `DataFrame.to_csv()` | `df.to_csv(path_or_buf=None, sep=',', index=True, encoding=None, header=True)` | `path_or_buf`: 文件路径；`sep`: 分隔符；`index`: 是否写入行索引；`encoding`: 编码（如'utf-8-sig'） | 无（写入文件）或返回字符串（若未指定路径） | 将 DataFrame 按 CSV 格式序列化写入 |
| `pd.read_csv()` | `pd.read_csv(filepath_or_buffer, sep=',', encoding=None, parse_dates=False, index_col=None)` | `filepath_or_buffer`: 文件路径或 URL；`parse_dates`: 是否解析日期列；`index_col`: 指定索引列 | 返回 DataFrame | 按分隔符解析文本，自动推断数据类型 |
| `df.plot()` | `df.plot(kind='line', x=None, y=None, figsize=None, title=None)` | `kind`: 图表类型（'line'/'bar'/'hist'/'scatter'等）；`x`/`y`: 指定列名；`figsize`: 画布尺寸 | 返回 `matplotlib.axes.Axes` 对象 | 基于 Matplotlib 的面向对象接口封装，自动适配 Pandas 数据类型 |

---

## 3. 代码示例

### 示例1：基础清洗与CSV存储（入门）

```python
import pandas as pd

# 模拟爬虫采集到的原始数据（含缺失值和重复项）
raw_data = {
    '书名': ['Python编程', '数据分析实战', None, 'Python编程', '机器学习'],
    '价格': [59.5, 79.0, 45.0, 59.5, None],
    '销量': [1200, 800, 500, 1200, 300]
}
df = pd.DataFrame(raw_data)
print("原始数据：")
print(df)
# 输出：
#          书名   价格     销量
# 0  Python编程  59.5  1200.0
# 1  数据分析实战  79.0   800.0
# 2        None  45.0   500.0
# 3  Python编程  59.5  1200.0
# 4     机器学习   NaN   300.0

# 步骤1：删除"书名"全为空的记录
df_clean = df.dropna(subset=['书名'])
# 步骤2：用均值填充"价格"缺失值
df_clean['价格'] = df_clean['价格'].fillna(df_clean['价格'].mean())
# 步骤3：去除完全重复的行
df_clean = df_clean.drop_duplicates()

print("\n清洗后数据：")
print(df_clean)
# 输出：
#          书名   价格     销量
# 0  Python编程  59.5  1200.0
# 1  数据分析实战  79.0   800.0
# 2     机器学习  69.25  300.0

# 存储到CSV（utf-8-sig编码兼容Excel）
df_clean.to_csv('books_clean.csv', index=False, encoding='utf-8-sig')
print("\n已保存至 books_clean.csv")
```

### 示例2：从CSV读取并可视化（进阶）

```python
import pandas as pd
import matplotlib.pyplot as plt

# 设置中文字体（Windows用SimHei，macOS用Arial Unicode MS）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 读取上一步保存的CSV
df = pd.read_csv('books_clean.csv', encoding='utf-8-sig')
print("读取结果：")
print(df)

# 创建柱状图展示各书籍销量
df.plot(kind='bar', x='书名', y='销量', figsize=(8, 5),
        title='各书籍销量对比', color='skyblue')
plt.xlabel('书名')
plt.ylabel('销量（本）')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('sales_bar.png', dpi=150)
plt.show()
# 输出：生成柱状图，显示三本书的销量对比，Python编程最高（1200），机器学习最低（300）
```

### 示例3：完整数据管道——清洗、SQLite存储与多图可视化（综合）

```python
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

# 模拟多日采集的电商数据
data = {
    '日期': ['2024-01-01', '2024-01-01', '2024-01-02', '2024-01-02', '2024-01-03'],
    '商品': ['手机', '耳机', '手机', '耳机', '手机'],
    '价格': [3999, 299, 3999, None, 4299],  # 含缺失值
    '销量': [5, 20, 7, 15, 6]
}
df = pd.DataFrame(data)
df['日期'] = pd.to_datetime(df['日期'])  # 转为日期类型

# 清洗：删除价格缺失的记录
df_clean = df.dropna(subset=['价格'])
# 清洗：删除重复记录（同日期同商品）
df_clean = df_clean.drop_duplicates(subset=['日期', '商品'])

# 存储到SQLite数据库
conn = sqlite3.connect('ecommerce.db')
df_clean.to_sql('sales', conn, if_exists='replace', index=False)
print("数据已存入SQLite数据库，共", len(df_clean), "条记录")

# 从数据库读回
df_db = pd.read_sql_query("SELECT * FROM sales", conn)
conn.close()

# 可视化1：时间序列折线图（手机价格变化）
phone_data = df_db[df_db['商品'] == '手机']
plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.plot(phone_data['日期'], phone_data['价格'], marker='o', linestyle='-')
plt.title('手机价格趋势')
plt.xlabel('日期')
plt.ylabel('价格（元）')

# 可视化2：饼图展示各商品销量占比
sales_by_product = df_db.groupby('商品')['销量'].sum()
plt.subplot(1, 2, 2)
plt.pie(sales_by_product, labels=sales_by_product.index, autopct='%1.1f%%')
plt.title('各商品销量占比')

plt.tight_layout()
plt.show()
# 输出：左侧折线图显示手机价格从3999涨至4299；右侧饼图显示耳机销量占比约74%，手机约26%
```

---

## 4. 常见错误

### 错误1：`inplace=True` 后忘记重新赋值导致数据未改变

```python
# 错误写法
df = pd.DataFrame({'A': [1, None, 3]})
df.dropna(inplace=False)  # 返回新对象但未接收
print(df)  # 仍然包含 NaN，数据未变

# 正确写法（二选一）
df.dropna(inplace=True)   # 方式1：原地修改
# 或
df = df.dropna()          # 方式2：重新赋值
```

**原因**：Pandas 中多数方法默认返回新对象，`inplace=False` 时原 DataFrame 不变。新手常忽略返回值。

### 错误2：CSV 中文乱码

```python
# 错误写法
df.to_csv('data.csv')  # 默认编码为utf-8，Excel打开会乱码

# 正确写法
df.to_csv('data.csv', encoding='utf-8-sig')  # 添加BOM头，兼容Excel
```

**原因**：Excel 默认使用 GBK 编码解析 CSV，而 Pandas 默认写入 UTF-8 无 BOM。`utf-8-sig` 编码会在文件开头添加 BOM 标记，让 Excel 正确识别。

### 错误3：`fillna` 直接修改原列时出现 SettingWithCopyWarning

```python
# 错误写法
df_sub = df[df['价格'] > 100]  # 视图而非副本
df_sub['价格'] = df_sub['价格'].fillna(0)  # 触发警告且可能不生效

# 正确写法
df_sub = df[df['价格'] > 100].copy()  # 显式创建副本
df_sub.loc[:, '价格'] = df_sub['价格'].fillna(0)
```

**原因**：布尔索引返回的是原 DataFrame 的视图（View），对其修改会引发 `SettingWithCopyWarning`。使用 `.copy()` 创建独立副本后再操作。

---

## 5. 练习

### 练习1：清洗并合并多源数据

你从两个不同网站采集了同一批商品的评分数据，分别存储在 `scores_a.csv` 和 `scores_b.csv` 中（可自行构造数据）。两个文件都有"商品名"和"评分"列，但存在以下问题：
- A 文件有 3 条记录评分缺失
- B 文件有 2 条重复记录
- 同一商品在两个文件中的评分可能不同（以更高分为准）

请编写代码完成：读取两个 CSV → 分别清洗（填充缺失值为该文件均值、去重）→ 按商品名合并 → 取每件商品的最高评分 → 保存为 `final_scores.csv` 并绘制评分分布直方图。

**答案提示**：使用 `pd.read_csv()` 读取，`fillna(df['评分'].mean())` 填充缺失，`drop_duplicates(subset=['商品名'])` 去重，`pd.concat()` 合并后用 `groupby('商品名')['评分'].max()` 取最高分，最后用 `df.plot(kind='hist')` 画直方图。

### 练习2：SQLite 存储与增量更新

设计一个简单的爬虫数据管理系统：每天爬取天气数据（城市、日期、最高温、最低温）存入 SQLite。要求：
1. 编写函数 `save_weather(data_list)`，将每日数据存入 `weather.db` 的 `daily` 表
2. 编写函数 `query_weather(city)`，返回指定城市所有记录
3. 实现"增量更新"逻辑：如果某城市某日的数据已存在，则更新温度，否则插入新记录

**答案提示**：使用 `sqlite3` 模块，建表时设置 `UNIQUE(city, date)` 约束；插入时使用 `INSERT OR REPLACE INTO` 或先 `SELECT` 判断再 `UPDATE`/`INSERT`；查询用 `WHERE city=?` 参数化查询防止 SQL 注入。测试时可用 `pd.DataFrame.to_sql()` 先初始化数据，再用原生 SQL 操作验证。