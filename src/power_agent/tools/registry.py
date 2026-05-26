"""注册表管理"""

from typing import Dict, List, Optional, Any, Callable
from .base import Tool, FunctionTool, DynamicTool
from ..skills.base import Skill
from ..memory.context import ContextManager
from ..exceptions import DuplicateError, NotFoundError


class Registry:
    """注册表管理器"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._skills: Dict[str, Skill] = {}
        self._context = ContextManager()

    # 工具管理
    def register_tool(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise DuplicateError(f"工具 '{tool.name}' 已注册")
        tool.context = self._context
        self._tools[tool.name] = tool

    def register_function_tool(self, func: Callable, name: Optional[str] = None,
                               description: Optional[str] = None) -> None:
        tool = FunctionTool(func, name, description, self._context)
        self.register_tool(tool)

    def register_dynamic_tool(self, name: str, description: str, executor: Callable,
                              parameters: Optional[Dict[str, Any]] = None,
                              returns: Optional[Dict[str, Any]] = None) -> None:
        tool = DynamicTool(name, description, executor, self._context, parameters, returns)
        self.register_tool(tool)

    def unregister_tool(self, tool_name: str) -> None:
        if tool_name not in self._tools:
            raise NotFoundError(f"工具 '{tool_name}' 未注册")
        del self._tools[tool_name]

    def get_tool(self, tool_name: str) -> Tool:
        tool = self._tools.get(tool_name)
        if not tool:
            raise NotFoundError(f"工具 '{tool_name}' 未注册")
        return tool

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self._tools

    # 技能管理
    def register_skill(self, skill: Skill) -> None:
        if skill.name in self._skills:
            raise DuplicateError(f"技能 '{skill.name}' 已注册")
        skill.context = self._context
        self._skills[skill.name] = skill

    def unregister_skill(self, skill_name: str) -> None:
        if skill_name not in self._skills:
            raise NotFoundError(f"技能 '{skill_name}' 未注册")
        del self._skills[skill_name]

    def get_skill(self, skill_name: str) -> Skill:
        skill = self._skills.get(skill_name)
        if not skill:
            raise NotFoundError(f"技能 '{skill_name}' 未注册")
        return skill

    def list_skills(self) -> List[Skill]:
        return list(self._skills.values())

    def has_skill(self, skill_name: str) -> bool:
        return skill_name in self._skills

    # 上下文管理
    @property
    def context(self) -> ContextManager:
        return self._context

    def add_context(self, key: str, value: Any, description: Optional[str] = None, **metadata) -> None:
        self._context.add(key, value, description, **metadata)

    def get_context(self, key: str, default: Any = None) -> Any:
        return self._context.get(key, default)

    def update_context(self, key: str, value: Any = None, description: Optional[str] = None, **metadata) -> None:
        self._context.update(key, value, description, **metadata)

    def remove_context(self, key: str) -> None:
        self._context.remove(key)

    # 统计
    def stats(self) -> Dict[str, Any]:
        return {
            "tools_count": len(self._tools),
            "skills_count": len(self._skills),
            "context_count": len(self._context),
            "tools": list(self._tools.keys()),
            "skills": list(self._skills.keys()),
            "context_keys": self._context.keys()
        }

    def clear(self) -> None:
        self._tools.clear()
        self._skills.clear()
        self._context.clear()
