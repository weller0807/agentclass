import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
KEY = os.getenv("JUHE_WEATHER_KEY")

@tool
def get_weather(city: str) -> str:
    """查询城市实时天气"""
    d = requests.get("https://apis.juhe.cn/simpleWeather/query",
                     params={"key": KEY, "city": city}, timeout=15).json()
    if d["error_code"] != 0:
        return f"{city}：{d['reason']}"
    r = d["result"]["realtime"]
    return f"{r['info']} {r['temperature']}℃ {r['direct']}{r['power']}"

def weather(state):
    idx = state["idx"]
    row = state["table_rows"][idx]
    text = get_weather.invoke({"city": row["city"]})
    rows = [dict(r) for r in state["table_rows"]]
    rows[idx]["weather"] = text
    return {"table_rows": rows, "match_table": rows, "idx": idx + 1}
