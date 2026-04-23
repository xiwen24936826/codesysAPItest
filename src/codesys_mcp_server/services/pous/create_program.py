"""Create-program service for the first MCP implementation phase."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Protocol

from .._service_common import begin_service_call, build_log_extra
from ._common import (
    error_response,
    require_absolute_path,
    require_non_empty_string,
    resolve_effective_container_path,
    resolve_language,
    success_response,
)


LOGGER = logging.getLogger(__name__)
TOOL_NAME = "create_program"


class ProgramCreator(Protocol):
    """Protocol for adapters that can create IEC programs."""

    def create_program(
        self,
        project_path: str,
        container_path: str,
        name: str,
        language: str = "ST",
    ) -> Any:
        """Create a program in the target project."""


@dataclass(frozen=True)
class CreateProgramRequest:
    """Validated request payload for the create_program tool."""

    project_path: str
    container_path: str
    name: str
    language: str = "ST"


@dataclass(frozen=True)
class CreateProgramValidationError(Exception):
    """Validation error for create_program requests."""

    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def create_program(
    request: dict[str, Any],
    program_creator: ProgramCreator,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create a program object and return a structured MCP-style response."""
    service_call = begin_service_call(request_id)

    try:
        validated_request = _validate_request(request)
        resolved_container_path = resolve_effective_container_path(
            browser=program_creator,
            project_path=validated_request.project_path,
            requested_container_path=validated_request.container_path,
        )

        program_creator.create_program(
            project_path=validated_request.project_path,
            container_path=resolved_container_path,
            name=validated_request.name,
            language=validated_request.language,
        )

        response_data = {
            "project_path": validated_request.project_path,
            "container_path": resolved_container_path,
            "name": validated_request.name,
            "object_type": "program",
            "language": validated_request.language,
        }

        LOGGER.info(
            "create_program succeeded",
            extra={
                "tool": TOOL_NAME,
                "request_id": service_call.request_id,
                "project_path": validated_request.project_path,
                "container_path": resolved_container_path,
                "pou_name": validated_request.name,
                "status": "success",
            },
        )
        return success_response(
            tool_name=TOOL_NAME,
            data=response_data,
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except CreateProgramValidationError as exc:
        LOGGER.warning(
            "create_program validation failed",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="failed",
                error_code=exc.code,
                project_path=request.get("project_path"),
                container_path=request.get("container_path"),
                pou_name=request.get("name"),
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
        return error_response(
            tool_name=TOOL_NAME,
            code="PROJECT_NOT_FOUND",
            message="Project file was not found.",
            details={"project_path": request.get("project_path")},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except LookupError as exc:
        return error_response(
            tool_name=TOOL_NAME,
            code="POU_CONTAINER_NOT_FOUND",
            message="POU container could not be resolved.",
            details={
                "container_path": request.get("container_path"),
                "exception": str(exc),
            },
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except Exception as exc:  # pragma: no cover - adapter safety net
        LOGGER.exception(
            "create_program failed with unexpected error",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="failed",
                error_code="POU_CREATE_FAILED",
                project_path=request.get("project_path"),
                container_path=request.get("container_path"),
                pou_name=request.get("name"),
            ),
        )
        return error_response(
            tool_name=TOOL_NAME,
            code="POU_CREATE_FAILED",
            message="Unexpected error while creating program.",
            details={"exception": str(exc)},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )


def _validate_request(request: dict[str, Any]) -> CreateProgramRequest:
    return CreateProgramRequest(
        project_path=require_absolute_path(
            "project_path",
            request.get("project_path"),
            CreateProgramValidationError,
        ),
        container_path=require_non_empty_string(
            "container_path",
            request.get("container_path"),
            CreateProgramValidationError,
        ),
        name=require_non_empty_string(
            "name",
            request.get("name"),
            CreateProgramValidationError,
        ),
        language=resolve_language(
            request.get("language"),
            CreateProgramValidationError,
        ),
    )
