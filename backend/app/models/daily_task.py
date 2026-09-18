# 每日任务数据类（纯 Python，不再依赖 SQLAlchemy）
from dataclasses import dataclass
from datetime import date

@dataclass
class DailyTask:
    """每日任务数据模型（与数据库表对应）"""
    id: int | None = None
    user_id: int = 1
    date: date | None = None
    content: str = ""
    category: str = "custom"  # lecture, quiz, lab, custom
    is_done: bool = False