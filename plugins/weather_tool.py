"""
天气工具 - 查询城市天气（使用 wttr.in 免费API，无需密钥）
"""
import sys
import urllib.request
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from power_agent import Tool


class WeatherTool(Tool):
    name = "weather"
    description = "查询指定城市的当前天气信息"

    def execute(self, city: str = "深圳") -> str:
        try:
            from urllib.parse import quote
            url = f"https://wttr.in/{quote(city)}?format=j1"
            req = urllib.request.Request(url, headers={"Accept-Language": "zh"})
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())

            current = data["current_condition"][0]
            temp = current["temp_C"]
            humidity = current["humidity"]
            desc = current["lang_zh"][0]["value"] if current.get("lang_zh") else current["weatherDesc"][0]["value"]
            wind = current["windspeedKmph"]

            return f"{city}天气: {desc}, 温度{temp}°C, 湿度{humidity}%, 风速{wind}km/h"
        except Exception as e:
            return f"查询天气失败: {e}"
