"""技能基类"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from ..exceptions import SkillError

if TYPE_CHECKING:
    from ..memory.context import ContextManager
    from ..tools.base import Tool


class SkillSchema(BaseModel):
    """技能模式定义"""
    name: str
    description: str
    tools: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)


class Skill(ABC):
    """技能基类"""
    name: str = ""
    description: str = ""

    def __init__(self, context: Optional["ContextManager"] = None):
        self.context = context
        self._tools: Dict[str, "Tool"] = {}

    def get_schema(self) -> SkillSchema:
        return SkillSchema(name=self.name, description=self.description,
                           tools=list(self._tools.keys()), capabilities=self._get_capabilities())

    def _get_capabilities(self) -> List[str]:
        return []

    def register_tool(self, tool: "Tool") -> None:
        from ..tools.base import Tool as ToolClass
        if tool.name in self._tools:
            raise SkillError(f"工具 '{tool.name}' 已存在于技能 '{self.name}' 中")
        if self.context:
            tool.context = self.context
        self._tools[tool.name] = tool

    def unregister_tool(self, tool_name: str) -> None:
        if tool_name not in self._tools:
            raise SkillError(f"工具 '{tool_name}' 不存在于技能 '{self.name}' 中")
        del self._tools[tool_name]

    def get_tool(self, tool_name: str) -> Optional["Tool"]:
        return self._tools.get(tool_name)

    def list_tools(self) -> List["Tool"]:
        return list(self._tools.values())

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self._tools

    @abstractmethod
    def execute(self, task: str, **kwargs) -> Any:
        pass

    def can_handle(self, task: str) -> bool:
        """判断该技能是否能处理此任务，子类可覆盖实现精确匹配"""
        return True

    def __call__(self, task: str, **kwargs) -> Any:
        return self.execute(task, **kwargs)


class CompositeSkill(Skill):
    """组合技能"""

    def __init__(self, name: str, description: str, context: Optional["ContextManager"] = None):
        super().__init__(context)
        self._name = name
        self._description = description
        self._sub_skills: Dict[str, Skill] = {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def register_sub_skill(self, skill: "Skill") -> None:
        if skill.name in self._sub_skills:
            raise SkillError(f"子技能 '{skill.name}' 已存在于组合技能 '{self.name}' 中")
        if self.context:
            skill.context = self.context
        self._sub_skills[skill.name] = skill

    def get_sub_skill(self, skill_name: str) -> Optional["Skill"]:
        return self._sub_skills.get(skill_name)

    def execute(self, task: str, **kwargs) -> Any:
        for skill in self._sub_skills.values():
            try:
                result = skill.execute(task, **kwargs)
                if result is not None:
                    return result
            except Exception:
                continue
        raise SkillError(f"组合技能 '{self.name}' 无法处理任务: {task}")
