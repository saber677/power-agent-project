"""
时间工具 - 获取当前时间和日期
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from power_agent import Tool
from datetime import datetime


class TimeTool(Tool):
    name = "time"
    description = "获取当前时间和日期"

    def execute(self, format: str = "%Y-%m-%d %H:%M:%S") -> str:
        return f"当前时间: {datetime.now().strftime(format)}"
