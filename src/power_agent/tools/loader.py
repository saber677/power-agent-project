"""插件动态加载器"""

import importlib.util
from pathlib import Path
from typing import Optional, Union
from .base import Tool
from ..skills.base import Skill


def load_plugin(file_path: Union[str, Path]) -> Optional[Union[Tool, Skill]]:
    """从文件加载一个 Tool 或 Skill 实例"""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"插件文件不存在: {file_path}")

    spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for obj in vars(module).values():
        if isinstance(obj, type) and obj not in (Tool, Skill):
            if issubclass(obj, Tool):
                return obj()
            if issubclass(obj, Skill):
                return obj()
    return None


def scan_plugins(plugins_dir: Union[str, Path]) -> list:
    """扫描目录下所有 .py 插件文件并加载"""
    plugins_dir = Path(plugins_dir)
    if not plugins_dir.exists():
        return []

    loaded = []
    for f in sorted(plugins_dir.glob("*.py")):
        if f.name.startswith("_"):
            continue
        try:
            plugin = load_plugin(f)
            if plugin:
                loaded.append(plugin)
        except Exception as e:
            print(f"⚠️  加载插件失败 {f.name}: {e}")
    return loaded
