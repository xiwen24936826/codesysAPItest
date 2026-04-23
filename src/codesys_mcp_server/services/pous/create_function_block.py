"""Create-function-block service for the first MCP implementation phase."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from typing import Any, Protocol
from uuid import uuid4

from ._common import (
    error_response,
    optional_non_empty_string,
    require_absolute_path,
    require_non_empty_string,
    require_string_list,
    resolve_effective_container_path,
    resolve_language,
    success_response,
)


LOGGER = logging.getLogger(__name__)
TOOL_NAME = "create_function_block"


class FunctionBlockCreator(Protocol):
    """Protocol for adapters that can create function blocks."""

    def create_function_block(
        self,
        project_path: str,
        container_path: str,
        name: str,
        language: str = "ST",
        base_type: str | None = None,
        interfaces: list[str] | None = None,
    ) -> Any:
        """Create a function block in the target project."""


@dataclass(frozen=True)
class CreateFunctionBlockRequest:
    """Validated request payload for create_function_block."""

    project_path: str
    container_path: str
    name: str
    language: str = "ST"
    base_type: str | None = None
    interfaces: list[str] | None = None


@dataclass(frozen=True)
class CreateFunctionBlockValidationError(Exception):
    """Validation error for create_function_block requests."""

    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def create_function_block(
    request: dict[str, Any],
    function_block_creator: FunctionBlockCreator,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create a function block and return a structured MCP-style response."""
    started_at = time.perf_counter()
    resolved_request_id = request_id or str(uuid4())

    try:
        validated_request = _validate_request(request)
        resolved_container_path = resolve_effective_container_path(
            browser=function_block_creator,
            project_path=validated_request.project_path,
            requested_container_path=validated_request.container_path,
        )

        function_block_creator.create_function_block(
            project_path=validated_request.project_path,
            container_path=resolved_container_path,
            name=validated_request.name,
            language=validated_request.language,
            base_type=validated_request.base_type,
            interfaces=validated_request.interfaces,
        )

        response_data = {
            "project_path": validated_request.project_path,
            "container_path": resolved_container_path,
            "name": validated_request.name,
            "object_type": "function_block",
            "language": validated_request.language,
            "base_type": validated_request.base_type,
            "interfaces": validated_request.interfaces or [],
        }

        LOGGER.info(
            "create_function_block succeeded",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": validated_request.project_path,
                "container_path": resolved_container_path,
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
    except CreateFunctionBlockValidationError as exc:
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
            "create_function_block failed with unexpected error",
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
            message="Unexpected error while creating function block.",
            details={"exception": str(exc)},
            request_id=resolved_request_id,
            started_at=started_at,
        )


def _validate_request(request: dict[str, Any]) -> CreateFunctionBlockRequest:
    return CreateFunctionBlockRequest(
        project_path=require_absolute_path(
            "project_path",
            request.get("project_path"),
            CreateFunctionBlockValidationError,
        ),
        container_path=require_non_empty_string(
            "container_path",
            request.get("container_path"),
            CreateFunctionBlockValidationError,
        ),
        name=require_non_empty_string(
            "name",
            request.get("name"),
            CreateFunctionBlockValidationError,
        ),
        language=resolve_language(
            request.get("language"),
            CreateFunctionBlockValidationError,
        ),
        base_type=optional_non_empty_string(
            "base_type",
            request.get("base_type"),
            CreateFunctionBlockValidationError,
        ),
        interfaces=require_string_list(
            "interfaces",
            request.get("interfaces"),
            CreateFunctionBlockValidationError,
        ),
    )
