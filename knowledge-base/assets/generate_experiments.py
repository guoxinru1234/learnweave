import json
from pathlib import Path

# ========== 实验数据 ==========
experiments_data = [
    {
        "id": "rdd-programming-lab",
        "title": "RDD 编程实战",
        "category": "case",
        "source_path": "实验手册/案例/RDD编程实战.docx",
        "suffix": "docx",
        "topics": ["Scala", "编程实践", "RDD", "YARN", "Local"],
        "lecture_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    },
    {
        "id": "scala-programming-lab",
        "title": "Scala 编程实践",
        "category": "case",
        "source_path": "实验手册/案例/Scala编程.pdf",
        "suffix": "pdf",
        "topics": ["Scala", "函数式编程", "习题"],
        "lecture_ids": [1, 2, 3, 4, 5, 6]
    },
    {
        "id": "spark-sql-basic-lab",
        "title": "SparkSQL 初级实战",
        "category": "case",
        "source_path": "实验手册/案例/SparkSQL初级实战.docx",
        "suffix": "docx",
        "topics": ["Scala", "SparkSQL", "DataFrame", "Local", "作业"],
        "lecture_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 17, 18, 19, 20]
    },
    {
        "id": "spark-streaming-basic-lab",
        "title": "Spark 流处理初级实战",
        "category": "case",
        "source_path": "实验手册/案例/Spark流处理初级实战.docx",
        "suffix": "docx",
        "topics": ["Scala", "RDD", "Local", "流处理", "作业"],
        "lecture_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    },
]

# ========== 生成 chunks.jsonl 的内容（完整正文） ==========
chunks_data = []

for exp in experiments_data:
    exp_id = exp["id"]
    title = exp["title"]

    # 根据不同的实验生成不同的内容
    if exp_id == "rdd-programming-lab":
        content = """
<h2>🎯 实验目的</h2>
<p>通过本实验，掌握 Spark RDD 的核心操作，包括：</p>
<ul>
  <li>RDD 的创建方式（parallelize、textFile）</li>
  <li>Transformation 操作（map、filter、flatMap、reduceByKey）</li>
  <li>Action 操作（collect、count、take）</li>
  <li>理解 Spark 的惰性求值机制</li>
</ul>

<h2>📋 实验环境</h2>
<ul>
  <li>Spark 3.2+</li>
  <li>Scala 2.12+</li>
  <li>IntelliJ IDEA 或 VS Code</li>
</ul>

<h2>📝 实验步骤</h2>

<h3>步骤1：启动 Spark Shell</h3>
<pre><code>spark-shell</code></pre>

<h3>步骤2：创建 RDD</h3>
<pre><code>val rdd = sc.parallelize(Array(1, 2, 3, 4, 5, 6, 7, 8, 9, 10))</code></pre>

<h3>步骤3：执行 Transformation 操作</h3>
<pre><code>// map - 每个元素乘以2
val doubled = rdd.map(_ * 2)
doubled.collect()

// filter - 筛选偶数
val evens = rdd.filter(_ % 2 == 0)
evens.collect()</code></pre>

<h2>实验任务</h2>
<ol>
  <li>创建一个包含 1 到 100 的 RDD，使用 map 计算每个数的平方</li>
  <li>筛选出平方数中大于 1000 的所有数</li>
  <li>使用 reduceByKey 统计文本文件中每个单词的出现次数</li>
</ol>

<h2>💡 思考题</h2>
<ol>
  <li>map 和 flatMap 的区别是什么？</li>
  <li>reduceByKey 和 groupByKey 有什么区别？</li>
</ol>
"""
    elif exp_id == "scala-programming-lab":
        content = """
<h2>🎯 实验目的</h2>
<p>掌握 Scala 基础语法和函数式编程特性。</p>

<h2>实验任务</h2>
<ol>
  <li>实现一个函数，计算斐波那契数列第 n 项</li>
  <li>使用 map 和 reduce 计算列表中所有奇数的乘积</li>
  <li>实现一个模式匹配，判断输入的字符串类型</li>
</ol>
"""
    elif exp_id == "spark-sql-basic-lab":
        content = """
<h2>🎯 实验目的</h2>
<p>掌握 Spark SQL 和 DataFrame 的核心操作。</p>

<h2>实验任务</h2>
<ol>
  <li>创建一个包含 10 条用户数据的 DataFrame</li>
  <li>查询年龄大于 25 的用户</li>
  <li>按年龄分组统计用户数量</li>
</ol>
"""
    else:
        content = """
<h2>🎯 实验目的</h2>
<p>掌握 Spark Structured Streaming 的基本使用。</p>

<h2>实验任务</h2>
<ol>
  <li>使用 socket 源创建流式输入</li>
  <li>实现实时词频统计</li>
  <li>将结果输出到控制台</li>
</ol>
"""

    chunk = {
        "id": f"{exp_id}-chunk-0",
        "asset_id": exp_id,
        "chunk_index": 0,
        "title": f"{title} 实验手册",
        "text": content
    }
    chunks_data.append(chunk)

# 写入 chunks.jsonl
with open("chunks.jsonl", "w", encoding="utf-8") as f:
    for chunk in chunks_data:
        f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

print(f"✅ 已重新生成 chunks.jsonl（{len(chunks_data)} 个 chunk）")
print("🎉 请重启后端服务！")