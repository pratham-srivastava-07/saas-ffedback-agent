"""Analysis endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app import service
from app.api.deps import runtime_dep
from app.llm import Runtime
from app.schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter(tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest, runtime: Runtime = Depends(runtime_dep)):
    """Run the full pipeline and return the result in one response."""
    raw = [item.model_dump() for item in payload.raw_feedback]
    return await service.analyze(runtime, raw)


@router.post("/analyze/stream")
async def analyze_stream(
    payload: AnalyzeRequest, runtime: Runtime = Depends(runtime_dep)
):
    """Same pipeline, streamed as server-sent events.

    Consume with ``fetch`` + ``ReadableStream``. ``EventSource`` cannot issue a
    POST, and the feedback batch has to go in the body.
    """
    raw = [item.model_dump() for item in payload.raw_feedback]
    return StreamingResponse(
        service.analyze_stream(runtime, raw),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Stops nginx and similar proxies buffering the stream, which
            # would defeat the point by delivering every frame at the end.
            "X-Accel-Buffering": "no",
        },
    )
