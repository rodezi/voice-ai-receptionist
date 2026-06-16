"""
Dashboard router — serves the monitoring UI and API endpoints.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from dashboard.state import (
    get_recent_events,
    get_stats,
    register_sse_queue,
    unregister_sse_queue,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


@router.get("/", response_class=HTMLResponse)
async def dashboard_index(request: Request) -> HTMLResponse:
    """Render the real-time dashboard HTML page."""
    stats = get_stats()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"stats": stats},
    )


@router.get("/api/stats")
async def api_stats() -> JSONResponse:
    """Return current dashboard statistics as JSON."""
    return JSONResponse(content=get_stats())


@router.get("/api/recent-events")
async def api_recent_events() -> JSONResponse:
    """Return the list of recent events as JSON."""
    return JSONResponse(content=get_recent_events())


@router.get("/api/events")
async def api_events(request: Request) -> StreamingResponse:
    """
    Server-Sent Events endpoint.
    Streams real-time events to connected dashboard clients.
    Sends a heartbeat ping every 15 seconds to keep the connection alive.
    """
    q = register_sse_queue()

    async def event_generator():
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info("SSE client disconnected")
                    break

                try:
                    # Wait for an event, timeout after 15 s → send heartbeat
                    message = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat to keep connection alive
                    yield 'data: {"type": "ping"}\n\n'
        except asyncio.CancelledError:
            logger.info("SSE stream cancelled")
        except Exception as exc:
            logger.error("SSE stream error: %s", exc)
        finally:
            unregister_sse_queue(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
