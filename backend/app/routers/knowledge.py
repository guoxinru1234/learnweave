"""Knowledge base routes."""
import json, os, re, shutil, time
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form

from ..core.config import settings
from ..rag.engine import RAGEngine

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


def _load_index():
    idx = settings.kb_path / "index.json"
    if not idx.exists():
        raise HTTPException(503, "知识库未初始化")
    return json.loads(idx.read_text(encoding="utf-8"))


def _load_lecture(lecture_id: str) -> str:
    md = settings.kb_path / lecture_id / "lecture.md"
    if not md.exists():
        raise HTTPException(404, f"讲座 {lecture_id} 不存在")
    return md.read_text(encoding="utf-8")


@router.get("/lectures")
async def list_lectures():
    data = _load_index()
    return {"total": data["total_lectures"], "lectures": data["lectures"]}


@router.get("/lecture/{lecture_id}")
async def get_lecture(lecture_id: str):
    return {"id": lecture_id, "content": _load_lecture(lecture_id)}


@router.get("/search")
async def search_knowledge(q: str = Query(..., min_length=1)):
    results = RAGEngine(str(settings.kb_path)).search(q, top_k=10)
    return {"query": q, "results": results, "count": len(results)}


@router.get("/assets")
async def get_asset_catalog():
    path = settings.kb_path / "assets" / "catalog.json"
    if not path.exists():
        raise HTTPException(503, "课程资产索引未生成，请先运行 make assets")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/asset/{asset_id}/chunks")
async def get_asset_chunks(asset_id: str):
    """获取指定资产的文本块内容"""
    chunks_path = settings.kb_path / "assets" / "chunks.jsonl"
    if not chunks_path.exists():
        raise HTTPException(404, "知识库索引不存在")
    chunks = []
    with open(chunks_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                c = json.loads(line.strip())
                if c.get("asset_id") == asset_id:
                    chunks.append(c)
            except json.JSONDecodeError:
                continue
    return {"asset_id": asset_id, "chunks": chunks, "total": len(chunks)}


def _extract_upload_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix in {".txt", ".md", ".csv", ".json", ".py"}:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        from pypdf import PdfReader
        return "\n\n".join(page.extract_text() or "" for page in PdfReader(str(file_path)).pages)
    if suffix == ".docx":
        from docx import Document
        return "\n".join(p.text for p in Document(str(file_path)).paragraphs if p.text.strip())
    raise HTTPException(400, "仅支持 PDF、DOCX、TXT、Markdown、CSV、JSON 和 Python 文件")


def _split_upload_text(text: str, limit: int = 1200) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, current = [], ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > limit:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(""),
    category: str = Form("manual"),
    topics: str = Form(""),
):
    """上传并解析本地资料到知识库。"""
    allowed_categories = {"lecture", "manual", "lab", "case", "exercise", "dataset", "faq", "answer"}
    if category not in allowed_categories:
        raise HTTPException(400, "资料分类无效")
    original_name = Path(file.filename or "upload.txt").name
    if Path(original_name).suffix.lower() not in {".pdf", ".docx", ".txt", ".md", ".csv", ".json", ".py"}:
        raise HTTPException(400, "不支持该文件格式")
    upload_dir = settings.kb_path / "assets" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / original_name
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        content = _extract_upload_text(file_path).strip()
    except HTTPException:
        file_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(422, f"文件解析失败：{exc}") from exc
    if not content:
        file_path.unlink(missing_ok=True)
        raise HTTPException(422, "文件中没有可提取的文本内容")
    text_chunks = _split_upload_text(content)
    asset_id = f"upload-{int(time.time() * 1000)}"
    topic_list = [item.strip() for item in re.split(r"[,，]", topics) if item.strip()][:10]
    display_title = title.strip() or Path(original_name).stem
    chunks_path = settings.kb_path / "assets" / "chunks.jsonl"
    with open(chunks_path, "a", encoding="utf-8") as f:
        for index, chunk_text in enumerate(text_chunks):
            chunk = {"chunk_id": f"{asset_id}-{index}", "asset_id": asset_id,
                     "title": display_title, "text": chunk_text, "chunk_index": index,
                     "topics": topic_list, "source_path": f"assets/uploads/{original_name}"}
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    catalog_path = settings.kb_path / "assets" / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {"assets": [], "counts": {}}
    assets = catalog.setdefault("assets", []) if isinstance(catalog, dict) else catalog
    asset = {"id": asset_id, "title": display_title, "category": category,
             "topics": topic_list, "chunk_count": len(text_chunks),
             "text_chars": len(content), "suffix": file_path.suffix.lower(),
             "source_path": f"assets/uploads/{original_name}", "uploaded": True}
    assets.insert(0, asset)
    if isinstance(catalog, dict):
        counts = catalog.setdefault("counts", {})
        counts["assets"] = len(assets)
        counts["chunks"] = int(counts.get("chunks", 0)) + len(text_chunks)
        by_category = counts.setdefault("by_category", {})
        by_category[category] = int(by_category.get(category, 0)) + 1
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"success": True, "asset": asset, "filename": original_name,
            "size": file_path.stat().st_size, "text_chars": len(content), "chunk_count": len(text_chunks)}
