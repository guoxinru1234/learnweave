"""LLM Service — 直接 HTTP 调用 (绕过 openai 库兼容问题)"""
import os, json, httpx
from typing import AsyncGenerator

PROVIDERS = {
    "deepseek": {"base_url": "https://api.deepseek.com/v1", "default_model": "deepseek-chat", "env_key": "DEEPSEEK_API_KEY"},
    "openai": {"base_url": "https://api.openai.com/v1", "default_model": "gpt-4o-mini", "env_key": "OPENAI_API_KEY"},
    "qwen": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "default_model": "qwen-plus", "env_key": "DASHSCOPE_API_KEY"},
    "zhipu": {"base_url": "https://open.bigmodel.cn/api/paas/v4", "default_model": "glm-4-flash", "env_key": "ZHIPU_API_KEY"},
    "moonshot": {"base_url": "https://api.moonshot.cn/v1", "default_model": "moonshot-v1-8k", "env_key": "MOONSHOT_API_KEY"},
    "ollama": {"base_url": "http://localhost:11434/v1", "default_model": "qwen2.5:7b", "env_key": None},
    "groq": {"base_url": "https://api.groq.com/openai/v1", "default_model": "llama-3.3-70b", "env_key": "GROQ_API_KEY"},
    "custom": {"base_url": "", "default_model": "", "env_key": "LLM_API_KEY"},
}

class LLMService:
    def __init__(self, provider: str = None):
        provider = provider or os.getenv("LLM_PROVIDER", "auto")
        if provider == "auto":
            for name, cfg in PROVIDERS.items():
                if cfg["env_key"] and os.getenv(cfg["env_key"]):
                    provider = name; break
            else:
                try: httpx.get("http://localhost:11434", timeout=1); provider = "ollama"
                except: provider = "openai"
        
        self.cfg = PROVIDERS.get(provider, PROVIDERS["openai"])
        self.api_key = os.getenv(self.cfg["env_key"], "") if self.cfg["env_key"] else "ollama"
        self.model = os.getenv("LLM_MODEL", self.cfg["default_model"])
        configured_base = os.getenv("LLM_BASE_URL", "") if provider == "custom" else ""
        self.base_url = (configured_base or self.cfg["base_url"]).rstrip("/")
        self.provider = provider

        if not self.base_url:
            raise ValueError("LLM_PROVIDER=custom 时必须配置 LLM_BASE_URL")

    async def chat(self, messages: list, **kwargs) -> str:
        """发送对话请求"""
        async with httpx.AsyncClient(timeout=60) as client:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            if self.provider == "ollama":
                headers.pop("Authorization", None)
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2000),
                },
                headers=headers,
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: list, **kwargs) -> AsyncGenerator[str, None]:
        """流式对话"""
        async with httpx.AsyncClient(timeout=60) as client:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            if self.provider == "ollama":
                headers.pop("Authorization", None)
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2000),
                    "stream": True,
                },
                headers=headers,
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            chunk = json.loads(line[6:])
                            if chunk["choices"][0]["delta"].get("content"):
                                yield chunk["choices"][0]["delta"]["content"]
                        except:
                            pass

    async def generate_with_context(self, system_prompt: str, user_query: str, context: str) -> str:
        return await self.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"知识库参考:\n{context}\n\n问题: {user_query}"}
        ])

PROMPTS = {
    "tutor": "你是 LearnWeave AI 辅导 Agent，专门辅导「大数据计算集群技术」课程。用中文回答，代码注释用中文，复杂概念先给类比再深入。",
    "profile": "你是 LearnWeave 画像构建 Agent。通过对话了解学习者的知识基础、认知风格、学习节奏、模态偏好、薄弱环节和学习动机，更新 30-100 分的维度分数。",
    "quiz": "你是 LearnWeave 出题 Agent。基于「大数据计算集群技术」生成选择题/填空题/编程题，难度根据掌握度动态调整。",
    "assess": "你是 LearnWeave 评估 Agent。分析答题数据，给出知识点掌握百分比、3个薄弱点和个性化建议。",
}
