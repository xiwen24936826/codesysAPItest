"""Open-project service for the first MCP implementation phase."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
import time
from typing import Any, Protocol
from uuid import uuid4

from codesys_mcp_server.core import CodesysProjectInUseError


LOGGER = logging.getLogger(__name__)
TOOL_NAME = "open_project"


class ProjectOpener(Protocol):
    """Protocol for adapters that can open a CODESYS project."""

    def open(self, path: str) -> Any:
        """Open a project in the target CODESYS environment."""


@dataclass(frozen=True)
class OpenProjectRequest:
    """Validated request payload for the open_project tool."""

    project_path: str


@dataclass(frozen=True)
class OpenProjectValidationError(Exception):
    """Validation error for open_project requests."""

    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def open_project(
    request: dict[str, Any],
    project_opener: ProjectOpener,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Open an existing project and return a structured MCP-style response."""
    started_at = time.perf_counter()
    resolved_request_id = request_id or str(uuid4())

    try:
        validated_request = _validate_request(request)

        project_opener.open(path=validated_request.project_path)

        response_data = {
            "project_path": validated_request.project_path,
            "project_name": Path(validated_request.project_path).stem,
            "is_primary": True,
        }

        LOGGER.info(
            "open_project succeeded",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": validated_request.project_path,
                "status": "success",
            },
        )
        return _success_response(
            data=response_data,
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except OpenProjectValidationError as exc:
        LOGGER.warning(
            "open_project validation failed",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": request.get("project_path"),
                "status": "failed",
                "error_code": exc.code,
            },
        )
        return _error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except FileNotFoundError:
        LOGGER.warning(
            "open_project target was not found",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": request.get("project_path"),
                "status": "failed",
                "error_code": "PROJECT_NOT_FOUND",
            },
        )
        return _error_response(
            code="PROJECT_NOT_FOUND",
            message="Project file was not found.",
            details={"project_path": request.get("project_path")},
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except CodesysProjectInUseError:
        LOGGER.warning(
            "open_project target is currently in use",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": request.get("project_path"),
                "status": "failed",
                "error_code": "PROJECT_IN_USE",
            },
        )
        return _error_response(
            code="PROJECT_IN_USE",
            message="Project file is currently in use by another IDE session.",
            details={"project_path": request.get("project_path")},
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except Exception as exc:  # pragma: no cover - safety net for unexpected adapter failures
        LOGGER.exception(
            "open_project failed with unexpected error",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": request.get("project_path"),
                "status": "failed",
                "error_code": "INTERNAL_ERROR",
            },
        )
        return _error_response(
            code="INTERNAL_ERROR",
            message="Unexpected error while opening project.",
            details={"exception": str(exc)},
            request_id=resolved_request_id,
            started_at=started_at,
        )


def _validate_request(request: dict[str, Any]) -> OpenProjectRequest:
    project_path = request.get("project_path")

    if not isinstance(project_path, str) or not project_path.strip():
        raise OpenProjectValidationError(
            message="Field 'project_path' is required.",
            details={"field": "project_path"},
        )

    if not Path(project_path).is_absolute():
        raise OpenProjectValidationError(
            message="Field 'project_path' must be an absolute path.",
            details={"field": "project_path", "value": project_path},
        )

    return OpenProjectRequest(project_path=project_path)


def _success_response(
    data: dict[str, Any],
    request_id: str,
    started_at: float,
) -> dict[str, Any]:
    return {
        "ok": True,
        "tool": TOOL_NAME,
        "data": data,
        "error": None,
        "meta": _build_meta(request_id=request_id, started_at=started_at),
    }


def _error_response(
    code: str,
    message: str,
    details: dict[str, Any],
    request_id: str,
    started_at: float,
) -> dict[str, Any]:
    return {
        "ok": False,
        "tool": TOOL_NAME,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "meta": _build_meta(request_id=request_id, started_at=started_at),
    }


def _build_meta(request_id: str, started_at: float) -> dict[str, Any]:
    return {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "request_id": request_id,
        "duration_ms": round((time.perf_counter() - started_at) * 1000),
    }
