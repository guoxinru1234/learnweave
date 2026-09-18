"""统一 LLM 客户端 — 支持多提供商、重试、流式"""
import httpx
import json
import asyncio
from typing import Optional, AsyncGenerator
from .config import settings


# ========== 自定义异常 ==========

class LLMError(Exception):
    """LLM 调用失败"""
    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class LLMAuthError(LLMError):
    """认证失败（API Key 错误或未配置）"""
    def __init__(self, message: str):
        super().__init__(message, retryable=False)


class LLMTimeoutError(LLMError):
    """请求超时"""
    def __init__(self, message: str):
        super().__init__(message, retryable=True)


# ========== 提供商配置 ==========

PROVIDERS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "api_key_attr": "deepseek_api_key",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "api_key_attr": "openai_api_key",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
        "api_key_attr": "qwen_api_key",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-flash",
        "api_key_attr": "glm_api_key",
    },
    "moonshot": {
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
        "api_key_attr": "moonshot_api_key",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b",
        "api_key_attr": "groq_api_key",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "default_model": "qwen2.5:7b",
        "api_key_attr": None,  # Ollama 不需要 key
    },
    "xfyun": {
        "base_url": "https://spark-api-open.xf-yun.com/v1",
        "default_model": "lite",
        "api_key_attr": "xfyun_api_password",
    },
    "custom": {
        "base_url": "",
        "default_model": "",
        "api_key_attr": "llm_api_key",
    },
}


# ========== LLM 客户端 ==========

class LLMClient:
    """统一的 LLM 客户端，支持多提供商、自动重试和流式输出"""

    def __init__(self):
        provider = settings.llm_provider or "deepseek"
        if provider not in PROVIDERS:
            print(f"[LLMClient] 未知提供商 '{provider}'，回退到 deepseek")
            provider = "deepseek"

        self.provider = provider
        cfg = PROVIDERS[provider]
        configured_base_urls = {
            "deepseek": settings.deepseek_base_url,
            "openai": settings.openai_base_url,
            "custom": settings.llm_base_url,
        }
        self.base_url = configured_base_urls.get(provider, cfg["base_url"]).rstrip("/")
        self.model = settings.llm_model or cfg["default_model"]

        # 读取 API Key
        key_attr = cfg.get("api_key_attr")
        self.api_key = getattr(settings, key_attr, "") if key_attr else ""

        if not self.base_url:
            raise LLMAuthError("未配置 LLM_BASE_URL，请填写 OpenAI 兼容接口地址")

        self.max_retries = 3
        self.request_timeout = 120.0

    # ---------- 请求构建 ----------

    def _build_payload(self, messages: list[dict], temperature: float = 0.7,
                       max_tokens: int = 2048, stream: bool = False) -> dict:
        return {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key and self.provider != "ollama":
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _classify_error(self, status: int, body: dict) -> LLMError:
        if status in (401, 403):
            return LLMAuthError(f"API 认证失败 ({status})，请检查 {self.provider.upper()} API Key")
        if status == 429:
            return LLMError(f"API 速率限制 ({status})，稍后重试", retryable=True)
        if status >= 500:
            return LLMError(f"API 服务器错误 ({status})", retryable=True)
        msg = body.get("error", {}).get("message", str(body))
        return LLMError(f"API 错误 ({status}): {msg}")

    # ---------- 对话（非流式） ----------

    async def chat(self, messages: list[dict], temperature: float = 0.7,
                   max_tokens: int = 2048) -> str:
        """发送对话请求，返回完整回复"""
        if not self.api_key and self.provider != "ollama":
            raise LLMAuthError(
                f"未配置 {self.provider.upper()} API Key，请在 .env 中设置 "
                f"{PROVIDERS[self.provider]['api_key_attr']}"
            )

        payload = self._build_payload(messages, temperature, max_tokens, stream=False)
        url = f"{self.base_url}/chat/completions"

        last_error = None
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                    resp = await client.post(url, headers=self._headers(), json=payload)

                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"]

                    err = self._classify_error(resp.status_code,
                                               resp.json() if resp.text else {})
                    if not err.retryable or attempt == self.max_retries - 1:
                        raise err
                    last_error = err

            except (LLMError, LLMAuthError, LLMTimeoutError):
                raise
            except httpx.TimeoutException:
                last_error = LLMTimeoutError(
                    f"请求超时 (尝试 {attempt + 1}/{self.max_retries})"
                )
            except Exception as e:
                last_error = LLMError(f"请求失败: {str(e)}", retryable=True)

            if attempt < self.max_retries - 1:
                delay = 2 ** attempt  # 1s, 2s, 4s
                print(f"[LLMClient] 重试 {attempt + 2}/{self.max_retries}，等待 {delay}s...")
                await asyncio.sleep(delay)

        raise last_error or LLMError("未知错误")

    # ---------- 流式对话 ----------

    async def chat_stream(self, messages: list[dict], temperature: float = 0.7,
                          max_tokens: int = 2048) -> AsyncGenerator[str, None]:
        """流式对话，逐 token 产出"""
        if not self.api_key and self.provider != "ollama":
            raise LLMAuthError(
                f"未配置 {self.provider.upper()} API Key"
            )

        payload = self._build_payload(messages, temperature, max_tokens, stream=True)
        url = f"{self.base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=self.request_timeout) as client:
            async with client.stream("POST", url, headers=self._headers(),
                                     json=payload) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise self._classify_error(resp.status_code,
                                               json.loads(body) if body else {})

                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line.strip() != "data: [DONE]":
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk["choices"][0]["delta"]
                            if delta.get("content"):
                                yield delta["content"]
                        except (json.JSONDecodeError, KeyError, IndexError):
                            pass


    # ---------- 同步便捷方法 ----------

    def chat_sync(self, messages: list[dict], temperature: float = 0.7,
                  max_tokens: int = 2048) -> str:
        """同步包装器，供无法使用 async 的场景（如 CourseAgent 同步方法）调用。
        首选异步 chat()；仅在同步上下文中使用此方法。"""
        import concurrent.futures
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 没有运行中的事件循环，直接 asyncio.run
            return asyncio.run(self.chat(messages, temperature, max_tokens))
        # 已有事件循环（如 FastAPI 请求中），在新线程里跑
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run, self.chat(messages, temperature, max_tokens)
            )
            return future.result()

    def chat_stream_sync(self, messages: list[dict], temperature: float = 0.7,
                         max_tokens: int = 2048):
        """同步流式生成器包装器。逐个产出 token 字符串。"""
        import concurrent.futures
        import queue

        async def _collect():
            tokens = []
            async for token in self.chat_stream(messages, temperature, max_tokens):
                tokens.append(token)
            return tokens

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.chat_stream(messages, temperature, max_tokens))

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, _collect())
            return iter(future.result())


# ========== 全局单例 ==========

llm_client = LLMClient()


def get_llm_client() -> LLMClient:
    """获取全局 LLM 客户端实例"""
    return llm_client
