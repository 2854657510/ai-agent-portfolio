import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

aclient = AsyncOpenAI(
    api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url
)

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000, description="用户问题")
 # 按 SSE 协议格式化消息。
def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
# 边收边发
async def _event_stream(question: str):
    try:
        stream = await aclient.chat.completions.create(
            model=settings.deepseek_model,
            messages=[{"role": "user", "content": question}],
            stream=True,
            max_tokens=2048,
        )
        async for chunk in stream:
            # 避免空 chunk
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            # 抽取出错时打印
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                yield _sse("reasoning", {"text": reasoning})
            if delta.content:
                yield _sse("delta", {"text": delta.content})
        yield _sse("done", {"finish": "stop"})
    # 接口报异常，发送给前端
    except Exception as e:
        logger.exception("流式请求失败")
        yield _sse("error", {"message": str(e)[:300]})

 # 流式对话接口。
@router.post("/chat/stream", tags=["stream"])
async def chat_stream(req: ChatRequest):
    return StreamingResponse(
        _event_stream(req.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
