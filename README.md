 # 结构化抽取服务

> 喂一段杂乱的招投标公告原文，拿到严格符合 Schema 的结构化 JSON。
> 官方 JSON Output → Prompt 引导 → 本地校验 + 失败自我修正。

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green)]()
[![tests](https://img.shields.io/badge/tests-10%20passed-brightgreen)]()

---

## 这个项目解决什么问题

大模型能从文本里抽信息，但**工程上直接用它有两个坑**：

1. **它可能编造。** 原文没有的字段，它倾向于猜一个看起来合理的值填上。
2. **它可能不按你的格式来。** 官方 JSON Output 只保证"是合法 JSON"，
   不保证"是你想要的 JSON" —— 它完全可能返回 `{"result": "...", "note": "已抽取"}`，
   语法完全合法，但你一个字段都对不上。

这个项目的价值在于**第二层的把关**：本地 Pydantic 校验 + 失败后把错误喂回模型自我修正 +
彻底失败时降级返回结构一致的空对象。

## 实测数据

| 指标 | 数值 | 说明 |
|---|---|---|
| 单次抽取输出 token | **78** | 关掉思考模式后；开着时是 1016（↓13 倍） |
| Prompt 缓存命中 | **640 / 895** | 系统提示词稳定，命中缓存部分按 1/10 计价 |
| 测试覆盖路径 | **4 条** | 一次成功 / 校验失败自愈 / 空内容重试 / 彻底失败降级 |
| 单元测试 | **10 passed** | 全部用假客户端，跑一次不花钱、0.99 秒 |

## 技术栈

| 层 | 选型 | 为什么 |
|---|---|---|
| Web 框架 | FastAPI | 自动生成 `/docs`、Pydantic 原生集成、原生 async |
| 数据契约 | Pydantic v2 | 类型校验 + 范围校验 + JSON Schema 导出，一份定义三处用 |
| 配置管理 | pydantic-settings | 环境变量 / `.env` 分层，密钥不进代码 |
| Prompt 模板 | Jinja2 + `StrictUndefined` | 提示词与代码解耦；变量漏传当场报错 |
| 模型调用 | openai SDK | DeepSeek 兼容 OpenAI 协议，直接复用官方 SDK |
| 前端 | Streamlit | 半天出可交互界面；前后端通过 HTTP 解耦 |
| 测试 | pytest + 假客户端 | 失败路径可测，且不消耗 API 额度 |

## 快速开始

```bash
# 1. 克隆
git clone
cd ai-agent-portfolio

# 2. 建环境
conda create -n agent15 python=3.11 -y
conda activate agent15

# 3. 装依赖
pip install -r requirements.txt

# 4. 配密钥
cp .env.example .env
# 编辑 .env，填入你的 DEEPSEEK_API_KEY

# 5. 启动后端（终端1）
uvicorn app.main:app --reload

# 6. 启动前端（终端2）
streamlit run frontend/app.py
```

- **前端界面**：http://localhost:8501 ← 推荐从这里开始，能输入、能看结果
- **接口文档**：http://127.0.0.1:8000/docs ← 调接口、看 Schema

> 两个终端都要保持开着。前端不 import 后端的任何代码，只通过 HTTP 调用 ——
> 这就是**前后端分离**：后端挂了前端也能启动，只是页面会提示"连不上后端"。

## 项目结构

```
ai-agent-portfolio/
├── app/
│   ├── config.py           # 配置层：.env 读取（绝对路径）+ URL 校验
│   ├── schema.py           # 数据契约：Request / Response / TenderNotice
│   ├── prompt.py           # Prompt 渲染层：Jinja2 模板加载与渲染
│   ├── extract.py          # 核心：抽取 + 校验 + 失败自我修正 + 降级
│   └── api/
│       ├── extract_api.py  # 抽取接口 POST /api/extract
│       └── stream.py       # 流式接口 POST /api/chat/stream (SSE)
├── prompts/
│   └── extract.j2          # 抽取提示词模板
├── scripts/
│   ├── check_config.py     # 验收脚本：配置是否读到
│   ├── check_schema.py     # 验收脚本：Schema 是否正确
│   ├── check_prompt.py     # 验收脚本：模板是否渲染干净
│   ├── raw.py              # 最小可运行示例：裸调一次模型
│   └── try_api.py          # 验收脚本：打 HTTP 接口
├── frontend/               # Streamlit 前端（通过 HTTP 调后端，不 import 后端代码）
│   ├── app.py              # 界面：输入公告 → 抽取 → 展示结果（含置信度可视化）
│   └── api_client.py       # 接口调用层：所有网络请求收在这里
│                           # 
├── tests/
│   └── test_extract.py     # 10 个测试，覆盖 4 条关键路径
├── conftest.py
├── requirements.txt
└── .env.example
```

## API

### `POST /api/extract` — 结构化抽取

```json
// 请求
{ "document": "XX市智慧交通建设项目。采购人：XX市交通运输局。预算约1850万元。" }

// 200 响应
{
  "project_name": "XX市智慧交通建设项目",
  "buyer": "XX市交通运输局",
  "budget_wan": 1850.0,
  "deadline": null,
  "qualification": ["具有独立法人资格"],
  "contact": { "name": "李工", "phone": "0571-8888xxxx" },
  "confidence": 0.95
}
```

- `422` — 抽取彻底失败，走降级路径，`detail` 里带失败原因
- 字段缺失时返回 `null`



