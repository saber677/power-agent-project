#!/usr/bin/env python3
"""
Power Agent 启动脚本
- 内置对话功能，独立运行不依赖 examples/
- 支持 /model 动态切换大模型厂商
- 支持 /load /unload /tools 动态管理插件
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def check_dependencies():
    """检查核心依赖是否已安装"""
    try:
        import openai
        import pydantic
        print(f"✅ OpenAI: {openai.__version__}")
        print(f"✅ Pydantic: {pydantic.__version__}")
        return True
    except ImportError as e:
        print(f"❌ 依赖缺失: {e}")
        print("运行: ./install_deps.sh")
        return False


# ============================================================
# 厂商配置
# 格式: "厂商名": ("默认API地址", "默认模型")
# 对应环境变量: <厂商名大写>_API_KEY, <厂商名大写>_BASE_URL, <厂商名大写>_MODEL
# ============================================================
PROVIDERS = {
    "openai": ("https://api.openai.com/v1", "gpt-4"),
    "deepseek": ("https://api.deepseek.com/v1", "deepseek-chat"),
    "qwen": ("https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen3.7-max"),
    "local": ("http://localhost:11434/v1", "llama3"),
}


def get_provider_config(name: str) -> dict:
    """
    获取厂商配置，优先从环境变量读取，否则使用 PROVIDERS 中的默认值。
    环境变量命名规则: <NAME>_API_KEY, <NAME>_BASE_URL, <NAME>_MODEL
    """
    prefix = name.upper()
    defaults = PROVIDERS.get(name, ("https://api.openai.com/v1", name))
    return {
        "api_key": os.getenv(f"{prefix}_API_KEY") or os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv(f"{prefix}_BASE_URL", defaults[0]),
        "model": os.getenv(f"{prefix}_MODEL", defaults[1]),
    }


def switch_provider(agent, name: str):
    """运行时切换大模型厂商"""
    config = get_provider_config(name)
    if not config["api_key"]:
        print(f"❌ 未找到 {name.upper()}_API_KEY，请在 .env.local 中配置")
        return
    agent.set_llm(
        api_key=config["api_key"],
        base_url=config["base_url"],
        model=config["model"],
        provider=name,
    )
    print(f"✅ 已切换到: {name} | 模型: {config['model']} | 地址: {config['base_url']}")


# ============================================================
# 对话主循环
# ============================================================
def run_chat():
    """运行交互式对话，支持插件动态加载和厂商切换"""
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env.local")
    load_dotenv(project_root / ".env")

    from power_agent import PowerAgent, scan_plugins, load_plugin, Tool, Skill

    print("=== Power Agent 对话 ===\n")
    agent = PowerAgent()

    # --- 启动时自动加载 plugins/ 目录下所有插件 ---
    plugins_dir = project_root / "plugins"
    loaded_plugins = set()  # 记录已加载的文件名，用于增量判断
    for plugin in scan_plugins(plugins_dir):
        if isinstance(plugin, Skill):
            agent.register_skill(plugin)
            print(f"  📦 已加载技能: {plugin.name}")
        elif isinstance(plugin, Tool):
            agent.register_tool(plugin)
            print(f"  🔧 已加载工具: {plugin.name}")
    # 标记所有已加载的文件
    for f in plugins_dir.glob("*.py"):
        if not f.name.startswith("_"):
            loaded_plugins.add(f.name)

    # --- 验证 API 配置 ---
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    if not api_key:
        print("❌ 未设置API密钥！请在 .env.local 中配置：")
        print("   OPENAI_API_KEY=你的密钥")
        return

    print(f"\n✅ API地址: {base_url}")
    print(f"✅ 模型: {model}")
    print(f"📋 可用厂商: {', '.join(PROVIDERS.keys())}")
    print("\n命令: /model <厂商>切换模型 | /load 增量加载插件 | /load <名称>加载指定插件 | /unload <名称>卸载 | /tools 查看 | /exit 退出\n")

    # --- 对话循环 ---
    from prompt_toolkit import PromptSession
    from prompt_toolkit.patch_stdout import patch_stdout
    session = PromptSession()

    while True:
        try:
            with patch_stdout():
                user_input = session.prompt("你: ").strip()
            if not user_input:
                continue

            # /exit - 退出
            if user_input == "/exit":
                print("再见！")
                break

            # /model <厂商名> - 动态切换大模型厂商
            if user_input.startswith("/model"):
                parts = user_input.split()
                if len(parts) < 2:
                    print(f"用法: /model <厂商名>  可选: {', '.join(PROVIDERS.keys())}")
                else:
                    switch_provider(agent, parts[1])
                continue

            # /load <插件名> - 动态加载插件（plugins/ 目录下的 .py 文件）
            if user_input.startswith("/load"):
                parts = user_input.split()
                if len(parts) < 2:
                    # 无参数时执行增量加载（等同于 /reload）
                    loaded = []
                    for f in sorted(plugins_dir.glob("*.py")):
                        if f.name.startswith("_") or f.name in loaded_plugins:
                            continue
                        try:
                            plugin = load_plugin(f)
                            if plugin:
                                ptype = "技能" if isinstance(plugin, Skill) else "工具"
                                if isinstance(plugin, Skill):
                                    agent.register_skill(plugin)
                                else:
                                    agent.register_tool(plugin)
                                loaded_plugins.add(f.name)
                                loaded.append(f"{plugin.name}({ptype})")
                        except Exception as e:
                            print(f"  ⚠️ {f.name}: {e}")
                    if loaded:
                        print(f"✅ 新加载: {', '.join(loaded)}")
                    else:
                        print("无新插件需要加载")
                else:
                    # 指定插件名加载
                    plugin_file = plugins_dir / f"{parts[1]}.py"
                    try:
                        plugin = load_plugin(plugin_file)
                        if plugin:
                            ptype = "技能" if isinstance(plugin, Skill) else "工具"
                            if isinstance(plugin, Skill):
                                agent.register_skill(plugin)
                            else:
                                agent.register_tool(plugin)
                            loaded_plugins.add(plugin_file.name)
                            print(f"✅ 已加载{ptype}: {plugin.name}")
                        else:
                            print(f"❌ 未找到有效的 Tool/Skill: {plugin_file}")
                    except Exception as e:
                        print(f"❌ 加载失败: {e}")
                continue

            # /unload <工具名> - 卸载已加载的工具
            if user_input.startswith("/unload"):
                parts = user_input.split()
                if len(parts) < 2:
                    print("用法: /unload <工具名>")
                else:
                    try:
                        agent.unregister_tool(parts[1])
                        print(f"✅ 已卸载: {parts[1]}")
                    except Exception as e:
                        print(f"❌ 卸载失败: {e}")
                continue

            # /tools - 列出所有已加载的工具
            if user_input == "/tools":
                tools = agent.registry.list_tools()
                if tools:
                    print("📦 已加载工具:")
                    for t in tools:
                        print(f"  - {t.name}: {t.description}")
                else:
                    print("暂无工具")
                continue

            # 正常对话
            print("思考中...", end="", flush=True)
            response = agent.chat(user_input)
            if isinstance(response, bytes):
                response = response.decode("utf-8", errors="replace")
            print(f"\r助手: {response}\n")

        except KeyboardInterrupt:
            print("\n\n退出...")
            break
        except Exception as e:
            import traceback
            print(f"\r❌ 错误: {e}")
            traceback.print_exc()
            print()


def run_test():
    """运行基础功能测试"""
    print("=== 系统测试 ===\n")

    try:
        from power_agent import PowerAgent
        agent = PowerAgent()
        print(f"✅ Agent创建: {agent.config.name}")

        # 测试工具注册和执行
        from power_agent import Tool

        class TestTool(Tool):
            name = "test"
            description = "测试"
            def execute(self, x): return f"测试: {x}"

        agent.register_tool(TestTool())
        result = agent.execute_tool("test", x="hello")
        print(f"✅ 工具测试: {result.result}")

        print("\n🎉 所有测试通过！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")


def main():
    """主函数 - 解析参数并启动对应模式"""
    parser = argparse.ArgumentParser(description="Power Agent 启动器")
    parser.add_argument("--mode", choices=["chat", "test"], default="chat", help="运行模式")
    parser.add_argument("--api-key", help="API密钥")

    args = parser.parse_args()

    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    # 设置API密钥（命令行参数优先）
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
        print(f"✅ API密钥已设置")

    # 运行模式
    if args.mode == "chat":
        run_chat()
    elif args.mode == "test":
        run_test()


if __name__ == "__main__":
    main()
