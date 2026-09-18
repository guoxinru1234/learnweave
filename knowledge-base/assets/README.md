# 知识资产索引

本目录由 `scripts/ingest_course_assets.py` 生成，包含课程讲义、实验手册、作业、案例、FAQ 和数据集的结构化索引。

- `catalog.json`: 全量资产元数据
- `chunks.jsonl`: RAG 检索文本块
- `experiments.json`: 实验与案例资产
- `datasets.json`: 数据集资产

本地 ChromaDB 索引可通过 `make assets-chroma` 生成到 `knowledge-base/.chroma/`，该目录不提交 Git。
