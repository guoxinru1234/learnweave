#!/usr/bin/env python3
"""完整知识库提取：从 syllabus（大纲表） + teaching plan（教案表）生成 24 讲 Markdown"""
import json, os, re, sys
from docx import Document

KB_DIR = sys.argv[1]
SYLLABUS_PATH = sys.argv[2]
TEACHING_PATH = sys.argv[3]

# ====== 1. Parse Syllabus ======
doc_syl = Document(SYLLABUS_PATH)
syllabus = []  # list of {num, title, content, week, date, hours_theory, hours_lab, prep, method, post}

if doc_syl.tables:
    t = doc_syl.tables[0]
    for row in t.rows[2:]:  # skip 2 header rows
        cells = [c.text.strip() for c in row.cells]
        if len(cells) < 10:
            continue
        date, week, day, num, content, theory, lab, prep, method, post = cells[:10]
        # Parse lecture number
        num_match = re.search(r'第\s*([一二三四五六七八九十百千\d]+)\s*讲', num)
        if not num_match:
            continue
        num_str = num_match.group(1)
        # Chinese numeral to int
        cn_map = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
                  '十一':11,'十二':12,'十三':13,'十四':14,'十五':15,'十六':16,'十七':17,'十八':18,'十九':19,'二十':20}
        try:
            ln = int(num_str) if num_str.isdigit() else cn_map.get(num_str, 0)
        except:
            ln = cn_map.get(num_str, 0)
        if ln == 0:
            continue
        
        # Extract title from content
        title_match = re.search(r'教学主题[：:]\s*(.+?)(?:\n|$)', content)
        exp_match = re.search(r'实验主题[：:]\s*(.+?)(?:\n|$)', content)
        title = title_match.group(1) if title_match else (exp_match.group(1) if exp_match else f'第{ln}讲')
        
        syllabus.append({
            'num': ln,
            'title': title[:80],
            'content': content[:500],
            'date': date, 'week': week,
            'hours_theory': theory, 'hours_lab': lab,
            'prep': prep, 'method': method, 'post': post
        })

print(f"  Syllabus: {len(syllabus)} lectures extracted")

# ====== 2. Parse Teaching Plans ======
doc_tp = Document(TEACHING_PATH)
teaching_plans = {}  # num -> dict

for table in doc_tp.tables:
    data = {}
    for row in table.rows:
        cells = [c.text.strip() for c in row.cells]
        if len(cells) < 2:
            continue
        # First cell is label, merged cells contain value
        label = cells[0].strip()
        value = ' '.join(c for c in cells[2:] if c.strip()) if len(cells) > 2 else cells[1].strip()
        
        if '授课题目' in label:
            data['title'] = value
        elif '教学目的' in label or '教学目标' in label:
            data['objectives'] = value
        elif '教学重点' in label:
            data['key_points'] = value
        elif '教学难点' in label:
            data['difficulties'] = value
        elif '教学内容' in label or '授课内容' in label:
            data['teaching_content'] = value
        elif '教学过程' in label:
            data['process'] = value
        elif '教学手段' in label or '教学方法' in label:
            data['methods'] = value
        elif '作业' in label or '课后要求' in label:
            data['homework'] = value
        elif '时间' in label:
            data['time'] = value
        elif '授课类型' in label or '类型' in label:
            data['type'] = value
        elif '课时' in label:
            data['hours'] = value
        elif '教材' in label or '参考' in label:
            data['references'] = value
        elif '思政' in label or '课程思政' in label:
            data['ideology'] = value
    
    if data.get('title'):
        # Match to lecture number by title keyword
        for s in syllabus:
            if s['title'][:6] in data['title'] or data['title'][:6] in s['title']:
                teaching_plans[s['num']] = data
                break
        # Fallback: try matching by content
        if not any(s['num'] in teaching_plans for s in syllabus if s['title'][:6] in data.get('title','')):
            # Just store by order
            idx = len(teaching_plans) + 1
            teaching_plans[idx] = data

print(f"  Teaching Plans: {len(teaching_plans)} detailed plans extracted")

# ====== 3. Generate Markdown ======
os.makedirs(KB_DIR, exist_ok=True)
manifest = {"course": "大数据计算集群技术", "total_lectures": 0, "lectures": []}

for s in sorted(syllabus, key=lambda x: x['num']):
    num = s['num']
    tp = teaching_plans.get(num, {})
    
    type_label = '理论' if tp.get('type') else '理论/实验'
    refs = tp.get('references', '')
    if not refs:
        refs = '1. 林子雨《Spark编程基础(Scala第2版)》，人民邮电出版社'
        refs += chr(10) + '2. Spark官方文档: https://spark.apache.org/docs/latest/'
    md = f"""# 第{num}讲：{s['title']}

> **课程**: 大数据计算集群技术 (Spark 生态)
> **教师**: 周青峰 · 河南工业大学 人工智能与大数据学院
> **教材**: 林子雨《Spark编程基础(Scala第2版)》
> **日期**: {s['date']} · {s['week']}
> **课时**: 理论 {s['hours_theory']}h / 实验 {s['hours_lab']}h

---

## 教学目的与要求

{tp.get('objectives', '（见下方教学内容）')}

## 教学重点

{tp.get('key_points', '（见下方教学内容）')}

## 教学难点

{tp.get('difficulties', '（见下方教学内容）')}

## 教学内容

### 课堂讲授

{s['content']}

{tp.get('teaching_content', '')}

### 教学过程设计

{tp.get('process', '（按教材章节顺序进行）')}

## 教学方法与手段

{tp.get('methods', s.get('method', '')[:300])}

## 课前预习要求

{s.get('prep', '')[:500]}

## 课后作业与要求

{tp.get('homework', s.get('post', '')[:500])}

## 课程思政元素

{tp.get('ideology', '结合大数据技术发展，培养学生的科技创新意识和工程伦理素养')}

## 参考资料

{refs}

---

*本文档由 LearnMate 知识库系统自动提取生成 · 第{num}讲*
"""
    
    dir_name = f"{num:02d}"
    os.makedirs(os.path.join(KB_DIR, dir_name), exist_ok=True)
    with open(os.path.join(KB_DIR, dir_name, 'lecture.md'), 'w', encoding='utf-8') as f:
        f.write(md)
    
    manifest['lectures'].append({
        'id': num, 'title': s['title'][:80], 'dir': dir_name, 'file': 'lecture.md'
    })

manifest['total_lectures'] = len(manifest['lectures'])

with open(os.path.join(KB_DIR, 'index.json'), 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"\n  ✅ 知识库生成完成: {manifest['total_lectures']} 讲")
