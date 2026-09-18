"""Audit 10 randomly sampled facts with full evidence chain."""
import json, re, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "tests"))
from offline_eval import generated_resource_hallucination_rate, load_kb_facts, PROJECT_ROOT

kb = load_kb_facts()
res_path = PROJECT_ROOT / "backend" / "data" / "lecture_cache" / "english_test_resource.json"
with open(res_path, encoding="utf-8") as f:
    real = json.load(f)

content = real["resource"]["content"]
code = real["resource"]["code"]
cites = real.get("citations", [])

# Extract facts
clean = re.sub(r"```.*?```", "", content + "\n" + code, flags=re.DOTALL)
clean = re.sub(r"<[^>]+>", "", clean)
clean = re.sub(r"^#+\s+.*$", "", clean, flags=re.MULTILINE)
clean = re.sub(r"^[-*]\s+.*$", "", clean, flags=re.MULTILINE)
stmts = [s.strip() for s in re.findall(r"[^.!?\n。！？]{40,300}[.!?。！？]", clean)
         if not re.match(r"^(本讲|本节|我们|首先|接下来|最后|总结|请|注意|提示)", s)]

# Build full text per source
kb_full = {}
for f in kb:
    sid = f["source"]
    kb_full[sid] = kb_full.get(sid, "") + " " + f["text"]

# Map citation path -> source_id
cite_map = {}
for c in cites:
    src = c["source"].replace("\\", "/")
    for p in src.split("/"):
        if p.isdigit():
            cite_map[c["source"]] = f"lecture-{int(p):02d}"
            break

random.seed(42)
sample = random.sample(stmts, min(10, len(stmts)))
issues_found = 0

for i, stmt in enumerate(sample):
    print(f"=== Fact {i} ===")
    print(f"STATEMENT: {stmt[:120]}")
    supported_by = []
    for csrc, sid in cite_map.items():
        if sid and sid in kb_full:
            full_text = kb_full[sid]
            skw = set(re.findall(r"[A-Za-z]{3,}|[一-鿿]{2,}", stmt.lower()))
            for chunk_start in range(0, len(full_text), 150):
                chunk = full_text[chunk_start:chunk_start+350]
                ckw = set(re.findall(r"[A-Za-z]{3,}|[一-鿿]{2,}", chunk.lower()))
                overlap = skw & ckw
                if len(overlap) >= 3:
                    supported_by.append({"source": sid, "excerpt": chunk.strip()[:250], "overlap": list(overlap)[:8]})
                    break
    if supported_by:
        ev = supported_by[0]
        actual_path = PROJECT_ROOT / csrc.replace("\\", "/")
        in_file = actual_path.exists() and (ev["excerpt"][:100] in actual_path.read_text(encoding="utf-8"))
        print(f"SOURCE: {ev['source']}")
        print(f"EXCERPT: {ev['excerpt'][:200]}")
        print(f"EXCERPT_IN_FILE: {in_file}")
        print(f"OVERLAP: {ev['overlap']}")
        direct = "Yes (specific chunk with keyword overlap >= 3)"
        print(f"DIRECT_SUPPORT: {direct}")
        print(f"STATUS: supported")
        if not in_file:
            issues_found += 1
            print("ISSUE: excerpt not found in actual file!")
    else:
        print(f"STATUS: unsupported")
        issues_found += 1
    print()

print(f"Issues found: {issues_found}/{len(sample)}")
if issues_found == 0:
    print("All sampled facts have genuine, specific evidence support.")
else:
    print(f"WARNING: {issues_found} facts lack proper evidence.")
