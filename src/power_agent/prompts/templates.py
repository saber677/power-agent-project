"""提示词模板管理"""

# 系统默认提示词
DEFAULT_SYSTEM_PROMPT = """你是一个智能助手，可以使用工具来帮助用户完成任务。
请根据用户的问题，选择合适的工具或直接回答。"""

TOOL_USAGE_PROMPT = """你可以使用以下工具来帮助回答问题。
当需要使用工具时，请调用对应的函数。
如果不需要工具，直接回答即可。"""


def get_system_prompt(custom: str = None, include_tool_hint: bool = True) -> str:
    """获取系统提示词"""
    if custom:
        return custom
    base = DEFAULT_SYSTEM_PROMPT
    if include_tool_hint:
        base += "\n\n" + TOOL_USAGE_PROMPT
    return base
