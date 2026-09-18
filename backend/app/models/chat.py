from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ChatMessage(BaseModel):
    """单条对话消息"""
    role: str  # user, assistant, system
    content: str

class ChatHistoryCreate(BaseModel):
    """保存对话历史请求"""
    session_id: str
    messages: List[ChatMessage]

class ChatHistoryResponse(BaseModel):
    """对话历史响应"""
    id: int
    session_id: str
    role: str
    content: str
    created_at: datetime