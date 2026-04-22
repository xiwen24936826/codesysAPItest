"""Create-function service for the first MCP implementation phase."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from typing import Any, Protocol
from uuid import uuid4

from ._common import (
    error_response,
    require_absolute_path,
    require_non_empty_string,
    resolve_language,
    success_response,
)


LOGGER = logging.getLogger(__name__)
TOOL_NAME = "create_function"


class FunctionCreator(Protocol):
    """Protocol for adapters that can create IEC functions."""

    def create_function(
        self,
        project_path: str,
        container_path: str,
        name: str,
        return_type: str,
        language: str = "ST",
    ) -> Any:
        """Create a function in the target project."""


@dataclass(frozen=True)
class CreateFunctionRequest:
    """Validated request payload for create_function."""

    project_path: str
    container_path: str
    name: str
    return_type: str
    language: str = "ST"


@dataclass(frozen=True)
class CreateFunctionValidationError(Exception):
    """Validation error for create_function requests."""

    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def create_function(
    request: dict[str, Any],
    function_creator: FunctionCreator,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create a function and return a structured MCP-style response."""
    started_at = time.perf_counter()
    resolved_request_id = request_id or str(uuid4())

    try:
        validated_request = _validate_request(request)

        function_creator.create_function(
            project_path=validated_request.project_path,
            container_path=validated_request.container_path,
            name=validated_request.name,
            return_type=validated_request.return_type,
            language=validated_request.language,
        )

        response_data = {
            "project_path": validated_request.project_path,
            "container_path": validated_request.container_path,
            "name": validated_request.name,
            "object_type": "function",
            "return_type": validated_request.return_type,
            "language": validated_request.language,
        }

        LOGGER.info(
            "create_function succeeded",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": validated_request.project_path,
                "container_path": validated_request.container_path,
                "pou_name": validated_request.name,
                "status": "success",
            },
        )
        return success_response(
            tool_name=TOOL_NAME,
            data=response_data,
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except CreateFunctionValidationError as exc:
        return error_response(
            tool_name=TOOL_NAME,
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except FileNotFoundError:
        return error_response(
            tool_name=TOOL_NAME,
            code="PROJECT_NOT_FOUND",
            message="Project file was not found.",
            details={"project_path": request.get("project_path")},
            request_id=resolved_request_id,
            started_at=started_at,
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
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except Exception as exc:  # pragma: no cover
        LOGGER.exception(
            "create_function failed with unexpected error",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": request.get("project_path"),
                "container_path": request.get("container_path"),
                "pou_name": request.get("name"),
                "status": "failed",
                "error_code": "POU_CREATE_FAILED",
            },
        )
        return error_response(
            tool_name=TOOL_NAME,
            code="POU_CREATE_FAILED",
            message="Unexpected error while creating function.",
            details={"exception": str(exc)},
            request_id=resolved_request_id,
            started_at=started_at,
        )


def _validate_request(request: dict[str, Any]) -> CreateFunctionRequest:
    return CreateFunctionRequest(
        project_path=require_absolute_path(
            "project_path",
            request.get("project_path"),
            CreateFunctionValidationError,
        ),
        container_path=require_non_empty_string(
            "container_path",
            request.get("container_path"),
            CreateFunctionValidationError,
        ),
        name=require_non_empty_string(
            "name",
            request.get("name"),
            CreateFunctionValidationError,
        ),
        return_type=require_non_empty_string(
            "return_type",
            request.get("return_type"),
            CreateFunctionValidationError,
        ),
        language=resolve_language(
            request.get("language"),
            CreateFunctionValidationError,
        ),
    )
