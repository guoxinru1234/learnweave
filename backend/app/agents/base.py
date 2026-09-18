"""Agent 基类 —— 所有 LearnWeave 专业 Agent 的抽象基类。

每个 Agent 拥有：
- 角色定义（system prompt）
- 统一的 LLMClient（不再各自创建 openai.OpenAI）
- 独立记忆（per-session key-value 存储）
- 共享状态读写能力（通过 execute(state) -> dict 更新）
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..core.llm import get_llm_client, LLMClient


class BaseAgent(ABC):
    """LearnWeave 多智能体系统的 Agent 基类。

    子类只需实现 execute() 方法，即可被 UnifiedOrchestrator 编排。
    """

    def __init__(self, name: str, role_prompt: str):
        self.name = name
        self.role_prompt = role_prompt
        self.llm: LLMClient = get_llm_client()
        self._memory: Dict[str, Any] = {}

    # ---- 子类必须实现 ----

    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行本 Agent 的任务。

        Args:
            state: 共享状态字典（LearnWeaveState），包含所有前置 Agent 的输出

        Returns:
            本 Agent 的输出字典，将被合并到共享状态中。
            例如 DocAgent 返回 {"lecture_doc": {...}}
        """
        ...

    # ---- LLM 调用 ----

    async def _call_llm(self, user_prompt: str, temperature: float = 0.7,
                        max_tokens: int = 2048) -> str:
        """异步调用 LLM，自动附加本 Agent 的角色 system prompt。"""
        messages = [
            {"role": "system", "content": self.role_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self.llm.chat(messages, temperature, max_tokens)

    def _call_llm_sync(self, user_prompt: str, temperature: float = 0.7,
                       max_tokens: int = 2048) -> str:
        """同步调用 LLM（用于同步上下文中，如非 LangGraph 的旧路径）。"""
        messages = [
            {"role": "system", "content": self.role_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.llm.chat_sync(messages, temperature, max_tokens)

    # ---- 记忆机制 ----

    def remember(self, key: str, value: Any):
        """存储跨调用的记忆（同一 session 内有效）。"""
        self._memory[key] = value

    def recall(self, key: str, default: Any = None) -> Any:
        """读取记忆。"""
        return self._memory.get(key, default)

    def clear_memory(self):
        """清除本 Agent 的所有记忆。"""
        self._memory.clear()

    # ---- 工具方法 ----

    def _get_mode_config(self, mode: str) -> dict:
        """获取学习模式配置。"""
        from ..routers.agent import MODE_CONFIG
        return MODE_CONFIG.get(mode, MODE_CONFIG["study"])

    def log(self, message: str):
        """Agent 日志（供调试用）。"""
        print(f"[{self.name}] {message}")
