from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx
from shared.config import settings


class LLMStrategy(ABC):
    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        ...
    @abstractmethod
    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        ...


class OpenRouterStrategy(LLMStrategy):
    BASE_URL = settings.OPENROUTER_BASE_URL

    def __init__(self, model: str = settings.LLM_DEFAULT_MODEL):
        self.model = model
        self.api_key = settings.OPENROUTER_API_KEY

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "HTTP-Referer": "https://github.com/backend-platform"}
        payload = {"model": self.model, "messages": messages, "max_tokens": kwargs.get("max_tokens", settings.LLM_MAX_TOKENS), "temperature": kwargs.get("temperature", settings.LLM_TEMPERATURE)}
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.BASE_URL}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "messages": messages, "max_tokens": kwargs.get("max_tokens", settings.LLM_MAX_TOKENS), "temperature": kwargs.get("temperature", settings.LLM_TEMPERATURE), "stream": True}
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.BASE_URL}/chat/completions", headers=headers, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and "[DONE]" not in line:
                        yield line[6:]


class LLMOrchestrator:
    _models: Dict[str, LLMStrategy] = {}

    @classmethod
    def register(cls, model_id: str, strategy: LLMStrategy) -> None:
        cls._models[model_id] = strategy

    @classmethod
    def get(cls, model_id: Optional[str] = None) -> LLMStrategy:
        model_id = model_id or settings.LLM_DEFAULT_MODEL
        strategy = cls._models.get(model_id)
        if not strategy:
            strategy = cls._models.get(settings.LLM_DEFAULT_MODEL)
            if not strategy:
                strategy = OpenRouterStrategy(model_id)
                cls.register(model_id, strategy)
        return strategy

    @classmethod
    async def ensemble_generate(cls, messages: List[Dict[str, str]], model_ids: List[str]) -> Dict[str, Any]:
        import asyncio
        tasks = [cls.get(mid).generate(messages) for mid in model_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        output = {}
        for mid, result in zip(model_ids, results):
            if isinstance(result, Exception):
                output[mid] = {"error": str(result)}
            else:
                choices = result.get("choices", [{}])
                output[mid] = choices[0].get("message", {}).get("content", "") if choices else ""
        return output


LLMOrchestrator.register("openai/gpt-4o", OpenRouterStrategy("openai/gpt-4o"))
LLMOrchestrator.register("anthropic/claude-3.5-sonnet", OpenRouterStrategy("anthropic/claude-3.5-sonnet"))
LLMOrchestrator.register("google/gemini-2.0-flash", OpenRouterStrategy("google/gemini-2.0-flash"))
LLMOrchestrator.register("deepseek/deepseek-chat", OpenRouterStrategy("deepseek/deepseek-chat"))
LLMOrchestrator.register("qwen/qwen-2.5-72b", OpenRouterStrategy("qwen/qwen-2.5-72b"))
