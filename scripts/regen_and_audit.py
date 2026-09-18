import json, os, sys
kb = 'knowledge-base'
chunks = []
for d in sorted(os.listdir(kb)):
    dp = os.path.join(kb, d)
    if not os.path.isdir(dp) or not d.isdigit(): continue
    lf = os.path.join(dp, 'lecture.md')
    if not os.path.exists(lf): continue
    with open(lf, encoding='utf-8') as f: text = f.read()
    for i in range(0, len(text), 500):
        c = text[i:i+500].strip()
        if len(c) > 50:
            chunks.append({'chunk_id': f'{d}-{i//500:03d}', 'asset_id': f'lecture-{d}', 'title': d, 'text': c, 'index': i//500})
os.makedirs(f'{kb}/assets', exist_ok=True)
with open(f'{kb}/assets/chunks.jsonl', 'w', encoding='utf-8') as f:
    for c in chunks: f.write(json.dumps(c, ensure_ascii=False) + '\n')
print(f'{len(chunks)} chunks')

# Audit
CORE_MAP = {61:'变量与运算符',62:'流程控制',63:'函数定义',64:'模块化编程',65:'数组索引与切片',66:'广播机制',67:'向量化运算',68:'随机数生成',69:'CSV与Excel',70:'数据筛选与条件过滤',71:'缺失值处理',72:'异常值检测与处理',73:'文本数据清洗',74:'train_test_split'}
ok = 0
for nid in range(61,75):
    lf = os.path.join(kb, f'{nid:02d}', 'lecture.md')
    with open(lf, encoding='utf-8') as f: text = f.read()
    has_ex = '```python' in text
    has_err = '常见错误' in text
    good = len(text) > 500 and has_ex and has_err
    print(f'{"PASS" if good else "FAIL"} | {nid} {CORE_MAP[nid]} | {len(text)} chars | ex={has_ex} | err={has_err}')
    if good: ok += 1
print(f'Chapters with real code: {ok}/14')

# Coverage eval
sys.path.insert(0, 'backend')
from tests.offline_eval import evaluate_knowledge_coverage, KB_PATH, load_kb_facts, evaluate_hallucination
all_c = []
for d in sorted(KB_PATH.iterdir()):
    if d.is_dir() and d.name.isdigit():
        lf = d / 'lecture.md'
        if lf.exists(): all_c.append(lf.read_text(encoding='utf-8'))
cov = evaluate_knowledge_coverage(all_c)
print(f'Coverage: {cov["covered"]}/{cov["total"]} = {cov["coverage_rate"]}%')
h = evaluate_hallucination(' '.join(all_c[:40]), load_kb_facts())
print(f'Hallucination: {h["hallucination_rate"]}%')
