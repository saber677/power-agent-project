# Power Agent

一个简洁实用的Python Agent框架，支持动态上下文、工具和技能，运行时动态加载插件和切换大模型。

## 快速开始

### 1. 安装
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置API密钥
```bash
# 在 .env.local 中配置（支持多厂商）
OPENAI_API_KEY=sk-your-key
OPENAI_BASE_URL=https://api.openai.com/v1

DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

QWEN_API_KEY=sk-your-key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 3. 启动对话
```bash
source venv/bin/activate
python3 app/chat.py --mode chat
```

### 4. 启动API服务
```bash
source venv/bin/activate
python3 app/server.py
```

## 项目结构
```
power-agent-project/
├── agent.md                  # Agent人格/规则配置（自动加载为system prompt）
├── src/power_agent/          # 核心框架
│   ├── core/                 # 核心引擎
│   │   ├── agent.py          # Agent主类（编排逻辑）
│   │   ├── config.py         # 配置定义
│   │   └── models.py         # 数据模型
│   ├── llm/                  # LLM层
│   │   ├── client.py         # LLM客户端
│   │   └── function_call.py  # Function Calling逻辑
│   ├── tools/                # 工具系统
│   │   ├── base.py           # Tool基类
│   │   ├── registry.py       # 注册表
│   │   └── loader.py         # 插件加载器
│   ├── skills/               # 技能系统
│   │   └── base.py           # Skill基类
│   ├── memory/               # 记忆与上下文
│   │   └── context.py        # 上下文管理
│   ├── prompts/              # 提示词管理
│   │   └── templates.py      # 系统提示词模板
│   └── exceptions.py         # 异常定义
├── app/                      # 应用入口
│   ├── chat.py               # 交互式对话客户端
│   └── server.py             # HTTP API服务（FastAPI）
├── plugins/                  # 插件目录（自动加载）
├── examples/                 # 示例
│   └── simple_chat.py        # 简洁对话示例
├── tests/                    # 测试
├── pyproject.toml            # 项目配置
└── requirements.txt          # 依赖
```

## agent.md 配置

项目根目录的 `agent.md` 文件用于定义 Agent 的人格、规则和背景知识。启动时自动加载为 system prompt 的一部分，修改后下次对话即生效，无需改代码。

示例：
```markdown
# 角色
你是一个通用私人助理

# 规则
- 用中文回答
- 先给结论后解释
```

## 运行时命令（chat模式）

| 命令 | 说明 |
|------|------|
| `/model <厂商>` | 动态切换大模型（openai/deepseek/qwen/local） |
| `/load <插件名>` | 加载 plugins/ 目录下的插件 |
| `/unload <工具名>` | 卸载已加载的工具 |
| `/tools` | 查看已加载的工具列表 |
| `/exit` | 退出 |

## API服务

```bash
source venv/bin/activate
python3 app/server.py  # 默认端口 8080
```

| 接口 | 方法 | 说明 |
|------|------|------|
| `/tools` | GET | 查看已加载的工具和技能 |
| `/reload` | POST | 增量加载新插件 |
| `/chat` | POST | 对话（支持流式） |

### /chat 接口

**请求体：**
```json
{
  "message": "你好",
  "system_prompt": "可选，额外的system prompt",
  "stream": false
}
```

**非流式响应：**
```json
{"reply": "你好呀！有什么可以帮你的？"}
```

**流式响应（stream: true）：** 返回 SSE 格式
```
data: {"content": "你"}
data: {"content": "好"}
data: {"content": "呀"}
data: [DONE]
```

## 动态切换大模型

```
你: /model deepseek
✅ 已切换到: deepseek | 模型: deepseek-chat | 地址: https://api.deepseek.com/v1
```

## 插件系统

### 编写插件
在 `plugins/` 目录创建 `.py` 文件，继承 `Tool` 或 `Skill`：

```python
# plugins/weather_tool.py
from power_agent import Tool

class WeatherTool(Tool):
    name = "weather"
    description = "查询天气"

    def execute(self, city: str = "深圳") -> str:
        return f"{city}今天晴，28°C"
```

Skill 支持 `can_handle()` 方法实现精确路由：

```python
from power_agent import Skill

class MathSkill(Skill):
    name = "math"
    description = "数学计算"

    def can_handle(self, task: str) -> bool:
        return any(kw in task for kw in ['计算', '加', '减', '乘', '除'])

    def execute(self, task: str, **kwargs):
        # 处理数学任务
        pass
```

### 核心API
```python
from power_agent import PowerAgent, Tool, Skill

agent = PowerAgent()

# 上下文管理（会自动注入到LLM对话中）
agent.add_context("user", "张三")
agent.get_context("user")

# 工具执行
agent.register_tool(MyTool())
agent.execute_tool("my_tool", param="value")

# 对话（带Function Calling + agent.md + 动态context）
response = agent.chat("帮我查一下天气")

# 动态切换LLM
agent.set_llm(provider="deepseek", api_key="sk-xxx", model="deepseek-chat")
```
