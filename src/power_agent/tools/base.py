"""工具基类"""

from typing import Any, Dict, Optional, Callable, TYPE_CHECKING
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from ..exceptions import ToolError

if TYPE_CHECKING:
    from ..memory.context import ContextManager


class ToolSchema(BaseModel):
    """工具模式定义"""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    returns: Dict[str, Any] = Field(default_factory=dict)


class Tool(ABC):
    """工具基类"""
    name: str = ""
    description: str = ""

    def __init__(self, context: Optional["ContextManager"] = None):
        self.context = context

    def get_schema(self) -> ToolSchema:
        return ToolSchema(name=self.name, description=self.description,
                          parameters=self._get_parameters(), returns=self._get_returns())

    def _get_parameters(self) -> Dict[str, Any]:
        return {}

    def _get_returns(self) -> Dict[str, Any]:
        return {}

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass

    def __call__(self, **kwargs) -> Any:
        return self.execute(**kwargs)


class FunctionTool(Tool):
    """函数工具包装器"""

    def __init__(self, func: Callable, name: Optional[str] = None,
                 description: Optional[str] = None, context: Optional["ContextManager"] = None):
        super().__init__(context)
        self.func = func
        self._name = name or func.__name__
        self._description = description or func.__doc__ or ""

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def execute(self, **kwargs) -> Any:
        try:
            return self.func(**kwargs)
        except Exception as e:
            raise ToolError(f"工具执行失败: {e}", details={"tool": self.name, "error": str(e)})


class DynamicTool(Tool):
    """动态工具"""

    def __init__(self, name: str, description: str, executor: Callable,
                 context: Optional["ContextManager"] = None,
                 parameters: Optional[Dict[str, Any]] = None,
                 returns: Optional[Dict[str, Any]] = None):
        super().__init__(context)
        self._name = name
        self._description = description
        self.executor = executor
        self._parameters = parameters or {}
        self._returns = returns or {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def _get_parameters(self) -> Dict[str, Any]:
        return self._parameters

    def _get_returns(self) -> Dict[str, Any]:
        return self._returns

    def execute(self, **kwargs) -> Any:
        try:
            return self.executor(**kwargs)
        except Exception as e:
            raise ToolError(f"动态工具执行失败: {e}", details={"tool": self.name, "error": str(e)})
