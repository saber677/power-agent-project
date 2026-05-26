"""
计算器工具 - 安全计算数学表达式
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from power_agent import Tool


class CalculatorTool(Tool):
    name = "calculator"
    description = "计算数学表达式"

    def execute(self, expression: str = "1+1") -> str:
        try:
            # 只允许数学运算，禁止危险操作
            allowed = set("0123456789+-*/.() ")
            if not all(c in allowed for c in expression):
                return f"❌ 不支持的字符: {expression}"
            result = eval(expression)
            return f"{expression} = {result}"
        except Exception as e:
            return f"❌ 计算错误: {e}"
