"""
基础测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from power_agent import PowerAgent, Tool, Skill, ContextManager


class TestTool(Tool):
    name = "test_tool"
    description = "测试工具"
    
    def execute(self, input_data: str) -> str:
        return f"处理: {input_data}"


class TestSkill(Skill):
    name = "test_skill"
    description = "测试技能"
    
    def execute(self, task: str, **kwargs) -> str:
        return f"技能处理: {task}"


def test_context_manager():
    """测试上下文管理器"""
    context = ContextManager()
    
    # 测试添加
    context.add("key1", "value1", description="测试键1")
    assert "key1" in context
    assert context.get("key1") == "value1"
    
    # 测试更新
    context.update("key1", value="new_value")
    assert context.get("key1") == "new_value"
    
    # 测试移除
    context.remove("key1")
    assert "key1" not in context
    
    # 测试清空
    context.add("key2", "value2")
    context.clear()
    assert len(context) == 0


def test_tool_registration():
    """测试工具注册"""
    agent = PowerAgent()
    tool = TestTool()
    
    # 注册工具
    agent.register_tool(tool)
    assert agent.registry.has_tool("test_tool")
    
    # 执行工具
    result = agent.execute_tool("test_tool", input_data="测试数据")
    assert result.success
    assert "处理: 测试数据" in result.result
    
    # 注销工具
    agent.unregister_tool("test_tool")
    assert not agent.registry.has_tool("test_tool")


def test_skill_registration():
    """测试技能注册"""
    agent = PowerAgent()
    skill = TestSkill()
    
    # 注册技能
    agent.register_skill(skill)
    assert agent.registry.has_skill("test_skill")
    
    # 执行技能
    result = agent.execute_skill("test_skill", "测试任务")
    assert result.success
    assert "技能处理: 测试任务" in result.result
    
    # 注销技能
    agent.unregister_skill("test_skill")
    assert not agent.registry.has_skill("test_skill")


def test_dynamic_tool():
    """测试动态工具"""
    agent = PowerAgent()
    
    # 定义动态函数
    def dynamic_func(name: str) -> str:
        return f"Hello, {name}!"
    
    # 注册动态工具
    agent.register_dynamic_tool(
        name="greet",
        description="问候工具",
        executor=dynamic_func,
        parameters={"name": {"type": "str", "description": "姓名"}}
    )
    
    # 执行动态工具
    result = agent.execute_tool("greet", name="World")
    assert result.success
    assert result.result == "Hello, World!"


def test_context_integration():
    """测试上下文集成"""
    agent = PowerAgent()
    
    # 添加上下文
    agent.add_context("api_key", "test_key_123", description="API密钥")
    agent.add_context("max_retries", 3, description="最大重试次数")
    
    # 获取上下文
    api_key = agent.get_context("api_key")
    max_retries = agent.get_context("max_retries")
    
    assert api_key == "test_key_123"
    assert max_retries == 3
    
    # 更新上下文
    agent.update_context("max_retries", value=5)
    assert agent.get_context("max_retries") == 5
    
    # 移除上下文
    agent.remove_context("api_key")
    assert agent.get_context("api_key") is None


def test_agent_stats():
    """测试Agent统计"""
    agent = PowerAgent()
    
    # 注册一些工具和技能
    agent.register_tool(TestTool())
    agent.register_skill(TestSkill())
    
    # 添加上下文
    agent.add_context("test_key", "test_value")
    
    # 执行一些操作
    agent.execute_tool("test_tool", input_data="test1")
    agent.execute_skill("test_skill", "test2")
    
    # 获取统计
    stats = agent.stats()
    
    assert stats["tools_count"] == 1
    assert stats["skills_count"] == 1
    assert stats["context_count"] == 1
    assert stats["execution_count"] == 2
    assert stats["success_count"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
