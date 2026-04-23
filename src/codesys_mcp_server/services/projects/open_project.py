"""Open-project service for the first MCP implementation phase."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any, Protocol

from .._service_common import begin_service_call, build_log_extra, error_response, success_response


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
    service_call = begin_service_call(request_id)

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
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="success",
                project_path=validated_request.project_path,
            ),
        )
        return success_response(
            tool_name=TOOL_NAME,
            data=response_data,
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except OpenProjectValidationError as exc:
        LOGGER.warning(
            "open_project validation failed",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="failed",
                error_code=exc.code,
                project_path=request.get("project_path"),
            ),
        )
        return error_response(
            tool_name=TOOL_NAME,
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except FileNotFoundError:
        LOGGER.warning(
            "open_project target was not found",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="failed",
                error_code="PROJECT_NOT_FOUND",
                project_path=request.get("project_path"),
            ),
        )
        return error_response(
            tool_name=TOOL_NAME,
            code="PROJECT_NOT_FOUND",
            message="Project file was not found.",
            details={"project_path": request.get("project_path")},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except Exception as exc:  # pragma: no cover - safety net for unexpected adapter failures
        LOGGER.exception(
            "open_project failed with unexpected error",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="failed",
                error_code="INTERNAL_ERROR",
                project_path=request.get("project_path"),
            ),
        )
        return error_response(
            tool_name=TOOL_NAME,
            code="INTERNAL_ERROR",
            message="Unexpected error while opening project.",
            details={"exception": str(exc)},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
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

