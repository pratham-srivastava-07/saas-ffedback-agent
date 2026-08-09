"""Analysis endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app import service
from app.api.deps import rate_limited_workspace_dep, runtime_dep, settings_dep
from app.ingest import ColumnMapping, CsvIngestError, parse_csv
from app.llm import Runtime
from app.schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter(tags=["analysis"])

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    # Stops nginx and similar proxies buffering the stream, which would
    # defeat the point by delivering every frame at the end.
    "X-Accel-Buffering": "no",
}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    payload: AnalyzeRequest,
    runtime: Runtime = Depends(runtime_dep),
    workspace_id: str = Depends(rate_limited_workspace_dep),
):
    """Run the full pipeline and return the result in one response."""
    raw = [item.model_dump() for item in payload.raw_feedback]
    return await service.analyze(runtime, raw, workspace_id)


@router.post("/analyze/stream")
async def analyze_stream(
    payload: AnalyzeRequest,
    runtime: Runtime = Depends(runtime_dep),
    workspace_id: str = Depends(rate_limited_workspace_dep),
):
    """Same pipeline, streamed as server-sent events.

    Consume with ``fetch`` + ``ReadableStream``. ``EventSource`` cannot issue a
    POST, and the feedback batch has to go in the body.
    """
    raw = [item.model_dump() for item in payload.raw_feedback]
    return StreamingResponse(
        service.analyze_stream(runtime, raw, workspace_id),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@router.post("/analyze/csv", response_model=AnalyzeResponse)
async def analyze_csv(
    file: UploadFile = File(..., description="UTF-8 CSV with a text column"),
    text_column: str = Form("text"),
    user_type_column: str = Form("user_type"),
    source_column: str = Form("source"),
    id_column: str = Form("id"),
    default_source: str = Form("other"),
    runtime: Runtime = Depends(runtime_dep),
    workspace_id: str = Depends(rate_limited_workspace_dep),
    settings=Depends(settings_dep),
):
    """Analyse a CSV export directly — the path a real user actually has."""
    try:
        items = parse_csv(
            await file.read(),
            ColumnMapping(
                text=text_column,
                user_type=user_type_column,
                source=source_column,
                id=id_column,
            ),
            max_items=settings.max_items_per_request,
            max_chars=settings.max_chars_per_item,
            default_source=default_source,
        )
    except CsvIngestError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return await service.analyze(runtime, items, workspace_id)
