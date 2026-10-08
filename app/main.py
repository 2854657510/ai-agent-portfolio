
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import extract_api, stream

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI(
    title="portfolio agent",
    version="0.0.1",
    description="AI Agent 作品集项目：结构化抽取 + 流式对话",
)


app.add_middleware(
    CORSMiddleware,
    # streamlit后端调用需要
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream.router, prefix="/api", tags=["stream"])
app.include_router(extract_api.router, prefix="/api", tags=["extract"])

# 健康检查
@app.get("/health", tags=["ops"])
async def health():
    return {"status": True}
