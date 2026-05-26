"""
简洁实用的对话Agent
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
# 加载环境变量
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env.local")
load_dotenv(Path(__file__).parent.parent / ".env")

from power_agent import PowerAgent, AgentConfig


def main():
    """主函数"""
    print("=== Power Agent 对话 ===\n")

    # 创建Agent（自动从环境变量读取LLM配置）
    agent = PowerAgent()

    # 验证LLM配置
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    if not api_key:
        print("❌ 未设置API密钥！请在 .env.local 中配置：")
        print("   OPENAI_API_KEY=你的密钥")
        print("   OPENAI_BASE_URL=你的API地址")
        print("   OPENAI_MODEL=模型名称")
        return

    print(f"✅ API地址: {base_url}")
    print(f"✅ 模型: {model}")
    print("\n输入 /exit 退出\n")

    # 对话循环
    while True:
        try:
            user_input = input("你: ").strip()
            if not user_input:
                continue
            if user_input == "/exit":
                print("再见！")
                break

            print("思考中...", end="", flush=True)
            response = agent.chat(user_input)
            print(f"\r助手: {response}\n")

        except KeyboardInterrupt:
            print("\n\n退出...")
            break
        except Exception as e:
            print(f"\r❌ 错误: {e}\n")


if __name__ == "__main__":
    main()
