# 纯 Python 数据类（无 SQLAlchemy）
from dataclasses import dataclass

@dataclass
class Note:
    """笔记数据模型"""
    id: int | None = None
    user_id: int = 1
    lecture_id: int = 0
    category: str = "course"  # course, personal, business, meeting
    title: str = ""
    content: str = ""
    created_at: str | None = None
    updated_at: str | None = None