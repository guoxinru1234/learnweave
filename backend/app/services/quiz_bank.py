"""Curated quiz bank for Python Data Analysis curriculum."""
from __future__ import annotations
from copy import deepcopy
from typing import Any, Optional, Dict

Question = Dict[str, Any]

TOPIC_ALIASES = {
    "python": "Python 语言基础",
    "python基础": "Python 语言基础",
    "python 基础": "Python 语言基础",
    "numpy": "NumPy 数值计算",
    "numpy基础": "NumPy 数值计算",
    "数组": "NumPy 数值计算",
    "pandas": "Pandas 数据处理",
    "pandas基础": "Pandas 数据处理",
    "dataframe": "Pandas 数据处理",
    "series": "Pandas 数据处理",
    "数据清洗": "数据清洗与预处理",
    "清洗": "数据清洗与预处理",
    "缺失值": "数据清洗与预处理",
    "可视化": "数据可视化",
    "matplotlib": "数据可视化",
    "seaborn": "数据可视化",
    "机器学习": "机器学习基础",
    "sklearn": "机器学习基础",
    "scikit-learn": "机器学习基础",
    "综合": "综合练习",
}

COURSE_QUIZ_BANK: dict[str, list[Question]] = {
    "Python 语言基础": [
        {
            "difficulty": "basic", "lecture": "第1-2讲",
            "q": "Python 中用于定义不可变序列的数据类型是？",
            "options": ["list", "tuple", "dict", "set"],
            "answer": 1,
            "explain": "tuple 是不可变序列，创建后不能修改元素。list 是可变的。",
        },
        {
            "difficulty": "basic", "lecture": "第1-2讲",
            "q": "下列哪个是 Python 合法的变量名？",
            "options": ["2name", "_count", "class", "my-var"],
            "answer": 1,
            "explain": "变量名可以以下划线开头，但不能以数字开头，不能是关键字，不能包含连字符。",
        },
        {
            "difficulty": "basic", "lecture": "第3讲",
            "q": "`for i in range(5):` 循环执行几次？",
            "options": ["4次", "5次", "6次", "无限次"],
            "answer": 1,
            "explain": "range(5) 生成 0,1,2,3,4，共5次迭代。",
        },
        {
            "difficulty": "intermediate", "lecture": "第4讲",
            "q": "Python 函数中 `*args` 的作用是？",
            "options": ["接收关键字参数", "接收任意数量的位置参数", "定义默认参数", "装饰函数"],
            "answer": 1,
            "explain": "*args 将多个位置参数收集为一个元组。",
        },
    ],
    "NumPy 数值计算": [
        {
            "difficulty": "basic", "lecture": "第5讲",
            "q": "创建全零数组的正确方式是？",
            "options": ["np.array([])", "np.zeros((3,4))", "np.empty(3,4)", "np.create(0,3,4)"],
            "answer": 1,
            "explain": "np.zeros((3,4)) 创建一个3行4列的全零数组。",
        },
        {
            "difficulty": "basic", "lecture": "第5讲",
            "q": "NumPy 数组与 Python 列表的主要区别是？",
            "options": ["NumPy 数组不能索引", "NumPy 数组元素类型必须相同", "NumPy 数组不支持切片", "NumPy 数组只能一维"],
            "answer": 1,
            "explain": "NumPy 数组要求所有元素类型相同，这使得向量化运算成为可能，比 Python 列表快 50 倍以上。",
        },
        {
            "difficulty": "intermediate", "lecture": "第6讲",
            "q": "NumPy 广播机制的作用是？",
            "options": ["播放音频", "使不同形状的数组能进行算术运算", "将数组发送到网络", "压缩数组存储"],
            "answer": 1,
            "explain": "广播允许不同形状的数组在算术运算中自动扩展维度，无需显式复制数据。",
        },
    ],
    "Pandas 数据处理": [
        {
            "difficulty": "basic", "lecture": "第9讲",
            "q": "Pandas 中读取 CSV 文件使用哪个函数？",
            "options": ["pd.load_csv()", "pd.read_csv()", "pd.import_csv()", "pd.open_csv()"],
            "answer": 1,
            "explain": "pd.read_csv('file.csv') 是 Pandas 读取 CSV 文件的标准方法。",
        },
        {
            "difficulty": "basic", "lecture": "第9讲",
            "q": "`df.head()` 的作用是？",
            "options": ["删除第一行", "返回前5行数据", "排序数据", "查看列名"],
            "answer": 1,
            "explain": "df.head() 默认返回 DataFrame 的前5行，用于快速预览数据。",
        },
        {
            "difficulty": "intermediate", "lecture": "第10讲",
            "q": "`df.loc` 和 `df.iloc` 的区别是什么？",
            "options": ["没有区别", "loc 用标签索引，iloc 用位置索引", "loc 只能用于行", "iloc 只能用于列"],
            "answer": 1,
            "explain": "loc 基于标签(label)选择，iloc 基于整数位置(integer position)选择。",
        },
        {
            "difficulty": "intermediate", "lecture": "第12讲",
            "q": "`df.groupby('col').mean()` 的作用是？",
            "options": ["按 col 列排序", "按 col 列分组并计算每组的平均值", "删除 col 列", "计算 col 列的平均值"],
            "answer": 1,
            "explain": "groupby 将数据按指定列分组，然后对每组应用聚合函数（如 mean）。",
        },
    ],
    "数据清洗与预处理": [
        {
            "difficulty": "basic", "lecture": "第13讲",
            "q": "Pandas 中检测缺失值的方法是？",
            "options": ["df.find_na()", "df.isna()", "df.missing()", "df.null()"],
            "answer": 1,
            "explain": "df.isna() 返回与 df 同形状的布尔 DataFrame，标记缺失值位置。",
        },
        {
            "difficulty": "basic", "lecture": "第13讲",
            "q": "`df.dropna()` 的作用是？",
            "options": ["标记缺失值", "删除包含缺失值的行或列", "用0填充缺失值", "统计缺失值数量"],
            "answer": 1,
            "explain": "dropna() 删除包含 NaN 的行（默认 axis=0）或列（axis=1）。",
        },
        {
            "difficulty": "intermediate", "lecture": "第14讲",
            "q": "检测异常值的常用统计方法是？",
            "options": ["只看最大值", "3σ原则或 IQR（四分位距）", "删除所有数据", "只保留重复值"],
            "answer": 1,
            "explain": "3σ原则（均值±3倍标准差）和 IQR（Q3+1.5*IQR）是常用的异常值检测方法。",
        },
    ],
    "数据可视化": [
        {
            "difficulty": "basic", "lecture": "第17讲",
            "q": "Matplotlib 中绘制折线图的基本函数是？",
            "options": ["plt.bar()", "plt.plot()", "plt.scatter()", "plt.hist()"],
            "answer": 1,
            "explain": "plt.plot() 用于绘制折线图，是 Matplotlib 最基础的绘图函数。",
        },
        {
            "difficulty": "basic", "lecture": "第17讲",
            "q": "`plt.figure()` 的作用是？",
            "options": ["关闭图表", "创建一个新的图形窗口", "保存图表", "显示图表"],
            "answer": 1,
            "explain": "plt.figure() 创建一个新的 Figure 对象，可以设置大小、DPI 等参数。",
        },
    ],
    "机器学习基础": [
        {
            "difficulty": "basic", "lecture": "第23讲",
            "q": "Scikit-learn 中训练模型的通用方法是？",
            "options": ["model.run()", "model.fit()", "model.train()", "model.learn()"],
            "answer": 1,
            "explain": "绝大多数 sklearn 模型使用 fit(X, y) 方法进行训练。",
        },
        {
            "difficulty": "intermediate", "lecture": "第23讲",
            "q": "`train_test_split` 的作用是？",
            "options": ["合并数据集", "将数据分为训练集和测试集", "标准化数据", "填充缺失值"],
            "answer": 1,
            "explain": "train_test_split 将数据集随机划分为训练集和测试集，用于评估模型泛化能力。",
        },
    ],
    "综合练习": [
        {
            "difficulty": "intermediate", "lecture": "综合",
            "q": "数据分析的标准流程（ETL）中，T 代表什么？",
            "options": ["Test 测试", "Transform 转换", "Train 训练", "Time 时间"],
            "answer": 1,
            "explain": "ETL = Extract(提取) + Transform(转换) + Load(加载)，T 是数据转换/清洗步骤。",
        },
    ],
}

DIFFICULTY_FALLBACK_ORDER = {
    "basic": ["basic", "intermediate", "advanced"],
    "intermediate": ["intermediate", "basic", "advanced"],
    "advanced": ["advanced", "intermediate", "basic"],
}


def normalize_topic(topic: str) -> str:
    normalized = " ".join(topic.strip().lower().split())
    return TOPIC_ALIASES.get(normalized, topic.strip())


def _topic_pool(canonical_topic: str, lecture: Optional[str] = None) -> list[Question]:
    if canonical_topic == "综合练习":
        all_questions = [
            {**question, "topic": topic_name}
            for topic_name, questions in COURSE_QUIZ_BANK.items()
            for question in questions
        ]
    else:
        all_questions = [
            {**question, "topic": canonical_topic}
            for question in COURSE_QUIZ_BANK.get(canonical_topic, [])
        ]
    if lecture:
        return [q for q in all_questions if q.get("lecture") == lecture]
    return all_questions


def select_questions(topic: str, difficulty: str, count: int, lecture: Optional[str] = None, offset: int = 0) -> tuple[str, list[Question]]:
    canonical_topic = normalize_topic(topic)
    pool = _topic_pool(canonical_topic, lecture=lecture)
    if lecture and not pool:
        pool = _topic_pool(canonical_topic)
    order = DIFFICULTY_FALLBACK_ORDER.get(difficulty, ["intermediate", "basic", "advanced"])
    selected: list[Question] = []
    for level in order:
        selected.extend(q for q in pool if q["difficulty"] == level)
        if len(selected) >= count:
            break
    if len(selected) < count:
        selected.extend(q for q in pool if q not in selected)
    if not selected:
        selected = [q for questions in COURSE_QUIZ_BANK.values() for q in questions]
    # 确定性轮转：不同考点(subtopic)传入不同 offset，让不同节点从题库不同位置取题，
    # 避免每个节点都拿到同样的前 count 题。
    if offset and selected:
        offset %= len(selected)
        selected = selected[offset:] + selected[:offset]
    selected = selected[:count]
    return canonical_topic, [deepcopy(q) for q in selected]


def recommendation_questions(topic: Optional[str] = None, lecture: Optional[str] = None) -> list[Question]:
    if topic:
        canonical, questions = select_questions(topic, "intermediate", 10, lecture=lecture)
    else:
        canonical = ""
        questions = []
        for topic_name in COURSE_QUIZ_BANK:
            _, topic_questions = select_questions(topic_name, "intermediate", 1, lecture=lecture)
            questions.extend(topic_questions)
    formatted = []
    for idx, question in enumerate(questions, start=1):
        item = deepcopy(question)
        item["id"] = idx
        item["topic"] = topic or normalize_topic(item.get("topic", "综合练习"))
        formatted.append(item)
    return formatted
