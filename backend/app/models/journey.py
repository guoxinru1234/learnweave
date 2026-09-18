from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class JourneyStep:
    """学习旅程步骤"""
    id: int
    label: str
    icon: str
    href: str
    completed: bool = False
    active: bool = False
    completed_at: Optional[str] = None

@dataclass
class Journey:
    """学习旅程"""
    user_id: int = 1
    steps: List[JourneyStep] = field(default_factory=lambda: [
        JourneyStep(1, "画像分析", "[Brain]", "/profile"),
        JourneyStep(2, "学习讲次", "📖", "/learn"),
        JourneyStep(3, "实践实验", "🧪", "/labs"),
        JourneyStep(4, "题库练习", "[Memo]", "/quiz"),
        JourneyStep(5, "学习评估", "📊", "/assessment"),
        JourneyStep(6, "掌握达成", "[Party]", "/"),
    ])
    current_step_id: int = 1
    overall_progress: float = 0.0
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_current_step(self) -> JourneyStep:
        return next((s for s in self.steps if s.id == self.current_step_id), self.steps[0])

    def get_next_step(self) -> Optional[JourneyStep]:
        for step in self.steps:
            if not step.completed:
                return step
        return None

    def complete_step(self, step_id: int):
        for step in self.steps:
            if step.id == step_id:
                step.completed = True
                step.completed_at = datetime.now().isoformat()
                break
        # 更新当前步骤
        for step in self.steps:
            if not step.completed:
                self.current_step_id = step.id
                step.active = True
                break
        else:
            self.current_step_id = self.steps[-1].id
            self.steps[-1].active = True

        # 计算总体进度
        completed = sum(1 for s in self.steps if s.completed)
        self.overall_progress = completed / len(self.steps)
        self.updated_at = datetime.now().isoformat()

# 存储（模拟数据库，实际应使用真实 DB）
_journey_store: dict[int, Journey] = {}

def get_journey(user_id: int = 1) -> Journey:
    if user_id not in _journey_store:
        _journey_store[user_id] = Journey(user_id=user_id)
    return _journey_store[user_id]

def save_journey(journey: Journey):
    _journey_store[journey.user_id] = journey