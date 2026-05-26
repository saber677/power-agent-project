#!/usr/bin/env python3
"""
Power Agent HTTP API 服务
提供插件增量加载接口：扫描 plugins/ 目录，只加载新增的插件

启动: python3 app/server.py
默认端口: 8080
"""

import os
import sys
import json
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv
load_dotenv(project_root / ".env.local")
load_dotenv(project_root / ".env")

from power_agent import PowerAgent, scan_plugins, load_plugin, Tool, Skill

# 全局 Agent 实例
agent = PowerAgent()
plugins_dir = project_root / "plugins"

# 记录已加载的插件文件名，用于增量判断
loaded_files = set()


def reload_plugins():
    """增量加载：只加载 plugins/ 中尚未加载的新插件"""
    newly_loaded = []
    for f in sorted(plugins_dir.glob("*.py")):
        if f.name.startswith("_") or f.name in loaded_files:
            continue
        try:
            from power_agent import load_plugin
            plugin = load_plugin(f)
            if plugin:
                if isinstance(plugin, Skill):
                    agent.register_skill(plugin)
                else:
                    agent.register_tool(plugin)
                loaded_files.add(f.name)
                newly_loaded.append({"name": plugin.name, "type": "Skill" if isinstance(plugin, Skill) else "Tool"})
        except Exception as e:
            newly_loaded.append({"name": f.stem, "error": str(e)})
    return newly_loaded


# 启动时加载所有插件
for item in reload_plugins():
    if "error" not in item:
        print(f"  🔧 已加载{item['type']}: {item['name']}")


class APIHandler(BaseHTTPRequestHandler):
    def _json_response(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def do_GET(self):
        # GET /tools - 查看已加载的工具和技能
        if self.path == "/tools":
            tools = agent.registry.list_tools()
            self._json_response(200, {
                "tools": [{"name": t.name, "description": t.description} for t in tools]
            })
        else:
            self._json_response(404, {"error": "未找到接口"})

    def do_POST(self):
        # POST /reload - 增量加载新插件
        if self.path == "/reload":
            result = reload_plugins()
            if result:
                self._json_response(200, {"loaded": result})
            else:
                self._json_response(200, {"message": "无新插件需要加载"})
        else:
            self._json_response(404, {"error": "未找到接口"})

    def log_message(self, format, *args):
        print(f"  [{self.command}] {self.path}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), APIHandler)
    print(f"\n🚀 API服务已启动: http://localhost:{port}")
    print(f"📋 接口:")
    print(f"  GET  /tools   - 查看已加载的工具")
    print(f"  POST /reload  - 增量加载新插件\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
