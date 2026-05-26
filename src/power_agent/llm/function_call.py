"""Function Calling 构建与执行"""

import json
import inspect
from typing import Any, Dict, List
from ..tools.base import Tool


def build_tool_schemas(tools: List[Tool]) -> List[Dict[str, Any]]:
    """将已注册工具转换为 OpenAI function calling 格式"""
    schemas = []
    for tool in tools:
        sig = inspect.signature(tool.execute)
        properties = {}
        required = []
        for name, param in sig.parameters.items():
            if name in ("self", "kwargs"):
                continue
            prop = {"type": "string"}
            if param.annotation == int:
                prop["type"] = "integer"
            elif param.annotation == float:
                prop["type"] = "number"
            elif param.annotation == bool:
                prop["type"] = "boolean"
            properties[name] = prop
            if param.default is inspect.Parameter.empty:
                required.append(name)

        schemas.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            }
        })
    return schemas


def call_with_tools(llm, messages: List[Dict], tools: List[Tool], registry, **kwargs) -> str:
    """执行带工具调用的LLM对话循环"""
    functions = build_tool_schemas(tools) if tools else None

    response = _call_llm(llm, messages, functions, **kwargs)

    max_rounds = 5
    for _ in range(max_rounds):
        if not hasattr(response, 'choices') or not response.choices:
            break
        choice = response.choices[0]
        if choice.finish_reason != "tool_calls" or not choice.message.tool_calls:
            break

        messages.append(choice.message)

        for tool_call in choice.message.tool_calls:
            func_name = tool_call.function.name
            try:
                func_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                func_args = {}

            try:
                tool = registry.get_tool(func_name)
                result = tool.execute(**func_args)
            except Exception as e:
                result = f"工具调用失败: {e}"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result),
            })

        response = _call_llm(llm, messages, functions, **kwargs)

    if hasattr(response, 'choices') and response.choices:
        return response.choices[0].message.content or ""
    return str(response)


def _call_llm(llm, messages, functions=None, **kwargs):
    """调用大模型（带重试）"""
    import time
    params = {
        "model": llm.model,
        "messages": messages,
        "temperature": kwargs.pop("temperature", 0.7),
    }
    if functions:
        params["tools"] = functions
    params.update(kwargs)

    for attempt in range(3):
        try:
            return llm.client.chat.completions.create(**params)
        except (UnicodeDecodeError, Exception) as e:
            if "utf-8" in str(e).lower() or "decode" in str(e).lower():
                if attempt < 2:
                    time.sleep(0.5)
                    continue
            raise
