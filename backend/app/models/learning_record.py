from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base

class LearningRecord(Base):
    __tablename__ = "learning_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    study_minutes = Column(Integer, default=0)
    completed_lectures = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)  # 0-100

    # 如果已有 User 模型，请添加 relationship
    # user = relationship("User", back_populates="learning_records")