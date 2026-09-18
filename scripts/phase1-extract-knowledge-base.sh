#!/bin/bash
# ============================================================
# 阶段1: 教案 → 结构化 Markdown 知识库
# 输入: ../Z01211305A-...docx + ../大数据计算集群技术-教案...docx
# 输出: knowledge-base/{01-24}/*.md + index.json
# ============================================================
source "$(dirname "$0")/common.sh"

PHASE="phase-1"

if is_phase_done "$PHASE"; then
    log_warn "阶段1已完成，跳过。（删除 .progress 强制重跑）"
    exit 0
fi

log_step "阶段1: 提取知识库"

check_python

# 安装依赖
pip3 install python-docx pyyaml --quiet 2>/dev/null || true

# 源文件
DOCX_DIR="$ROOT/.."
SYLLABUS="$DOCX_DIR/Z01211305A-大数据2301-2303班-大数据计算集群技术课程执行大纲-周青峰.docx"
TEACHING="$DOCX_DIR/大数据计算集群技术-教案（大数据2301-2303）.docx"
KB_DIR="$ROOT/knowledge-base"

mkdir -p "$KB_DIR"

# 检查源文件
if [ ! -f "$SYLLABUS" ]; then
    log_error "找不到课程大纲: $SYLLABUS"
    exit 1
fi
if [ ! -f "$TEACHING" ]; then
    log_error "找不到教案: $TEACHING"
    exit 1
fi

log_info "源文件检查通过"

# 编写提取脚本
cat > /tmp/learnmate_extract_kb.py << 'PYEOF'
import sys, os, json, re
from docx import Document

KB_DIR = sys.argv[1]
SYLLABUS = sys.argv[2]
TEACHING = sys.argv[3]

def extract_text(docx_path):
    doc = Document(docx_path)
    lines = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)
    return lines

# 按讲座分割教案内容
def split_lectures(lines):
    lectures = {}
    current_lecture = None
    current_content = []
    lecture_pattern = re.compile(r'第\s*(\d+)\s*[讲 lecture]', re.I)
    
    for line in lines:
        m = lecture_pattern.search(line)
        if m:
            num = int(m.group(1))
            if current_lecture is not None and current_content:
                lectures[current_lecture] = '\n'.join(current_content)
            current_lecture = num
            current_content = [line]
        elif current_lecture is not None:
            current_content.append(line)
        else:
            # 前言/序言放在 lecture 0
            if 0 not in lectures:
                lectures[0] = ''
                current_lecture = 0
                current_content = [line]
            else:
                current_content.append(line)
    
    if current_lecture is not None and current_content:
        lectures[current_lecture] = '\n'.join(current_content)
    
    return lectures

# 生成每讲 Markdown
def generate_markdown(lecture_num, content, syllabus_lines):
    title = f"第{lecture_num}讲"
    # 从大纲中提取标题
    for line in syllabus_lines:
        if f'第{lecture_num}' in line or f'第{lecture_num:02d}' in line:
            title = line.strip()[:80]
            break
    
    md = f"""# {title}

> 课程: 大数据计算集群技术 (Spark 生态)
> 教师: 周青峰
> 教材: 林子雨《Spark编程基础(Scala第2版)》

---

{content}

---

*本文档由 LearnMate 知识库系统自动提取生成*
"""
    return md

# 主流程
print("正在提取大纲...")
syllabus_lines = extract_text(SYLLABUS)
print(f"  大纲: {len(syllabus_lines)} 行")

print("正在提取教案...")
teaching_lines = extract_text(TEACHING)
print(f"  教案: {len(teaching_lines)} 行")

print("正在分割讲座...")
lectures = split_lectures(teaching_lines + syllabus_lines)
print(f"  识别到 {len(lectures)} 个讲座单元")

# 创建目录结构
os.makedirs(KB_DIR, exist_ok=True)

# 讲座标题映射
lecture_titles = {}
title_pattern = re.compile(r'第\s*(\d+)\s*[讲课].*[:：]?\s*(.+)')

for line in syllabus_lines + teaching_lines:
    m = title_pattern.search(line)
    if m:
        num = int(m.group(1))
        title = m.group(2).strip()[:60]
        if num not in lecture_titles:
            lecture_titles[num] = title

# 生成 Markdown 文件
manifest = {"course": "大数据计算集群技术", "total_lectures": 0, "lectures": []}

for num in sorted(lectures.keys()):
    if num == 0:
        continue
    content = lectures[num]
    title = lecture_titles.get(num, f"第{num}讲")
    
    # 保存 Markdown
    dir_name = f"{num:02d}"
    os.makedirs(os.path.join(KB_DIR, dir_name), exist_ok=True)
    md_path = os.path.join(KB_DIR, dir_name, "lecture.md")
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(generate_markdown(num, content, syllabus_lines))
    
    manifest["lectures"].append({
        "id": num,
        "title": title,
        "dir": dir_name,
        "file": "lecture.md",
        "lines": len(content.split('\n'))
    })
    print(f"  ✓ 第{num:02d}讲: {title[:50]}")

manifest["total_lectures"] = len(manifest["lectures"])

# 保存 manifest
with open(os.path.join(KB_DIR, 'index.json'), 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"\n完成! 共生成 {manifest['total_lectures']} 个讲座文件")
print(f"知识库路径: {KB_DIR}")
PYEOF

python3 /tmp/learnmate_extract_kb.py "$KB_DIR" "$SYLLABUS" "$TEACHING"

# 验证
if [ -f "$KB_DIR/index.json" ]; then
    LECTURE_COUNT=$(python3 -c "import json; print(json.load(open('$KB_DIR/index.json'))['total_lectures'])")
    log_ok "知识库提取完成: ${LECTURE_COUNT} 讲"
    mark_phase_done "$PHASE"
else
    log_error "知识库提取失败"
    exit 1
fi
