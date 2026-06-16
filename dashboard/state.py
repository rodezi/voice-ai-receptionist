"""
Dashboard state — in-memory stats, event history, and SSE queue management.
"""

from __future__ import annotations

import asyncio
import json
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DashboardStats:
    active_calls: int = 0
    completed_calls: int = 0
    leads_registered: int = 0
    appointments_scheduled: int = 0
    reports_generated: int = 0


_stats = DashboardStats()
_recent_events: deque = deque(maxlen=50)
_sse_queues: list[asyncio.Queue] = []


def get_stats() -> dict:
    """Return current dashboard stats as a plain dict."""
    return {
        "active_calls": _stats.active_calls,
        "completed_calls": _stats.completed_calls,
        "leads_registered": _stats.leads_registered,
        "appointments_scheduled": _stats.appointments_scheduled,
        "reports_generated": _stats.reports_generated,
    }


def get_recent_events() -> list:
    """Return the list of recent events (up to 50)."""
    return list(_recent_events)


def emit_event(event_type: str, data: dict) -> None:
    """
    Record an event, update stats, and push to all active SSE queues.

    Parameters
    ----------
    event_type : str
        One of: call_started, call_ended, appointment_scheduled, report_generated.
    data : dict
        Arbitrary event payload.
    """
    event = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    _recent_events.append(event)

    # Update counters
    if event_type == "call_started":
        _stats.active_calls += 1
    elif event_type == "call_ended":
        _stats.active_calls = max(0, _stats.active_calls - 1)
        _stats.completed_calls += 1
        _stats.leads_registered += 1
    elif event_type == "appointment_scheduled":
        _stats.appointments_scheduled += 1
    elif event_type == "report_generated":
        _stats.reports_generated += 1

    # Push to all registered SSE consumers
    serialized = json.dumps(event)
    for q in list(_sse_queues):
        try:
            q.put_nowait(serialized)
        except Exception:
            pass


def register_sse_queue() -> asyncio.Queue:
    """Register a new SSE client queue and return it."""
    q: asyncio.Queue = asyncio.Queue()
    _sse_queues.append(q)
    return q


def unregister_sse_queue(q: asyncio.Queue) -> None:
    """Remove a disconnected SSE client queue."""
    try:
        _sse_queues.remove(q)
    except ValueError:
        pass
