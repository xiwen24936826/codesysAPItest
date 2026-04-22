"""Save-project service for the first MCP implementation phase."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
import time
from typing import Any, Protocol
from uuid import uuid4


LOGGER = logging.getLogger(__name__)
TOOL_NAME = "save_project"
SUPPORTED_SAVE_MODES = {"save", "save_as"}


class ProjectSaver(Protocol):
    """Protocol for adapters that can save a CODESYS project."""

    def save(self, path: str) -> Any:
        """Save the current project."""

    def save_as(self, path: str, target_path: str) -> Any:
        """Save the current project to a new target path."""


@dataclass(frozen=True)
class SaveProjectRequest:
    """Validated request payload for the save_project tool."""

    project_path: str
    save_mode: str
    target_project_path: str | None = None


@dataclass(frozen=True)
class SaveProjectValidationError(Exception):
    """Validation error for save_project requests."""

    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def save_project(
    request: dict[str, Any],
    project_saver: ProjectSaver,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Save the current project and return a structured MCP-style response."""
    started_at = time.perf_counter()
    resolved_request_id = request_id or str(uuid4())

    try:
        validated_request = _validate_request(request)

        if validated_request.save_mode == "save":
            project_saver.save(path=validated_request.project_path)
            saved_project_path = validated_request.project_path
        else:
            project_saver.save_as(
                path=validated_request.project_path,
                target_path=validated_request.target_project_path or "",
            )
            saved_project_path = validated_request.target_project_path or validated_request.project_path

        response_data = {
            "project_path": saved_project_path,
            "save_mode": validated_request.save_mode,
            "saved": True,
        }

        LOGGER.info(
            "save_project succeeded",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": validated_request.project_path,
                "save_mode": validated_request.save_mode,
                "target_project_path": validated_request.target_project_path,
                "status": "success",
            },
        )
        return _success_response(
            data=response_data,
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except SaveProjectValidationError as exc:
        LOGGER.warning(
            "save_project validation failed",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": request.get("project_path"),
                "save_mode": request.get("save_mode"),
                "target_project_path": request.get("target_project_path"),
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
            "save_project target was not found",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": request.get("project_path"),
                "save_mode": request.get("save_mode"),
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
    except Exception as exc:  # pragma: no cover - adapter safety net
        LOGGER.exception(
            "save_project failed with unexpected error",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": request.get("project_path"),
                "save_mode": request.get("save_mode"),
                "status": "failed",
                "error_code": "SAVE_FAILED",
            },
        )
        return _error_response(
            code="SAVE_FAILED",
            message="Unexpected error while saving project.",
            details={"exception": str(exc)},
            request_id=resolved_request_id,
            started_at=started_at,
        )


def _validate_request(request: dict[str, Any]) -> SaveProjectRequest:
    project_path = request.get("project_path")
    save_mode = request.get("save_mode")
    target_project_path = request.get("target_project_path")

    if not isinstance(project_path, str) or not project_path.strip():
        raise SaveProjectValidationError(
            message="Field 'project_path' is required.",
            details={"field": "project_path"},
        )

    if not Path(project_path).is_absolute():
        raise SaveProjectValidationError(
            message="Field 'project_path' must be an absolute path.",
            details={"field": "project_path", "value": project_path},
        )

    if not isinstance(save_mode, str) or save_mode not in SUPPORTED_SAVE_MODES:
        raise SaveProjectValidationError(
            message="Field 'save_mode' must be one of: save, save_as.",
            details={"field": "save_mode", "value": save_mode},
        )

    if save_mode == "save_as":
        if not isinstance(target_project_path, str) or not target_project_path.strip():
            raise SaveProjectValidationError(
                message="Field 'target_project_path' is required when save_mode is 'save_as'.",
                details={"field": "target_project_path"},
            )
        if not Path(target_project_path).is_absolute():
            raise SaveProjectValidationError(
                message="Field 'target_project_path' must be an absolute path.",
                details={"field": "target_project_path", "value": target_project_path},
            )

    return SaveProjectRequest(
        project_path=project_path,
        save_mode=save_mode,
        target_project_path=target_project_path,
    )


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

