"""
Power Agent 异常类
"""

from typing import Any, Optional


class PowerAgentError(Exception):
    """Power Agent 基础异常类"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(message)


class ToolError(PowerAgentError):
    """工具执行异常"""
    pass


class SkillError(PowerAgentError):
    """技能执行异常"""
    pass


class ContextError(PowerAgentError):
    """上下文管理异常"""
    pass


class RegistryError(PowerAgentError):
    """注册表异常"""
    pass


class ValidationError(PowerAgentError):
    """数据验证异常"""
    pass


class NotFoundError(PowerAgentError):
    """未找到资源异常"""
    pass


class DuplicateError(PowerAgentError):
    """重复资源异常"""
    pass
