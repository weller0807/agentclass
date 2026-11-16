# 足球赛程助手

查大连英博海发 2025 赛季中超赛程的网页小工具。用大白话提问（比如"5 月 1 号大连队在哪踢"），页面给出文字回答，并把命中的比赛列成表格，顺带查一下比赛地的天气。

界面用 Gradio，流程用 LangGraph 串起来，DeepSeek 负责把检出来的赛程说成人话。

## 怎么跑起来

### 1. 装依赖

先建虚拟环境（项目用的是 Python 3.14）：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

然后装库：

```powershell
pip install gradio pandas langchain-core langchain-openai langgraph python-dotenv requests
```

### 2. 配 API Key（用你自己的）



在项目根目录新建 `.env` 文件，内容两行：

```
DEEPSEEK_API_KEY=你自己的 DeepSeek 密钥
JUHE_WEATHER_KEY=你自己的聚合数据密钥
```

- `DEEPSEEK_API_KEY`：拿自己的账号去 https://platform.deepseek.com 申请，用来生成回答。**必须填**，缺了启动直接报 `缺少 DEEPSEEK_API_KEY`
- `JUHE_WEATHER_KEY`：拿自己的账号去 https://www.juhe.cn 申请"天气查询"接口，用来查比赛地天气。不填也能跑，只是天气那列空着

key 是要花钱的，别提交上去，也别贴到聊天里。

### 3. 启动

```powershell
python main.py
```

终端出现 `访问地址： http://localhost:7860` 后，浏览器打开这个地址就行。

程序监听的是 `0.0.0.0`，所以同一个 WiFi 下的手机、平板也能用电脑的局域网 IP 打开。第一次运行时 Windows 防火墙会弹窗，点"允许"。

## 怎么用

1. 输入框打字提问，点"生成"
2. 上面那个框是 AI 的回答，下面那张表是命中的比赛，列依次是日期、星期、主队、客队、场地、天气

能听懂的说法，举几个例子：

- "5月1日大连队的比赛"
- "辽宁队那场在哪踢"
- "最后一场什么时候"
- "最近一场"

赛程里没有的东西，它会直接说没找到，不会瞎编。

## 代码怎么组织的

```
main.py                  Gradio 界面，只管收问题、显示结果
backend.py               接 DeepSeek，把赛程丢给模型组织成回答
matches.json             赛程数据，30 场
matches.md               赛程表格的阅读版，方便人工核对
retrieval_demo/
  v2versionnewtome.py    流程编排：选赛程 → 逐场查天气 → 生成回答
  data.py                读 matches.json，按队名/城市/日期挑出相关比赛
  weather.py             调聚合数据接口查实时天气
  model_chat.py          备用版本，走本地 Ollama 的 qwen2.5，没接进主流程
```

一次查询的流程是这样走的：

```
提问 → data.py 挑出相关比赛 → 有命中就逐场查天气 → 交给 DeepSeek 生成回答 → 返回文字 + 表格
```

## 换数据

赛程全在 `matches.json`，一条一场，字段长这样：

```json
{
  "match_date": "3.7",
  "weekday": "六",
  "kickoff": "17:00",
  "home": "上海申花",
  "away": "大连英博海发",
  "venue": "上海体育场",
  "city": "上海"
}
```

改的时候注意三点：

- `city` 是查天气用的，必须填对，填错天气就查不出来
- 队名写全称（"大连英博海发""辽宁铁人"），用户说简称靠模型自己对应
- 场馆和城市的对应关系写在 `data.py` 的 `VENUE_CITY` 字典里，出现新场馆要往里面补一条

## 已知问题

- 天气查的是**此刻**的实时天气，不是比赛日的预报。问今天之后的比赛，天气只能参考着看
- 模型偶尔不按 JSON 格式输出，会兜底成"这次没生成成功，请重试"，重试一次通常就好
- `model_chat.py` 是早期走本地 Ollama 的版本，需要自己先跑起 `qwen2.5` 才能用，目前只留作参考
