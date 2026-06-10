#!/usr/bin/env python3
"""
Power Agent HTTP API 服务（FastAPI + 流式响应）

启动: python3 app/server.py
默认端口: 8080
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv
load_dotenv(project_root / ".env.local")
load_dotenv(project_root / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from power_agent import PowerAgent, scan_plugins, load_plugin, Tool, Skill

# 全局 Agent 实例
agent = PowerAgent()
plugins_dir = project_root / "plugins"
loaded_files = set()

app = FastAPI(title="Power Agent API", version="0.1.0")


def _reload_plugins():
    """增量加载新插件"""
    newly_loaded = []
    for f in sorted(plugins_dir.glob("*.py")):
        if f.name.startswith("_") or f.name in loaded_files:
            continue
        try:
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
for item in _reload_plugins():
    if "error" not in item:
        print(f"  🔧 已加载{item['type']}: {item['name']}")


# ============ 请求模型 ============

class ChatRequest(BaseModel):
    message: str
    system_prompt: Optional[str] = None
    stream: bool = False


# ============ 接口 ============

@app.get("/tools")
def list_tools():
    """查看已加载的工具和技能"""
    tools = agent.registry.list_tools()
    skills = agent.registry.list_skills()
    return {
        "tools": [{"name": t.name, "description": t.description} for t in tools],
        "skills": [{"name": s.name, "description": s.description} for s in skills],
    }


@app.post("/reload")
def reload_plugins():
    """增量加载新插件"""
    result = _reload_plugins()
    if result:
        return {"loaded": result}
    return {"message": "无新插件需要加载"}


@app.post("/chat")
def chat(req: ChatRequest):
    """对话接口，支持流式和非流式"""
    if req.stream:
        return StreamingResponse(_stream_chat(req.message, req.system_prompt), media_type="text/event-stream")
    try:
        reply = agent.chat(req.message, system_prompt=req.system_prompt)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _stream_chat(message: str, system_prompt: Optional[str] = None):
    """SSE 流式返回"""
    import json
    from power_agent.llm.function_call import build_tool_schemas

    # 构建 messages
    messages = []
    final_system = agent._build_system_prompt(system_prompt)
    if final_system:
        messages.append({"role": "system", "content": final_system})
    messages.extend(agent._chat_history)
    messages.append({"role": "user", "content": message})

    tools = agent.registry.list_tools()
    tool_schemas = build_tool_schemas(tools) if tools else None

    # 如果有工具，先走 function calling 多轮交互（非流式），直到不再需要工具
    if tool_schemas:
        max_rounds = 5
        for _ in range(max_rounds):
            response = agent.llm.chat_with_tools(messages, tool_schemas)
            if not hasattr(response, 'choices') or not response.choices:
                break
            choice = response.choices[0]
            if choice.finish_reason != "tool_calls" or not choice.message.tool_calls:
                break

            # 执行工具调用
            messages.append(choice.message)
            for tool_call in choice.message.tool_calls:
                func_name = tool_call.function.name
                try:
                    func_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    func_args = {}
                try:
                    tool = agent.registry.get_tool(func_name)
                    result = tool.execute(**func_args)
                except Exception as e:
                    result = f"工具调用失败: {e}"
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                })

    # 最后一轮：流式输出
    try:
        full_reply = ""
        for chunk in agent.llm.stream_chat_completion(messages):
            full_reply += chunk
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        agent._chat_history.append({"role": "user", "content": message})
        agent._chat_history.append({"role": "assistant", "content": full_reply})
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    print(f"\n🚀 Power Agent API 服务启动中...")
    print(f"📋 接口:")
    print(f"  GET  /tools   - 查看已加载的工具")
    print(f"  POST /reload  - 增量加载新插件")
    print(f"  POST /chat    - 对话（支持 stream: true 流式返回）\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
