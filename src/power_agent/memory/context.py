"""上下文管理"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from ..exceptions import ContextError


class ContextItem(BaseModel):
    """上下文项"""
    key: str
    value: Any
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContextManager:
    """上下文管理器"""

    def __init__(self):
        self._context: Dict[str, ContextItem] = {}

    def add(self, key: str, value: Any, description: Optional[str] = None, **metadata) -> None:
        if key in self._context:
            raise ContextError(f"上下文键 '{key}' 已存在")
        self._context[key] = ContextItem(key=key, value=value, description=description, metadata=metadata)

    def update(self, key: str, value: Any = None, description: Optional[str] = None, **metadata) -> None:
        if key not in self._context:
            raise ContextError(f"上下文键 '{key}' 不存在")
        item = self._context[key]
        if value is not None:
            item.value = value
        if description is not None:
            item.description = description
        if metadata:
            item.metadata.update(metadata)

    def get(self, key: str, default: Any = None) -> Any:
        item = self._context.get(key)
        return item.value if item else default

    def get_item(self, key: str) -> Optional[ContextItem]:
        return self._context.get(key)

    def remove(self, key: str) -> None:
        if key not in self._context:
            raise ContextError(f"上下文键 '{key}' 不存在")
        del self._context[key]

    def clear(self) -> None:
        self._context.clear()

    def list(self) -> List[ContextItem]:
        return list(self._context.values())

    def keys(self) -> List[str]:
        return list(self._context.keys())

    def __contains__(self, key: str) -> bool:
        return key in self._context

    def __len__(self) -> int:
        return len(self._context)

    def to_dict(self) -> Dict[str, Any]:
        return {key: item.value for key, item in self._context.items()}
