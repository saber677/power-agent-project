"""Function Calling 构建与执行"""

import json
import inspect
import re
from typing import Any, Dict, List, Optional, get_type_hints
from ..tools.base import Tool


def _python_type_to_json_schema(annotation) -> Dict[str, Any]:
    """将 Python 类型注解转换为 JSON Schema"""
    if annotation is inspect.Parameter.empty or annotation is None:
        return {"type": "string"}

    origin = getattr(annotation, "__origin__", None)

    # Optional[X] -> X 的 schema
    if origin is type(None):
        return {"type": "string"}
    if origin is not None:
        args = getattr(annotation, "__args__", ())
        # Optional[X] = Union[X, None]
        if origin is type(None):
            return {"type": "string"}
        try:
            from typing import Union
            if origin is Union:
                non_none = [a for a in args if a is not type(None)]
                if len(non_none) == 1:
                    return _python_type_to_json_schema(non_none[0])
                return {"type": "string"}
        except Exception:
            pass
        # List[X]
        if origin is list:
            item_schema = _python_type_to_json_schema(args[0]) if args else {"type": "string"}
            return {"type": "array", "items": item_schema}
        # Dict[K, V]
        if origin is dict:
            return {"type": "object"}

    # 基本类型
    type_map = {
        str: {"type": "string"},
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        list: {"type": "array"},
        dict: {"type": "object"},
    }
    return type_map.get(annotation, {"type": "string"})


def _parse_docstring_params(docstring: str) -> Dict[str, str]:
    """从 docstring 提取参数描述"""
    if not docstring:
        return {}
    params = {}
    # 匹配 :param name: description 或 Args: 下的 name: description
    for match in re.finditer(r":param\s+(\w+):\s*(.+)", docstring):
        params[match.group(1)] = match.group(2).strip()
    # 匹配 Google style: name: description (缩进的行)
    in_args = False
    for line in docstring.split("\n"):
        stripped = line.strip()
        if stripped.lower().startswith("args:"):
            in_args = True
            continue
        if in_args:
            if not stripped or (not line.startswith(" ") and not line.startswith("\t")):
                in_args = False
                continue
            match = re.match(r"(\w+)\s*(?:\(.+?\))?\s*:\s*(.+)", stripped)
            if match:
                params[match.group(1)] = match.group(2).strip()
    return params


def build_tool_schemas(tools: List[Tool]) -> List[Dict[str, Any]]:
    """将已注册工具转换为 OpenAI function calling 格式"""
    schemas = []
    for tool in tools:
        sig = inspect.signature(tool.execute)
        # 尝试获取 type hints
        try:
            hints = get_type_hints(tool.execute)
        except Exception:
            hints = {}
        # 从 docstring 提取参数描述
        param_docs = _parse_docstring_params(tool.execute.__doc__ or "")

        properties = {}
        required = []
        for name, param in sig.parameters.items():
            if name in ("self", "kwargs", "args"):
                continue
            annotation = hints.get(name, param.annotation)
            prop = _python_type_to_json_schema(annotation)
            # 添加参数描述
            if name in param_docs:
                prop["description"] = param_docs[name]
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
    temperature = kwargs.pop("temperature", 0.7)

    response = llm.chat_with_tools(messages, functions, temperature=temperature, **kwargs)

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

        response = llm.chat_with_tools(messages, functions, temperature=temperature, **kwargs)

    if hasattr(response, 'choices') and response.choices:
        return response.choices[0].message.content or ""
    return str(response)
