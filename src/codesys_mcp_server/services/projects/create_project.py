"""Create-project service for the first MCP implementation phase."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any, Protocol

from .._service_common import begin_service_call, build_log_extra, error_response, success_response


LOGGER = logging.getLogger(__name__)
TOOL_NAME = "create_project"
SUPPORTED_PROJECT_MODES = {"empty", "template"}


class ProjectCreator(Protocol):
    """Protocol for adapters that can create a CODESYS project."""

    def create(self, path: str, primary: bool = True) -> Any:
        """Create a project in the target CODESYS environment."""


@dataclass(frozen=True)
class CreateProjectRequest:
    """Validated request payload for the create_project tool."""

    project_path: str
    project_mode: str
    set_as_primary: bool = True
    template_project_path: str | None = None


def create_project(
    request: dict[str, Any],
    project_creator: ProjectCreator,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create a new project and return a structured MCP-style response."""
    service_call = begin_service_call(request_id)

    try:
        validated_request = _validate_request(request)

        if validated_request.project_mode == "template":
            raise CreateProjectValidationError(
                message="Template project mode is defined but not implemented in phase 1.",
                details={"project_mode": validated_request.project_mode},
            )

        project_creator.create(
            path=validated_request.project_path,
            primary=validated_request.set_as_primary,
        )

        response_data = {
            "project_path": validated_request.project_path,
            "project_name": Path(validated_request.project_path).stem,
            "project_mode": validated_request.project_mode,
            "is_primary": validated_request.set_as_primary,
        }

        LOGGER.info(
            "create_project succeeded",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="success",
                project_path=validated_request.project_path,
                project_mode=validated_request.project_mode,
            ),
        )
        return success_response(
            tool_name=TOOL_NAME,
            data=response_data,
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except CreateProjectValidationError as exc:
        LOGGER.warning(
            "create_project validation failed",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="failed",
                error_code=exc.code,
                project_path=request.get("project_path"),
                project_mode=request.get("project_mode"),
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
    except Exception as exc:  # pragma: no cover - safety net for unexpected adapter failures
        LOGGER.exception(
            "create_project failed with unexpected error",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="failed",
                error_code="INTERNAL_ERROR",
                project_path=request.get("project_path"),
                project_mode=request.get("project_mode"),
            ),
        )
        return error_response(
            tool_name=TOOL_NAME,
            code="INTERNAL_ERROR",
            message="Unexpected error while creating project.",
            details={"exception": str(exc)},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )


@dataclass(frozen=True)
class CreateProjectValidationError(Exception):
    """Validation error for create_project requests."""

    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def _validate_request(request: dict[str, Any]) -> CreateProjectRequest:
    project_path = request.get("project_path")
    project_mode = request.get("project_mode")
    set_as_primary = request.get("set_as_primary", True)
    template_project_path = request.get("template_project_path")

    if not isinstance(project_path, str) or not project_path.strip():
        raise CreateProjectValidationError(
            message="Field 'project_path' is required.",
            details={"field": "project_path"},
        )

    if not Path(project_path).is_absolute():
        raise CreateProjectValidationError(
            message="Field 'project_path' must be an absolute path.",
            details={"field": "project_path", "value": project_path},
        )

    if not isinstance(project_mode, str) or project_mode not in SUPPORTED_PROJECT_MODES:
        raise CreateProjectValidationError(
            message="Field 'project_mode' must be one of: empty, template.",
            details={"field": "project_mode", "value": project_mode},
        )

    if not isinstance(set_as_primary, bool):
        raise CreateProjectValidationError(
            message="Field 'set_as_primary' must be a boolean when provided.",
            details={"field": "set_as_primary", "value": set_as_primary},
        )

    if project_mode == "template":
        if not isinstance(template_project_path, str) or not template_project_path.strip():
            raise CreateProjectValidationError(
                message="Field 'template_project_path' is required when project_mode is 'template'.",
                details={"field": "template_project_path"},
            )
        if not Path(template_project_path).is_absolute():
            raise CreateProjectValidationError(
                message="Field 'template_project_path' must be an absolute path.",
                details={"field": "template_project_path", "value": template_project_path},
            )

    return CreateProjectRequest(
        project_path=project_path,
        project_mode=project_mode,
        set_as_primary=set_as_primary,
        template_project_path=template_project_path,
    )
