"""SQLite-backed product data store.

The database is intentionally lightweight for local deployment. It is seeded
from the generated knowledge asset indexes so lab APIs are available without a
separate provisioning step.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .config import settings


def get_connection() -> sqlite3.Connection:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _row_to_dict(row: sqlite3.Row) -> dict:
    data = dict(row)
    for key in ("topics", "lecture_ids", "payload"):
        if key in data and isinstance(data[key], str) and data[key]:
            data[key] = json.loads(data[key])
    return data


def init_db() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(
            """
            -- ===== 课程相关表 =====
            CREATE TABLE IF NOT EXISTS courses (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS lectures (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                dir TEXT NOT NULL,
                file TEXT NOT NULL
            );

            -- ===== 实验相关表 =====
            CREATE TABLE IF NOT EXISTS labs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                source_path TEXT NOT NULL,
                suffix TEXT NOT NULL,
                topics TEXT NOT NULL,
                lecture_ids TEXT NOT NULL,
                text_chars INTEGER NOT NULL,
                chunk_count INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_path TEXT NOT NULL,
                suffix TEXT NOT NULL,
                topics TEXT NOT NULL,
                text_chars INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS knowledge_points (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                lecture_ids TEXT NOT NULL,
                asset_count INTEGER NOT NULL
            );

            -- ===== 学习行为表 =====
            CREATE TABLE IF NOT EXISTS learning_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learner_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learner_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                score REAL NOT NULL,
                total INTEGER NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- ===== 学习记录表（用于日历打卡） =====
            CREATE TABLE IF NOT EXISTS learning_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                date TEXT NOT NULL,
                study_minutes INTEGER DEFAULT 0,
                completed_lectures INTEGER DEFAULT 0,
                accuracy REAL DEFAULT 0,
                is_logged_in INTEGER DEFAULT 0,
                UNIQUE(user_id, date)
            );

            -- ===== 每日计划任务表 =====
            CREATE TABLE IF NOT EXISTS daily_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                date TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'custom',
                is_done INTEGER DEFAULT 0
            );

            -- ===== 笔记系统表 =====
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                lecture_id INTEGER NOT NULL,
                category TEXT DEFAULT 'course',
                title TEXT DEFAULT '',
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_notes_user_lecture ON notes(user_id, lecture_id);
            CREATE INDEX IF NOT EXISTS idx_notes_category ON notes(category);

            -- ===== AI 对话历史表 =====
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_chat_user_session ON chat_history(user_id, session_id);
            CREATE INDEX IF NOT EXISTS idx_chat_created_at ON chat_history(created_at);

            -- ===== 用户反馈表 =====
            CREATE TABLE IF NOT EXISTS chat_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER DEFAULT 1,
                feedback_type TEXT NOT NULL CHECK(feedback_type IN ('helpful', 'not_helpful', 'needs_improvement')),
                comment TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_feedback_chat_id ON chat_feedback(chat_id);

            -- ===== 用户表（认证用） =====
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login_at TEXT DEFAULT NULL
            );

            -- ===== 教师设置表（key-value 配置） =====
            CREATE TABLE IF NOT EXISTS teacher_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT '',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- 默认功能开关（INSERT OR IGNORE 避免重启覆盖）
            INSERT OR IGNORE INTO teacher_settings (key, value) VALUES ('feature_profile_building', 'true');
            INSERT OR IGNORE INTO teacher_settings (key, value) VALUES ('feature_multi_agent_generation', 'true');
            INSERT OR IGNORE INTO teacher_settings (key, value) VALUES ('feature_path_planning', 'true');
            INSERT OR IGNORE INTO teacher_settings (key, value) VALUES ('feature_intelligent_tutoring', 'true');
            INSERT OR IGNORE INTO teacher_settings (key, value) VALUES ('feature_assessment', 'true');

            -- ===== [NEW] 用户画像表（存储兴趣、擅长、薄弱、提升目标） =====
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                interested_topics TEXT DEFAULT '[]',
                strong_topics TEXT DEFAULT '[]',
                weak_topics TEXT DEFAULT '[]',
                improvement_goals TEXT DEFAULT '[]',
                has_completed_guide INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        seed_reference_data(conn)
        _ensure_default_admin(conn)


def seed_reference_data(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO courses(id, title, description) VALUES (?, ?, ?)",
        (
            "python-data-analysis",
            "Python数据分析实战",
            "从零基础到数据科学家的系统学习路径，覆盖Python编程、NumPy/Pandas数据处理、数据可视化、机器学习基础与工业级部署。",
        ),
    )

    kb_index = _read_json(settings.kb_path / "index.json", {"lectures": []})
    for lecture in kb_index.get("lectures", []):
        conn.execute(
            "INSERT OR REPLACE INTO lectures(id, title, dir, file) VALUES (?, ?, ?, ?)",
            (lecture["id"], lecture["title"], lecture["dir"], lecture["file"]),
        )

    experiments = _read_json(
        settings.kb_path / "assets" / "experiments.json",
        {"experiments": []},
    )
    for lab in experiments.get("experiments", []):
        conn.execute(
            """
            INSERT OR REPLACE INTO labs
            (id, title, category, source_path, suffix, topics, lecture_ids, text_chars, chunk_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lab["id"],
                lab["title"],
                lab["category"],
                lab["source_path"],
                lab["suffix"],
                json.dumps(lab.get("topics", []), ensure_ascii=False),
                json.dumps(lab.get("lecture_ids", []), ensure_ascii=False),
                lab.get("text_chars", 0),
                lab.get("chunk_count", 0),
            ),
        )

    datasets = _read_json(settings.kb_path / "assets" / "datasets.json", {"datasets": []})
    for dataset in datasets.get("datasets", []):
        conn.execute(
            """
            INSERT OR REPLACE INTO datasets
            (id, title, source_path, suffix, topics, text_chars)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                dataset["id"],
                dataset["title"],
                dataset["source_path"],
                dataset["suffix"],
                json.dumps(dataset.get("topics", []), ensure_ascii=False),
                dataset.get("text_chars", 0),
            ),
        )

    topic_assets: dict[str, dict[str, Any]] = {}
    for lab in experiments.get("experiments", []):
        for topic in lab.get("topics", []):
            bucket = topic_assets.setdefault(topic, {"lecture_ids": set(), "asset_count": 0})
            bucket["asset_count"] += 1
            bucket["lecture_ids"].update(lab.get("lecture_ids", []))
    for topic, info in topic_assets.items():
        point_id = topic.lower().replace(" ", "-")
        conn.execute(
            """
            INSERT OR REPLACE INTO knowledge_points(id, name, lecture_ids, asset_count)
            VALUES (?, ?, ?, ?)
            """,
            (
                point_id,
                topic,
                json.dumps(sorted(info["lecture_ids"]), ensure_ascii=False),
                info["asset_count"],
            ),
        )


def _ensure_default_admin(conn: sqlite3.Connection) -> None:
    """创建默认管理员账号（如果不存在）"""
    from app.core.security import get_password_hash

    cursor = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    if cursor.fetchone() is None:
        hashed = get_password_hash("admin123")
        conn.execute(
            "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
            ("admin", hashed, "admin"),
        )


def list_labs(topic: str | None = None, category: str | None = None) -> list[dict]:
    query = "SELECT * FROM labs"
    conditions: list[str] = []
    params: list[str] = []
    if topic:
        conditions.append("topics LIKE ?")
        params.append(f"%{topic}%")
    if category:
        conditions.append("category = ?")
        params.append(category)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY category, title"
    with get_connection() as conn:
        return [_row_to_dict(row) for row in conn.execute(query, params).fetchall()]


def get_lab(lab_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM labs WHERE id = ?", (lab_id,)).fetchone()
    if not row:
        return None
    lab = _row_to_dict(row)
    chunks = get_lab_chunks(lab_id)
    lab["chunks"] = chunks
    lab["content"] = "\n\n".join(chunk["text"] for chunk in chunks)
    lab["content_preview"] = lab["content"][:4000]
    return lab


def get_lab_chunks(lab_id: str) -> list[dict]:
    chunks_path = settings.kb_path / "assets" / "chunks.jsonl"
    if not chunks_path.exists():
        return []

    chunks: list[dict] = []
    with chunks_path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            chunk = json.loads(line)
            if chunk.get("asset_id") == lab_id:
                chunks.append({
                    "id": chunk.get("id"),
                    "chunk_index": chunk.get("chunk_index", 0),
                    "title": chunk.get("title", ""),
                    "text": chunk.get("text", ""),
                })
    chunks.sort(key=lambda item: item["chunk_index"])
    return chunks


def list_datasets() -> list[dict]:
    with get_connection() as conn:
        return [_row_to_dict(row) for row in conn.execute("SELECT * FROM datasets ORDER BY title")]


def list_knowledge_points() -> list[dict]:
    with get_connection() as conn:
        return [
            _row_to_dict(row)
            for row in conn.execute("SELECT * FROM knowledge_points ORDER BY asset_count DESC, name")
        ]