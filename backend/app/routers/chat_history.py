from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..core.database import get_connection
from ..core.deps import get_current_user_id
from ..models.chat import ChatHistoryCreate, ChatHistoryResponse, ChatMessage

router = APIRouter(prefix="/api/chat/history", tags=["chat"])

@router.post("/save")
def save_chat_history(history: ChatHistoryCreate,
                      user_id: int = Depends(get_current_user_id)):
    """保存对话历史（按当前登录用户隔离）"""
    with get_connection() as conn:
        for msg in history.messages:
            conn.execute(
                """
                INSERT INTO chat_history (user_id, session_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, history.session_id, msg.role, msg.content, datetime.now().isoformat())
            )
        conn.commit()
    return {"status": "saved", "session_id": history.session_id, "count": len(history.messages)}

@router.get("/{session_id}")
def get_chat_history(session_id: str,
                     user_id: int = Depends(get_current_user_id), limit: int = 50):
    """获取某个会话的历史记录（仅限当前用户自己的会话）"""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, session_id, role, content, created_at
            FROM chat_history
            WHERE user_id = ? AND session_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (user_id, session_id, limit)
        ).fetchall()
    return [dict(row) for row in rows]

@router.get("/sessions/list")
def list_sessions(user_id: int = Depends(get_current_user_id)):
    """获取当前用户的所有对话会话列表（按最近活动排序）"""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT session_id, MAX(created_at) as last_activity, COUNT(*) as message_count
            FROM chat_history
            WHERE user_id = ?
            GROUP BY session_id
            ORDER BY last_activity DESC
            """,
            (user_id,)
        ).fetchall()
    return [dict(row) for row in rows]

@router.delete("/{session_id}")
def delete_session(session_id: str,
                   user_id: int = Depends(get_current_user_id)):
    """删除整个会话（仅限当前用户自己的会话）"""
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM chat_history WHERE user_id = ? AND session_id = ?",
            (user_id, session_id)
        )
        conn.commit()
    return {"status": "deleted", "session_id": session_id}