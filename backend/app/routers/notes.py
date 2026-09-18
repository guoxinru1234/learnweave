from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..core.database import get_connection
from ..core.deps import get_current_user_id

router = APIRouter(prefix="/notes", tags=["notes"])

class NoteCreate(BaseModel):
    lecture_id: int = 0
    category: str = "course"
    title: str = ""
    content: str

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None

class NoteResponse(BaseModel):
    id: int
    lecture_id: int
    category: str
    title: str
    content: str
    created_at: str
    updated_at: str


@router.get("", response_model=List[NoteResponse])
@router.get("/", response_model=List[NoteResponse])
def get_notes(
    lecture_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    user_id: int = Depends(get_current_user_id)
):
    """获取笔记列表，支持按讲次/分类筛选和关键词搜索"""
    with get_connection() as conn:
        sql = """
            SELECT id, lecture_id, category, title, content, created_at, updated_at
            FROM notes WHERE user_id = ?
        """
        params = [user_id]

        if lecture_id is not None:
            sql += " AND lecture_id = ?"
            params.append(lecture_id)
        if category:
            sql += " AND category = ?"
            params.append(category)
        if q:
            sql += " AND (title LIKE ? OR content LIKE ?)"
            params.append(f"%{q}%")
            params.append(f"%{q}%")

        sql += " ORDER BY created_at DESC"
        rows = conn.execute(sql, params).fetchall()

    return [
        {
            "id": row[0],
            "lecture_id": row[1],
            "category": row[2] or "course",
            "title": row[3] or "",
            "content": row[4],
            "created_at": row[5],
            "updated_at": row[6],
        }
        for row in rows
    ]


@router.get("/categories/stats")
def get_category_stats(user_id: int = Depends(get_current_user_id)):
    """获取各分类的笔记数量统计"""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT category, COUNT(*) as count FROM notes WHERE user_id = ? GROUP BY category",
            (user_id,)
        ).fetchall()
    result = {}
    for row in rows:
        cat = row[0] or "uncategorized"
        result[cat] = row[1]
    return result


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(note_id: int, user_id: int = Depends(get_current_user_id)):
    """获取单条笔记详情"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, lecture_id, category, title, content, created_at, updated_at FROM notes "
            "WHERE id = ? AND user_id = ?",
            (note_id, user_id)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Note not found")
    return {
        "id": row[0],
        "lecture_id": row[1],
        "category": row[2] or "course",
        "title": row[3] or "",
        "content": row[4],
        "created_at": row[5],
        "updated_at": row[6],
    }


@router.post("/", response_model=NoteResponse, status_code=201)
def create_note(note: NoteCreate, user_id: int = Depends(get_current_user_id)):
    """创建新笔记"""
    now = datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO notes (user_id, lecture_id, category, title, content, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, note.lecture_id, note.category, note.title, note.content, now, now)
        )
        conn.commit()
        new_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, lecture_id, category, title, content, created_at, updated_at FROM notes WHERE id = ?",
            (new_id,)
        ).fetchone()
    return {
        "id": row[0],
        "lecture_id": row[1],
        "category": row[2] or "course",
        "title": row[3] or "",
        "content": row[4],
        "created_at": row[5],
        "updated_at": row[6],
    }


@router.patch("/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, update: NoteUpdate, user_id: int = Depends(get_current_user_id)):
    """更新笔记"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM notes WHERE id = ? AND user_id = ?",
            (note_id, user_id)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Note not found")

        updates = []
        params = []
        if update.title is not None:
            updates.append("title = ?")
            params.append(update.title)
        if update.content is not None:
            updates.append("content = ?")
            params.append(update.content)
        if update.category is not None:
            updates.append("category = ?")
            params.append(update.category)
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(note_id)

        conn.execute(f"UPDATE notes SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()

        row = conn.execute(
            "SELECT id, lecture_id, category, title, content, created_at, updated_at FROM notes WHERE id = ?",
            (note_id,)
        ).fetchone()
    return {
        "id": row[0],
        "lecture_id": row[1],
        "category": row[2] or "course",
        "title": row[3] or "",
        "content": row[4],
        "created_at": row[5],
        "updated_at": row[6],
    }


@router.delete("/{note_id}")
def delete_note(note_id: int, user_id: int = Depends(get_current_user_id)):
    """删除笔记"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM notes WHERE id = ? AND user_id = ?",
            (note_id, user_id)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Note not found")
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
    return {"message": "deleted"}


@router.get("/export/{lecture_id}")
def export_notes(lecture_id: int, user_id: int = Depends(get_current_user_id)):
    """导出某个讲次的所有笔记为 Markdown 格式"""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT title, content, created_at FROM notes "
            "WHERE user_id = ? AND lecture_id = ? ORDER BY created_at",
            (user_id, lecture_id)
        ).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No notes found for this lecture")

    lines = [f"# 笔记 - 讲次 {lecture_id}\n"]
    lines.append(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append("---\n")

    for row in rows:
        title = row[0] or "无标题笔记"
        content = row[1]
        created_at = row[2]
        lines.append(f"## {title}")
        lines.append(f"*创建于: {created_at}*\n")
        lines.append(content)
        lines.append("\n---\n")

    return {
        "filename": f"notes_lecture_{lecture_id}.md",
        "content": "\n".join(lines),
        "count": len(rows)
    }
