# -*- coding: utf-8 -*-
"""赛程数据 + 第一个 list 节点
matches.json -> list[dict] -> 按 state["question"] 选出赛程
"""
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE, "matches.json")

# 场馆 -> 城市：全部显式映射（weather 要用 city 查天气）
# 不再用 venue[:2] 猜，查不到的场馆 city 留空，避免"哈尔""呼和""乌鲁"这种错值
VENUE_CITY = {
    "上海体育场": "上海",
    "上海浦东足球场": "上海",
    "上汽浦东足球场": "上海",
    "武汉体育中心体育场": "武汉",
    "大连梭鱼湾足球场": "大连",
    "济南奥体中心体育场": "济南",
    "沈阳铁西体育场": "沈阳",
    "北京工人体育场": "北京",
    "青岛青春足球场": "青岛",
    "青岛西海岸大学城体育场": "青岛",
    "深圳市体育中心体育场": "深圳",
    "天津泰达足球场": "天津",
    "浙江省黄龙体育中心体育场": "杭州",
    "郑州航海体育场": "郑州",
    "云南玉溪高原体育运动中心体育场": "玉溪",
    "重庆龙兴足球场": "重庆",
    "五粮液文体中心足球场": "成都",
}

# 球队简称 -> 全名：用户常问"辽宁队""申花""海港"，要能落到具体队
# 注意：城市名本身（大连/北京/天津/武汉/深圳/青岛/成都/重庆）不作为球队别名，
# 裸写城市按"地点"理解；只有"XX队""英博""申花"这类才是球队
TEAM_ALIAS = {
    "大连队": "大连英博海发", "英博": "大连英博海发", "海发": "大连英博海发",
    "辽宁": "辽宁铁人", "辽宁队": "辽宁铁人", "铁人": "辽宁铁人",
    "申花": "上海申花", "上海申花": "上海申花",
    "海港": "上海海港", "上海海港": "上海海港",
    "山东": "山东泰山", "山东队": "山东泰山", "泰山": "山东泰山",
    "浙江": "浙江俱乐部", "浙江队": "浙江俱乐部",
    "河南": "河南俱乐部", "河南队": "河南俱乐部",
    "武汉队": "武汉三镇", "三镇": "武汉三镇",
    "云南": "云南玉昆", "云南队": "云南玉昆", "玉昆": "云南玉昆",
    "重庆队": "重庆铜梁龙", "铜梁龙": "重庆铜梁龙",
    "北京队": "北京国安", "国安": "北京国安",
    "海牛": "青岛海牛", "青岛海牛": "青岛海牛",
    "西海岸": "青岛西海岸", "青岛西海岸": "青岛西海岸",
    "深圳队": "深圳新鹏城", "新鹏城": "深圳新鹏城",
    "成都队": "成都蓉城", "蓉城": "成都蓉城",
    "天津队": "天津津门虎", "津门虎": "天津津门虎",
}


def _date_key(text):
    """3.7 / 11.08 统一成 3.7 / 11.8：去掉零填充，避免"11月8日"对不上表里的 11.08"""
    a, b = text.split(".")
    return f"{int(a)}.{int(b)}"


def load_matches():
    """matches.json -> list[dict]；缺 city 的按场馆表补，date_key 现算"""
    with open(DATA_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    rows = []
    for r in raw:
        row = dict(r)
        row["city"] = row.get("city") or VENUE_CITY.get(row.get("venue", ""), "")
        row["date_key"] = _date_key(row["match_date"])   # 只用于比对，显示仍用 match_date
        rows.append(row)
    return rows


MATCHES = load_matches()
TEAM_NAMES = {r["home"] for r in MATCHES} | {r["away"] for r in MATCHES}
CITY_NAMES = set(VENUE_CITY.values())


def teams_in(q_text):
    """问题里提到的球队（按全名 + 简称展开成全名）"""
    found = {n for n in TEAM_NAMES if n.lower() in q_text}
    found |= {full for alias, full in TEAM_ALIAS.items() if alias.lower() in q_text}
    return found


def cities_in(q_text, hit_teams):
    """问题里提到的地点；已被命中球队全名覆盖的（如"北京国安"里的北京）不再当地点"""
    return {c for c in CITY_NAMES
            if c in q_text and not any(c in t for t in hit_teams)}


def select_matches(question):
    """按问题选赛程：有日期先按日期筛，再按队名/城市筛；只给日期时返回当天全部比赛"""
    q = question.strip().lower().replace("月", ".").replace("号", "").replace("日", "")
    dates = {f"{int(a)}.{int(b)}" for a, b in re.findall(r"(\d{1,2})\.(\d{1,2})", q)}
    q_text = re.sub(r"\d{1,2}\.\d{1,2}", " ", q)

    hit_teams = teams_in(q_text)
    hit_cities = cities_in(q_text, hit_teams)

    def same_row(r):
        team_ok = r["home"] in hit_teams or r["away"] in hit_teams
        city_ok = bool(r["city"]) and r["city"] in hit_cities
        if not hit_teams and not hit_cities:
            return False
        # 同时提到两支球队/球队加地点时（"辽宁队什么时候打大连"），要求全部满足
        if hit_teams and hit_cities:
            return team_ok and city_ok
        if len(hit_teams) > 1:
            return r["home"] in hit_teams and r["away"] in hit_teams
        return team_ok or city_ok

    hits = [r for r in MATCHES if r["date_key"] in dates]
    if hits:
        # 只有日期、没有队名和城市时，直接返回当天所有比赛
        return [r for r in hits if same_row(r)] or hits
    return [r for r in MATCHES if same_row(r)]


def list_node(state):
    """图里第一个节点：从 state["question"] 选赛程，交给后面 weather 逐场循环"""
    rows = select_matches(state["question"])
    return {"table_rows": rows, "match_table": rows, "idx": 0}


def retrieve_matches(question):        # 兼容 backend.py 的老调用
    return select_matches(question)


FORMAT_FIELDS = ["match_date", "weekday", "kickoff", "home", "away", "venue", "city", "weather"]


def format_matches(rows):
    """rows -> JSON 字符串（喂给 LLM 的【赛程数据】就是这段 JSON）"""
    data = []
    for r in rows:
        d = {k: r[k] for k in FORMAT_FIELDS if k in r}
        if not d.get("weather"):
            d.pop("weather", None)          # 没查到天气就不带这个字段
        d.pop("date_key", None)             # 内部比对字段，不给模型看
        data.append(d)
    return json.dumps(data, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print(len(MATCHES), "场比赛")
    for q in ["5月1日大连队的比赛", "11月8日", "辽宁队什么时候打大连",
              "上海队的比赛", "大连天气怎么样"]:
        rows = select_matches(q)
        print(q, "->", len(rows), "场", [r["match_date"] + "/" + r["city"] for r in rows])
