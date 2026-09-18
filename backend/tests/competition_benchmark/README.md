# Competition benchmark

This benchmark contains 50 reproducible, de-identified cases for the competition.
It is not a claim that these are 50 real learners. Cases are formed from five
learning profiles and ten real curriculum topics. Run `python generate_cases.py`
from this directory to regenerate `cases.jsonl` and `expected_labels.jsonl`.

Each case is one learner-topic pair. The expected level is the target for resource
generation, while the knowledge points are the facts that must be traceable to the
course knowledge base. Generated output should be stored separately in
`generated_results.jsonl`; never overwrite the inputs or labels.

The benchmark covers the competition's minimum three learner groups and expands
them to five profiles: beginner, theory-oriented, practice-oriented, balanced,
and advanced. The ten topics map to lectures 1-10 of `python-data-analysis`.

## Metrics

- Difficulty match: approved cases / all cases
- Knowledge coverage: matched expected points / all expected points
- Hallucination rate: unsupported factual claims / extracted factual claims
- Code pass rate: executable code / cases containing code

The labels are review targets, not measured results. A competition report must be
generated from actual system output and include the run timestamp, model name,
knowledge-base revision, and audit report for every case.
