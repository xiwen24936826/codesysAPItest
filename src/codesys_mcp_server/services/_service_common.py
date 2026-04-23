"""Shared helpers for service-layer responses, request context, and log extras."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import time
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class ServiceCallContext:
    """Runtime context shared by a single service invocation."""

    request_id: str
    started_at: float


def begin_service_call(request_id: str | None = None) -> ServiceCallContext:
    """Create a stable request/timing context for one service call."""
    return ServiceCallContext(
        request_id=request_id or str(uuid4()),
        started_at=time.perf_counter(),
    )


def success_response(
    tool_name: str,
    data: dict[str, Any],
    request_id: str,
    started_at: float,
) -> dict[str, Any]:
    """Build a successful service response using the project-wide MCP shape."""
    return {
        "ok": True,
        "tool": tool_name,
        "data": data,
        "error": None,
        "meta": build_meta(request_id=request_id, started_at=started_at),
    }


def error_response(
    tool_name: str,
    code: str,
    message: str,
    details: dict[str, Any],
    request_id: str,
    started_at: float,
) -> dict[str, Any]:
    """Build a failed service response using the project-wide MCP shape."""
    return {
        "ok": False,
        "tool": tool_name,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "meta": build_meta(request_id=request_id, started_at=started_at),
    }


def build_meta(request_id: str, started_at: float) -> dict[str, Any]:
    """Build standard response metadata for a completed service call."""
    return {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "request_id": request_id,
        "duration_ms": round((time.perf_counter() - started_at) * 1000),
    }


def build_log_extra(
    *,
    tool_name: str,
    request_id: str,
    status: str,
    error_code: str | None = None,
    **fields: Any,
) -> dict[str, Any]:
    """Build a consistent logging `extra` payload for service-layer events."""
    extra = {
        "tool": tool_name,
        "request_id": request_id,
        "status": status,
    }
    if error_code is not None:
        extra["error_code"] = error_code
    extra.update(fields)
    return extra
