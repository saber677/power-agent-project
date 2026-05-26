"""LLM客户端"""

import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from ..exceptions import PowerAgentError


class LLMClient:
    """支持多厂商的LLM客户端"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None,
                 model: str = "gpt-3.5-turbo", provider: str = "openai"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or self._get_default_base_url(provider)
        self.model = model
        self.provider = provider
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _get_default_base_url(self, provider: str) -> str:
        defaults = {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "local": "http://localhost:11434/v1",
        }
        return defaults.get(provider, "https://api.openai.com/v1")

    def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7,
                        max_tokens: Optional[int] = None, **kwargs) -> str:
        if not self.api_key:
            raise PowerAgentError("API密钥未设置")
        params = {"model": self.model, "messages": messages, "temperature": temperature, **kwargs}
        if max_tokens:
            params["max_tokens"] = max_tokens
        try:
            response = self.client.chat.completions.create(**params)
            if hasattr(response, 'choices') and response.choices:
                return response.choices[0].message.content
            return str(response)
        except Exception as e:
            raise PowerAgentError(f"LLM调用失败: {e}")

    def stream_chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7, **kwargs):
        if not self.api_key:
            raise PowerAgentError("API密钥未设置")
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=temperature, stream=True, **kwargs
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise PowerAgentError(f"流式调用失败: {e}")


def create_llm_client(provider: str = "openai", api_key: Optional[str] = None, **kwargs) -> LLMClient:
    """创建LLM客户端工厂函数"""
    env_config = {
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": os.getenv("OPENAI_BASE_URL"),
            "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        },
        "anthropic": {
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "base_url": os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"),
            "model": os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
        },
    }
    config = env_config.get(provider, {})
    if api_key:
        config["api_key"] = api_key
    config.update(kwargs)
    return LLMClient(provider=provider, **config)
