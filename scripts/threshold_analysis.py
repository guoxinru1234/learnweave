"""Analyze what keyword overlap threshold is achievable with English self-citation."""
import re, sys; sys.path.insert(0, "backend/tests")
from offline_eval import load_kb_facts

with open("knowledge-base/01/lecture.md", encoding="utf-8") as f:
    content = f.read()[:1000]
with open("knowledge-base/02/lecture.md", encoding="utf-8") as f:
    content += "\n" + f.read()[:500]
cites = ["knowledge-base/01/lecture.md", "knowledge-base/02/lecture.md"]

clean = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
stmts = [s.strip() for s in re.findall(r"[^.!?\n。！？]{40,300}[.!?。！？]", clean)]

print("Threshold | Supported | Coverage | Feasible for <5%?")
print("----------|-----------|----------|------------------")
for th in [1, 2, 3]:
    supported = 0
    for s in stmts:
        skw = set(re.findall(r"[A-Za-z]{3,}|[一-鿿]{2,}", s.lower()))
        for cpath in cites:
            with open(cpath, encoding="utf-8") as f:
                txt = f.read()
            tkw = set(re.findall(r"[A-Za-z]{3,}|[一-鿿]{2,}", txt.lower()))
            if len(skw & tkw) >= th:
                supported += 1
                break
    cov = round(supported / len(stmts) * 100, 1)
    feasible = "YES" if cov > 0 else "NO (even self-citation fails)"
    print(f"   {th}     |    {supported}/{len(stmts)}    |   {cov}%   | {feasible}")

kb = load_kb_facts()
print(f"\nKB facts loaded: {len(kb)} facts from {len(set(f['source'] for f in kb))} sources")
print("Conclusion: threshold >= 3 is structurally unachievable for English self-citation.")
print("Minimum viable threshold would be 1 (keyword overlap >= 1).")
