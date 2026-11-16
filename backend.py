# -*- coding: utf-8 -*-
"""backend.py —— 后端统一出口：检索 + LangChain 标准链"""
import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from retrieval_demo.data import format_matches, retrieve_matches
import os
from pathlib import Path

from dotenv import load_dotenv
SYSTEM = (
    "你是足球赛程助手。只能根据【赛程数据】回答，禁止编造。"
    "用户可能用简称提问（如“辽宁队”指“辽宁铁人”）。"
    "问“最近/最后/下一场”时按 match_date 取日期最晚的一场，问“最早/第一场”时取日期最早的一场，"
    "不要在命中数据里随便挑一行。"
    "只输出 JSON 对象，含 answer 和 source 两个字段，不要多余文字。"
    "数据里没有就如实说明，source 写“数据中未找到”。"
    "数据里有 weather 字段时，回答里带上比赛地点的天气。"
)
# 使用.env文档存我自己的apikey
load_dotenv(Path(__file__).resolve().parent / ".env")

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("缺少 DEEPSEEK_API_KEY，请检查 .env 文件")

llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=api_key,
    temperature=0,
    model_kwargs={"response_format": {"type": "json_object"}},
)

PROMPT = ChatPromptTemplate.from_messages([
    ("system", "{system_prompt}"),
    ("human", "{question}"),
])

chain = PROMPT | llm


def chat(state):
    """LangGraph 节点：吃 state，返回要写回 state 的字段"""
    question = state["question"]
    if not question.strip():
        return {"answer": "", "match_table": []}
    rows = state.get("table_rows") or retrieve_matches(question)
    context = format_matches(rows)
    try:
        resp = chain.invoke({
            "system_prompt": SYSTEM + "\n\n【赛程数据】\n" + context,
            "question": question,
        })
        data = json.loads(resp.content)
        return {"answer": data.get("answer", ""), "match_table": rows}
    except Exception:
        # 模型没按 JSON 输出时 json.loads 会抛异常，这里兜住，前端不会崩
        return {"answer": "这次没生成成功，请重试", "match_table": rows}

# 原来的版本（吃 question、返回 answer + source），保留备查：
# def chat(question):
#     if not question.strip():
#         return {"answer": "", "source": ""}
#     rows = retrieve_matches(question)
#     try:
#         resp = chain.invoke({
#             "system_prompt": SYSTEM + "\n\n【赛程数据】\n" + format_matches(rows),
#             "question": question,
#         })
#         return json.loads(resp.content)
#     except Exception:
#         # 模型没按 JSON 输出时 json.loads 会抛异常，这里兜住，前端不会崩
#         return {"answer": "这次没生成成功，请重试", "source": "解析失败"}
