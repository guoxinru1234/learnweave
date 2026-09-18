#!/usr/bin/env python3
"""用 LLM 为知识库空壳讲次生成中文结构化教学内容（基于官方文档，防幻觉）。

用法:
  python scripts/generate_lecture_content.py 16 20   # 生成第 16-20 讲
  python scripts/generate_lecture_content.py 21 25   # 生成第 21-25 讲
"""
import sys
import os
import json
import time
from pathlib import Path

# 把 backend 加入 sys.path
BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.core.llm import get_llm_client

KB = Path(__file__).resolve().parent.parent / "knowledge-base"

SYSTEM_PROMPT = """你是 Python 数据分析领域的资深课程讲师。请为指定知识点生成一份详实、准确的中文学习讲义，作为领域知识库的正式内容。

严格要求：
1. 只使用 Python / NumPy / Pandas / Matplotlib / Scikit-learn 等库【真实存在】的 API，绝不编造不存在的函数名、参数或返回值。
2. 所有代码必须可运行，带中文注释，不写伪代码。
3. 概念解释准确，符合官方文档描述。
4. 内容要详实：概念、原理、代码示例、常见错误、练习都要有。
"""


def load_lecture_meta():
    with open(KB / "index.json", encoding="utf-8") as f:
        idx = json.load(f)
    return {lec["id"]: lec for lec in idx.get("lectures", [])}


def generate_lecture(llm, num, title, module):
    prompt = f"""请为「{title}」（属于「{module}」模块）生成一份完整的中文学习讲义。

输出结构（用 Markdown，## 表示二级标题）：

# {title}
> 模块：{module} | 编号：第{num}讲 | Python数据分析实战

## 1. 概念
（核心概念的定义和适用场景，150-300字，给一个生活化类比帮助理解）

## 2. 核心API与原理
（列出该知识点最常用的 3-5 个 API/方法，逐个说明签名、参数、返回值，用表格呈现）

## 3. 代码示例
（3 个从简单到进阶的可运行 Python 代码示例，每个带输出结果注释）

## 4. 常见错误
（3 个新手常犯的错误，每个给出错误原因和正确写法）

## 5. 练习
（2 道思考题或动手题，附答案提示）

要求：内容详实、准确、代码可运行，总字数 1500-3000 字。只输出 Markdown 内容，不要额外解释。"""

    content = llm.chat_sync(
        [{"role": "system", "content": SYSTEM_PROMPT},
         {"role": "user", "content": prompt}],
        temperature=0.5, max_tokens=4000,
    )
    return content.strip()


def write_lecture(num, content):
    path = KB / f"{num:02d}" / "lecture.md"
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return len(content)


def main():
    if len(sys.argv) < 3:
        print("用法: python generate_lecture_content.py <起始讲次> <结束讲次>")
        sys.exit(1)

    start = int(sys.argv[1])
    end = int(sys.argv[2])
    meta = load_lecture_meta()
    llm = get_llm_client()

    for num in range(start, end + 1):
        lec = meta.get(num)
        if not lec:
            print(f"  [{num:02d}] 讲次不存在，跳过")
            continue
        title = lec.get("title", f"第{num}讲")
        module = lec.get("module", "Python数据分析")

        print(f"[{num:02d}] 生成 {title}（{module}）...")
        try:
            content = generate_lecture(llm, num, title, module)
            length = write_lecture(num, content)
            print(f"  → 写入 {length} 字")
        except Exception as e:
            print(f"  → 失败: {e}")
        time.sleep(1)  # 避免 API 限流

    print("\n完成。")


if __name__ == "__main__":
    main()
