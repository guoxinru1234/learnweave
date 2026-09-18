"""Application settings for LearnWeave backend."""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = Path(__file__).resolve().parents[2]
LEARNMATE_DIR = Path(__file__).resolve().parents[3]

load_dotenv(LEARNMATE_DIR / ".env")


class Settings:
    """统一的应用配置，从 .env 加载"""

    # ========== App ==========
    app_name: str = "LearnWeave API"
    version: str = "0.4.0"

    # ========== 路径 ==========
    learnmate_dir: Path = LEARNMATE_DIR
    backend_dir: Path = BACKEND_DIR
    kb_path: Path = LEARNMATE_DIR / "knowledge-base"
    external_kb_path: str = os.getenv("EXTERNAL_KB_PATH", "")  # 外部知识库路径，留空则不用
    data_dir: Path = BACKEND_DIR / "data"
    db_path: Path = data_dir / "learnmate.db"

    # ========== LLM 通用 ==========
    llm_provider: str = os.getenv("LLM_PROVIDER", "deepseek")
    llm_model: str = os.getenv("LLM_MODEL", "deepseek-chat")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")

    # ========== DeepSeek ==========
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    # ========== OpenAI ==========
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    # ========== 通义千问 ==========
    qwen_api_key: str = os.getenv("DASHSCOPE_API_KEY", os.getenv("QWEN_API_KEY", ""))

    # ========== 智谱 GLM ==========
    glm_api_key: str = os.getenv("ZHIPU_API_KEY", os.getenv("GLM_API_KEY", ""))

    # ========== Moonshot (Kimi) ==========
    moonshot_api_key: str = os.getenv("MOONSHOT_API_KEY", "")

    # ========== 讯飞星火 ==========
    xfyun_api_password: str = os.getenv("XFYUN_API_PASSWORD", "")

    # ========== Groq ==========
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")

    # ========== 学习闭环 ==========
    learning_loop_enabled: bool = os.getenv("LEARNING_LOOP_ENABLED", "true").lower() in ("1", "true", "yes")
    learning_loop_cooldown_seconds: int = int(os.getenv("LEARNING_LOOP_COOLDOWN_SECONDS", "300"))
    default_course_id: str = os.getenv("DEFAULT_COURSE_ID", "python-data-analysis")

    @property
    def cors_origins(self) -> list[str]:
        raw = os.getenv("CORS_ORIGINS", "*")
        return [item.strip() for item in raw.split(",") if item.strip()]


settings = Settings()
