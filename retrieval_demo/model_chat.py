import json
# from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from sympy.physics.units import temperature

from data import MATCHES, format_matches, retrieve_matches
# llm = ChatOpenAI(
#     model="deepseek-chat",
#     api_key="sk-",
#     base_url="https://api.deepseek.com",
#     temperature=0,
# )
DEFAULT_SYSTEM = (
    "你是足球赛程助手。你只能根据下面【赛程数据】回答用户问题，禁止编造。\n"
    "用户可能用球队简称提问，请对照【赛程数据】里的队名理解（例如“辽宁队”指“辽宁铁人”）。\n"
    "必须只输出一个 JSON 对象，不要输出任何多余文字、不要用 markdown 代码块标记。\n"
    '格式固定为：{"answer": "用中文给出的完整回答", "source": "数据来源说明（命中哪些比赛）"}\n'
    "如果赛程数据里没有用户问的信息，answer 如实说明没有，source 写“数据中未找到，今天是11月7日”。\n"
    "\n【赛程数据】\n{context}"
)
from langchain_ollama import ChatOllama
llm = ChatOllama(
    model="qwen2.5",
    base_url="http://127.0.0.1:11434",
    temperature=0.5
)

def model_chat(state):
    question = state["question"]
    rows = retrieve_matches(question)
    context = format_matches(rows)
    system_text = DEFAULT_SYSTEM.replace("{context}", context)
    messages = [("system", system_text), ("human", question)]
    resp = llm.invoke(messages)
    return {
        "answer": resp.content,
        "context": context,
        "match_table": rows,
    }

def chat_json(question, system_text):
    if not question.strip():
        return {"answer": "", "source": ""}
    rows = retrieve_matches(question)
    context = format_matches(rows)
    system = system_text + "\n\n【赛程数据】\n" + context
    resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=question)])
    content = resp.content.strip()
    try:
        return json.loads(content)
    except Exception:
        try:
            start = content.index("{")
            end = content.rindex("}") + 1
            return json.loads(content[start:end])
        except Exception:
            return {"answer": content, "source": "解析失败（模型未按 JSON 输出）"}
