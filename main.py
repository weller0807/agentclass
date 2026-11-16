# -*- coding: utf-8 -*-
"""main.py —— Gradio 前端：回答 + 命中赛程表格"""
import os
import sys

import gradio as gr
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "retrieval_demo"))

from v2versionnewtome import ask

COLUMNS = ["match_date", "weekday", "home", "away", "venue", "weather"]
HEADERS = ["日期", "星期", "主队", "客队", "场地", "天气"]

PORT = 7860


def to_df(rows):
    """rows -> 表格；缺的字段补空字符串"""
    if not rows:
        return pd.DataFrame(columns=HEADERS)
    df = pd.DataFrame([{c: r.get(c, "") for c in COLUMNS} for r in rows])
    df.columns = HEADERS
    return df


def chat_and_table(question):
    """返回 (回答文字, 命中赛程表格)"""
    if not question or not question.strip():
        return "", to_df(None)
    answer, rows = ask(question.strip())
    return answer, to_df(rows)


with gr.Blocks(title="足球赛程助手") as demo:
    gr.Markdown("## ⚽ 足球赛程助手")

    question = gr.Textbox(label="你的问题",
                          placeholder="例如：5月1日大连队的比赛")

    answer_box = gr.Textbox(label="AI 回答", lines=4, interactive=False)
    table = gr.Dataframe(label="命中的赛程（日期 | 星期 | 主队 | 客队 | 场地 | 天气）",
                         headers=HEADERS, interactive=False)

    btn = gr.Button("生成", variant="primary")
    btn.click(fn=chat_and_table, inputs=[question],
              outputs=[answer_box, table])

if __name__ == "__main__":
    print(f"访问地址： http://localhost:{PORT}")
    # 0.0.0.0 = 监听所有网卡，同 WiFi 下别的设备也能访问
    demo.launch(server_name="0.0.0.0", server_port=PORT)
