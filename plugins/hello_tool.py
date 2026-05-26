"""
示例插件：Hello工具 - 用于验证插件加载机制
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from power_agent import Tool


class HelloTool(Tool):
    name = "hello"
    description = "打招呼工具，用于测试插件加载"

    def execute(self, name: str = "世界") -> str:
        return f"你好，{name}！插件加载成功 🎉"
