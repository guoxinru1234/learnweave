"""Shared request schemas."""
from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional
from pydantic import BaseModel
from typing import Optional, List

class QuizGenerateRequest(BaseModel):
    topic: Optional[str] = None
    count: int = 5
    difficulty: str = "adaptive"
    profile: Optional[List[int]] = None
    user_id: int = 0
    lecture: Optional[str] = None
# ===== 认证相关 =====
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"  # "user" or "admin"

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    is_new_user: bool = False
    has_completed_guide: bool = False

# ===== [NEW] 用户画像相关 =====
class UserProfileBase(BaseModel):
    interested_topics: List[str] = []
    strong_topics: List[str] = []
    weak_topics: List[str] = []
    improvement_goals: List[str] = []
    has_completed_guide: bool = False


class UserProfileCreate(UserProfileBase):
    user_id: int


class UserProfileUpdate(BaseModel):
    interested_topics: Optional[List[str]] = None
    strong_topics: Optional[List[str]] = None
    weak_topics: Optional[List[str]] = None
    improvement_goals: Optional[List[str]] = None
    has_completed_guide: Optional[bool] = None


class UserProfileResponse(UserProfileBase):
    id: int
    user_id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

# ===== 以下是原有的业务模型 =====
DEFAULT_PROFILE = [72, 80, 55, 75, 90, 85]
ALLOWED_DIFFICULTIES = {"adaptive", "basic", "intermediate", "advanced"}


def _default_profile() -> list[int]:
    return DEFAULT_PROFILE.copy()


def _validate_profile(values: list[int]) -> list[int]:
    if len(values) != 6:
        raise ValueError("profile must contain exactly 6 scores")
    if any(score < 0 or score > 100 for score in values):
        raise ValueError("profile scores must be between 0 and 100")
    return values


class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    stream: bool = False


class ProfileAnswer(BaseModel):
    step: int
    answer: str


class ProfileState(BaseModel):
    values: List[int] = Field(default_factory=_default_profile)

    @field_validator("values")
    @classmethod
    def validate_values(cls, values: list[int]) -> list[int]:
        return _validate_profile(values)


class ResourceRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=80)
    resource_types: Optional[List[str]] = None
    user_id: int = 0
    username: str = "anonymous"
    profile: Optional[dict] = None
    path_type: str = "default"


class QuizGenerateRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=80)
    subtopic: Optional[str] = Field(default=None, max_length=120)
    count: int = Field(default=3, ge=1, le=10)
    difficulty: str = "adaptive"
    profile: Optional[List[int]] = None
    user_id: int = 0
    lecture: Optional[str] = None

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, value: str) -> str:
        if value not in ALLOWED_DIFFICULTIES:
            raise ValueError(f"difficulty must be one of {sorted(ALLOWED_DIFFICULTIES)}")
        return value

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, values: list[int] | None) -> list[int] | None:
        if values is None:
            return values
        return _validate_profile(values)


class TutorRequest(BaseModel):
    question: str = Field(min_length=1, max_length=200)
    topic: Optional[str] = Field(default=None, max_length=80)
    history: List[Dict[str, str]] = Field(default_factory=list)


class AgentRunRequest(BaseModel):
    profile: List[int] = Field(default_factory=_default_profile)
    course_id: str = "python-data-analysis"
    lecture_num: int = 1
    course_title: str = "Python数据分析实战"
    lecture_topic: str = ""
    mode: str = "study"

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, values: list[int]) -> list[int]:
        return _validate_profile(values)
