from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import re
from ..agents.tutor_agent import get_tutor_agent, clean_tutor_visible_text

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _clean(text: str) -> str:
    """清洗 Markdown"""
    text = clean_tutor_visible_text(text)
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\-*]{3,}\s*$', '', text, flags=re.MULTILINE)
    lines = text.split('\n')
    clean, skip = [], False
    for line in lines:
        s = line.strip()
        if s.startswith('|') and s.endswith('|'):
            if re.match(r'^\|[\s\-:|]+\|$', s): skip = True; continue
            if skip or '|' in s[1:-1]:
                cells = [c.strip() for c in s[1:-1].split('|')]
                clean.append('：'.join(cells)); skip = True; continue
        skip = False
        line = re.sub(r'^(\s*)[-*]\s+', r'\1· ', line)
        line = re.sub(r'`([^`]+)`', r'\1', line)
        clean.append(line)
    text = '\n'.join(clean)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    role: str
    content: str
    sources: List[Dict[str, Any]] = []
    follow_up: List[str] = []
    session_id: str


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())

        # 提取最后一条用户消息
        user_messages = [m for m in request.messages if m.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="没有用户消息")

        question = user_messages[-1].content

        # 调用 TutorAgent，传入完整对话历史
        tutor = get_tutor_agent()
        result = await tutor.answer_with_history(
            question=question,
            history=[m.model_dump() for m in request.messages],
            topic=None
        )

        return ChatResponse(
            role="assistant",
            content=_clean(result.get("answer", "抱歉，我暂时无法回答这个问题。")),
            sources=result.get("sources", []),
            follow_up=result.get("follow_up", []),
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 服务错误: {str(e)}")
