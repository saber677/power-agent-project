# Power Agent

一个简洁实用的Python Agent框架，支持动态上下文、工具和技能，运行时动态加载插件和切换大模型。

## 快速开始

### 1. 安装
```bash
./install_deps.sh
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
python3 start_agent.py --mode chat
```

## 运行时命令

| 命令 | 说明 |
|------|------|
| `/model <厂商>` | 动态切换大模型（openai/deepseek/qwen/local） |
| `/load <插件名>` | 加载 plugins/ 目录下的插件 |
| `/unload <工具名>` | 卸载已加载的工具 |
| `/tools` | 查看已加载的工具列表 |
| `/exit` | 退出 |

## 动态切换大模型

预设厂商，运行时一键切换（自动读取对应环境变量的 key）：

```
你: /model deepseek
✅ 已切换到: deepseek | 模型: deepseek-chat | 地址: https://api.deepseek.com/v1

你: /model openai
✅ 已切换到: openai | 模型: gpt-4 | 地址: https://api.openai.com/v1
```

也可通过命令行环境变量临时指定：
```bash
OPENAI_MODEL=gpt-4o python3 start_agent.py --mode chat
```

## 插件系统

### 自动加载
启动时自动扫描 `plugins/` 目录，加载所有 Tool 和 Skill。

### 手动加载
运行时通过 `/load` 命令动态加载：
```
你: /load hello_tool
✅ 已加载: hello
```

### 编写插件
在 `plugins/` 目录创建 `.py` 文件，继承 `Tool` 或 `Skill`：

```python
# plugins/weather_tool.py
from power_agent import Tool

class WeatherTool(Tool):
    name = "weather"
    description = "查询天气"

    def execute(self, city: str = "深圳") -> str:
        # 调用天气API...
        return f"{city}今天晴，28°C"
```

放入 `plugins/` 即可，启动自动加载或运行时 `/load weather_tool`。

## 核心特性

### 动态上下文
```python
from power_agent import PowerAgent

agent = PowerAgent()
agent.add_context("user", "张三")
agent.get_context("user")  # 返回 "张三"
```

### 工具系统
```python
from power_agent import Tool

class CalculatorTool(Tool):
    name = "calculator"
    description = "计算器"

    def execute(self, expression: str) -> str:
        return f"结果: {eval(expression)}"

agent.register_tool(CalculatorTool())
agent.execute_tool("calculator", expression="2+3")
```

### 技能系统
```python
from power_agent import Skill

class MathSkill(Skill):
    name = "math"
    description = "数学技能"

    def __init__(self):
        super().__init__()
        self.register_tool(CalculatorTool())

    def execute(self, task: str) -> str:
        if "计算" in task:
            return self.get_tool("calculator").execute(task.replace("计算", ""))
        return "无法处理"

agent.register_skill(MathSkill())
```

## 项目结构
```
power-agent-project/
├── src/power_agent/          # 核心框架
│   ├── plugin_loader.py      # 插件动态加载器
│   └── ...
├── plugins/                  # 插件目录（自动加载）
│   └── hello_tool.py        # 示例插件
├── examples/simple_chat.py   # 简洁对话示例（给别人看）
├── start_agent.py           # 启动脚本（自己用）
├── install_deps.sh          # 安装脚本
└── requirements.txt         # 依赖列表
```

## 扩展
- 添加工具：在 `plugins/` 目录创建 `.py` 文件，继承 `Tool`
- 添加技能：继承 `Skill`，组合多个工具
- 添加厂商：在 `start_agent.py` 的 `PROVIDERS` 字典加一行
