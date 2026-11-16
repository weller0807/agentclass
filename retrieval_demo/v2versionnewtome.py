# -*- coding: utf-8 -*-
"""v2versionnewtome.py —— list(选赛程) → weather(逐场查天气) → chat(收尾)"""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from backend import chat
from retrieval_demo.data import list_node
from retrieval_demo.weather import weather


class GraphState(TypedDict):
    question: str
    answer: str
    table_rows: list
    match_table: list
    idx: int


def judge(state):
    return "next" if state["idx"] < len(state["table_rows"]) else "done"


g = StateGraph(GraphState)
g.add_node("list", list_node)
g.add_node("weather", weather)
g.add_node("chat", chat)
g.add_edge(START, "list")
g.add_conditional_edges("list", judge, {"next": "weather", "done": "chat"})
g.add_conditional_edges("weather", judge, {"next": "weather", "done": "chat"})
g.add_edge("chat", END)
graph = g.compile()


def ask(question):
    """前端入口：一次性跑完，返回 (回答文字, 命中赛程)"""
    question = (question or "").strip()
    if not question:
        return "", []
    res = graph.invoke({"question": question, "idx": 0})
    return res["answer"], res["match_table"]
