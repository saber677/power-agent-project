"""主Agent类"""

from typing import Any, Dict, List, Optional
from ..tools.registry import Registry
from ..tools.base import Tool
from ..skills.base import Skill
from ..llm.client import LLMClient, create_llm_client
from ..llm.function_call import build_tool_schemas, call_with_tools
from ..exceptions import PowerAgentError, NotFoundError
from .config import AgentConfig
from .models import ExecutionResult


class PowerAgent:
    """Power Agent 主类"""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.registry = Registry()
        self._execution_history: List[ExecutionResult] = []
        self._llm: Optional[LLMClient] = None

    @property
    def llm(self) -> LLMClient:
        """获取LLM客户端（懒加载）"""
        if self._llm is None:
            kwargs = {"provider": self.config.llm_provider}
            if self.config.llm_api_key:
                kwargs["api_key"] = self.config.llm_api_key
            if self.config.llm_base_url:
                kwargs["base_url"] = self.config.llm_base_url
            if self.config.llm_model:
                kwargs["model"] = self.config.llm_model
            self._llm = create_llm_client(**kwargs)
        return self._llm

    def set_llm(self, api_key: Optional[str] = None, base_url: Optional[str] = None,
                model: Optional[str] = None, provider: str = "openai") -> None:
        """动态设置/切换LLM配置"""
        self.config.llm_provider = provider
        if api_key:
            self.config.llm_api_key = api_key
        if base_url:
            self.config.llm_base_url = base_url
        if model:
            self.config.llm_model = model
        self._llm = None

    def chat(self, message: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """带 function calling 和上下文记忆的对话方法"""
        if not hasattr(self, '_chat_history'):
            self._chat_history = []

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(self._chat_history)
        messages.append({"role": "user", "content": message})

        tools = self.registry.list_tools()
        reply = call_with_tools(self.llm, messages, tools, self.registry, **kwargs)

        self._chat_history.append({"role": "user", "content": message})
        self._chat_history.append({"role": "assistant", "content": reply})
        return reply

    # 工具管理
    def register_tool(self, tool: Tool) -> None:
        self.registry.register_tool(tool)

    def register_function_tool(self, func, name: Optional[str] = None, description: Optional[str] = None) -> None:
        self.registry.register_function_tool(func, name, description)

    def register_dynamic_tool(self, name: str, description: str, executor,
                              parameters: Optional[Dict[str, Any]] = None,
                              returns: Optional[Dict[str, Any]] = None) -> None:
        self.registry.register_dynamic_tool(name, description, executor, parameters, returns)

    def unregister_tool(self, tool_name: str) -> None:
        self.registry.unregister_tool(tool_name)

    def get_tool(self, tool_name: str) -> Tool:
        return self.registry.get_tool(tool_name)

    def list_tools(self) -> List[Tool]:
        return self.registry.list_tools()

    # 技能管理
    def register_skill(self, skill: Skill) -> None:
        self.registry.register_skill(skill)

    def unregister_skill(self, skill_name: str) -> None:
        self.registry.unregister_skill(skill_name)

    def get_skill(self, skill_name: str) -> Skill:
        return self.registry.get_skill(skill_name)

    def list_skills(self) -> List[Skill]:
        return self.registry.list_skills()

    # 上下文管理
    def add_context(self, key: str, value: Any, description: Optional[str] = None, **metadata) -> None:
        self.registry.add_context(key, value, description, **metadata)

    def get_context(self, key: str, default: Any = None) -> Any:
        return self.registry.get_context(key, default)

    def update_context(self, key: str, value: Any = None, description: Optional[str] = None, **metadata) -> None:
        self.registry.update_context(key, value, description, **metadata)

    def remove_context(self, key: str) -> None:
        self.registry.remove_context(key)

    # 执行功能
    def execute_tool(self, tool_name: str, **kwargs) -> ExecutionResult:
        """执行工具"""
        try:
            tool = self.registry.get_tool(tool_name)
            result = tool.execute(**kwargs)
            execution_result = ExecutionResult(success=True, result=result, tool_used=tool_name)
        except Exception as e:
            execution_result = ExecutionResult(success=False, result=None, error=str(e), tool_used=tool_name)
        self._execution_history.append(execution_result)
        return execution_result

    def execute_skill(self, skill_name: str, task: str, **kwargs) -> ExecutionResult:
        """执行技能"""
        try:
            skill = self.registry.get_skill(skill_name)
            result = skill.execute(task, **kwargs)
            execution_result = ExecutionResult(success=True, result=result, skill_used=skill_name)
        except Exception as e:
            execution_result = ExecutionResult(success=False, result=None, error=str(e), skill_used=skill_name)
        self._execution_history.append(execution_result)
        return execution_result

    def execute(self, command: str, **kwargs) -> ExecutionResult:
        """智能执行命令 - 自动选择最合适的工具或技能"""
        for skill in self.registry.list_skills():
            try:
                result = skill.execute(command, **kwargs)
                if result is not None:
                    execution_result = ExecutionResult(success=True, result=result, skill_used=skill.name)
                    self._execution_history.append(execution_result)
                    return execution_result
            except Exception:
                continue

        execution_result = ExecutionResult(success=False, result=None, error=f"无法处理命令: {command}")
        self._execution_history.append(execution_result)
        return execution_result

    # 历史与统计
    def get_history(self, limit: Optional[int] = None) -> List[ExecutionResult]:
        if limit:
            return self._execution_history[-limit:]
        return self._execution_history

    def clear_history(self) -> None:
        self._execution_history.clear()

    def stats(self) -> Dict[str, Any]:
        registry_stats = self.registry.stats()
        return {
            **registry_stats,
            "agent_name": self.config.name,
            "execution_count": len(self._execution_history),
            "success_count": sum(1 for r in self._execution_history if r.success),
            "failure_count": sum(1 for r in self._execution_history if not r.success)
        }

    def __call__(self, command: str, **kwargs) -> Any:
        result = self.execute(command, **kwargs)
        if result.success:
            return result.result
        else:
            raise PowerAgentError(f"执行失败: {result.error}")
