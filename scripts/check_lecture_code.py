#!/usr/bin/env python3
"""检查 13-60 讲 lecture.md 里所有 Python 代码块的语法正确性。"""
import re
import ast
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

total_blocks = 0
syntax_errors = []

for num in range(13, 61):
    path = f'knowledge-base/{num:02d}/lecture.md'
    try:
        with open(path, encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        continue
    # 提取 python 代码块（用三反引号包裹）
    blocks = re.findall(r'```python\n(.*?)```', content, re.DOTALL)
    for i, block in enumerate(blocks):
        total_blocks += 1
        try:
            ast.parse(block)
        except SyntaxError as e:
            syntax_errors.append((num, i, f"第{e.lineno}行: {e.msg}"))

print(f"共检查 {total_blocks} 个 Python 代码块")
print(f"语法错误: {len(syntax_errors)} 个")
for num, i, err in syntax_errors[:20]:
    print(f"  lecture {num} 代码块{i}: {err}")
