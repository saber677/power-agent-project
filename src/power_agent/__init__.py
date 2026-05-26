"""
Power Agent - 一个具有动态上下文、工具和技能功能的Python Agent框架
"""

__version__ = "0.1.0"
__author__ = "AI_KIRO"

from .core import PowerAgent, AgentConfig, ExecutionResult
from .memory import ContextManager, ContextItem
from .tools import Tool, FunctionTool, DynamicTool, ToolSchema, Registry, load_plugin, scan_plugins
from .skills import Skill, CompositeSkill, SkillSchema
from .llm import LLMClient, create_llm_client
from .exceptions import (
    PowerAgentError, ToolError, SkillError, ContextError,
    RegistryError, ValidationError, NotFoundError, DuplicateError
)

__all__ = [
    # 主类
    "PowerAgent", "AgentConfig", "ExecutionResult",
    # 上下文
    "ContextManager", "ContextItem",
    # 工具
    "Tool", "FunctionTool", "DynamicTool", "ToolSchema",
    # 技能
    "Skill", "CompositeSkill", "SkillSchema",
    # LLM
    "LLMClient", "create_llm_client",
    # 插件
    "load_plugin", "scan_plugins",
    # 注册表
    "Registry",
    # 异常
    "PowerAgentError", "ToolError", "SkillError", "ContextError",
    "RegistryError", "ValidationError", "NotFoundError", "DuplicateError",
]
