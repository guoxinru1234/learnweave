from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, default=1)  # 临时硬编码
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    topic = Column(String(200), nullable=True)
    sources = Column(Text, nullable=True)  # JSON 格式存储来源
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    # user = relationship("User", back_populates="conversations")