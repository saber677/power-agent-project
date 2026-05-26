"""数据模型"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    """执行结果"""
    success: bool
    result: Any
    error: Optional[str] = None
    tool_used: Optional[str] = None
    skill_used: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
