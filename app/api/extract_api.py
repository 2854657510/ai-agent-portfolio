from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.extract import extract_safe
from app.schema import TenderNotice

router = APIRouter()


class ExtractRequest(BaseModel):
    document: str = Field(
        ..., min_length=1, max_length=50000, description="待抽取的公告原文"
    )
@router.post("/extract", response_model=TenderNotice, tags=["extract"])
async def extract(req: ExtractRequest):
    result = await run_in_threadpool(extract_safe, req.document)

    if result.get("_failed"):
        raise HTTPException(
            status_code=422,
            detail={
                "message": "抽取失败，已走降级路径",
                "reason": result.get("_error", "")[:500],
            },
        )
    return result
