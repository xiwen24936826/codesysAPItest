"""Read-textual-implementation service for the first MCP implementation phase."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from typing import Any, Protocol
from uuid import uuid4

from ._common import (
    error_response,
    extract_text,
    require_absolute_path,
    require_non_empty_string,
    success_response,
)


LOGGER = logging.getLogger(__name__)
TOOL_NAME = "read_textual_implementation"


class TextDocumentReader(Protocol):
    """Protocol for adapters that can read textual documents."""

    def read_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
    ) -> Any:
        """Read a textual document from the target project."""


@dataclass(frozen=True)
class ReadTextualImplementationRequest:
    """Validated request payload for read_textual_implementation."""

    project_path: str
    container_path: str
    object_name: str


@dataclass(frozen=True)
class ReadTextualImplementationValidationError(Exception):
    """Validation error for read_textual_implementation requests."""

    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def read_textual_implementation(
    request: dict[str, Any],
    text_document_reader: TextDocumentReader,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Read the implementation text and return a structured MCP-style response."""
    started_at = time.perf_counter()
    resolved_request_id = request_id or str(uuid4())

    try:
        validated_request = _validate_request(request)
        text = extract_text(
            text_document_reader.read_text_document(
                project_path=validated_request.project_path,
                container_path=validated_request.container_path,
                object_name=validated_request.object_name,
                document_kind="implementation",
            )
        )

        response_data = {
            "project_path": validated_request.project_path,
            "container_path": validated_request.container_path,
            "object_name": validated_request.object_name,
            "document_kind": "implementation",
            "text": text,
        }
        return success_response(
            tool_name=TOOL_NAME,
            data=response_data,
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except ReadTextualImplementationValidationError as exc:
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
        LOGGER.warning(
            "read_textual_implementation could not resolve implementation text",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": request.get("project_path"),
                "container_path": request.get("container_path"),
                "object_name": request.get("object_name"),
                "status": "failed",
                "error_code": "TEXT_DOCUMENT_NOT_FOUND",
            },
        )
        return error_response(
            tool_name=TOOL_NAME,
            code="TEXT_DOCUMENT_NOT_FOUND",
            message="Textual implementation could not be resolved.",
            details={"exception": str(exc)},
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except Exception as exc:  # pragma: no cover
        LOGGER.exception(
            "read_textual_implementation failed with unexpected error",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": request.get("project_path"),
                "container_path": request.get("container_path"),
                "object_name": request.get("object_name"),
                "status": "failed",
                "error_code": "INTERNAL_ERROR",
            },
        )
        return error_response(
            tool_name=TOOL_NAME,
            code="INTERNAL_ERROR",
            message="Unexpected error while reading textual implementation.",
            details={"exception": str(exc)},
            request_id=resolved_request_id,
            started_at=started_at,
        )


def _validate_request(request: dict[str, Any]) -> ReadTextualImplementationRequest:
    return ReadTextualImplementationRequest(
        project_path=require_absolute_path(
            "project_path",
            request.get("project_path"),
            ReadTextualImplementationValidationError,
        ),
        container_path=require_non_empty_string(
            "container_path",
            request.get("container_path"),
            ReadTextualImplementationValidationError,
        ),
        object_name=require_non_empty_string(
            "object_name",
            request.get("object_name"),
            ReadTextualImplementationValidationError,
        ),
    )
