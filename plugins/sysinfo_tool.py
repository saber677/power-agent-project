"""
系统信息工具 - 获取系统基本信息
"""
import sys
import platform
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from power_agent import Tool


class SystemInfoTool(Tool):
    name = "sysinfo"
    description = "获取系统信息（操作系统、Python版本等）"

    def execute(self, **kwargs) -> str:
        info = [
            f"系统: {platform.system()} {platform.release()}",
            f"架构: {platform.machine()}",
            f"Python: {platform.python_version()}",
            f"主机名: {platform.node()}",
        ]
        return "\n".join(info)
