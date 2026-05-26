"""Agent配置"""

from typing import Optional
from pydantic import BaseModel


class AgentConfig(BaseModel):
    """Agent配置"""
    name: str = "PowerAgent"
    description: str = "一个具有动态上下文、工具和技能功能的Python Agent"
    max_context_size: int = 1000
    enable_auto_discovery: bool = True
    plugins_path: Optional[str] = None
    # LLM配置
    llm_provider: str = "openai"
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: Optional[str] = None
