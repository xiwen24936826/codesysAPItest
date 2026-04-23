"""Append-text-document service for the first MCP implementation phase."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Protocol

from .._service_common import begin_service_call, build_log_extra
from ._common import (
    execute_text_write_flow,
    error_response,
    require_absolute_path,
    require_ascii_text,
    require_document_kind,
    require_non_empty_string,
    success_response,
)


LOGGER = logging.getLogger(__name__)
TOOL_NAME = "append_text_document"


class TextDocumentAppender(Protocol):
    """Protocol for adapters that can append textual documents."""

    def append_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        text_to_append: str,
    ) -> Any:
        """Append text to the target document."""

    def read_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
    ) -> Any:
        """Read a textual document in the target project."""


@dataclass(frozen=True)
class AppendTextDocumentRequest:
    """Validated request payload for append_text_document."""

    project_path: str
    container_path: str
    object_name: str
    document_kind: str
    text_to_append: str


@dataclass(frozen=True)
class AppendTextDocumentValidationError(Exception):
    """Validation error for append_text_document requests."""

    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def append_text_document(
    request: dict[str, Any],
    text_document_appender: TextDocumentAppender,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Append to the target text document and return a structured response."""
    service_call = begin_service_call(request_id)

    try:
        validated_request = _validate_request(request)
        resolved_container_path, expected_text = execute_text_write_flow(
            adapter=text_document_appender,
            validated_request=validated_request,
            validation_error_cls=AppendTextDocumentValidationError,
            build_expected_text=lambda current_text: current_text + validated_request.text_to_append,
            perform_write=lambda container_path: text_document_appender.append_text_document(
                project_path=validated_request.project_path,
                container_path=container_path,
                object_name=validated_request.object_name,
                document_kind=validated_request.document_kind,
                text_to_append=validated_request.text_to_append,
            ),
        )

        response_data = {
            "project_path": validated_request.project_path,
            "container_path": resolved_container_path,
            "object_name": validated_request.object_name,
            "document_kind": validated_request.document_kind,
            "updated": True,
            "appended_length": len(validated_request.text_to_append),
            "roundtrip_verified": True,
        }
        return success_response(
            tool_name=TOOL_NAME,
            data=response_data,
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except AppendTextDocumentValidationError as exc:
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
            code="TEXT_DOCUMENT_NOT_FOUND",
            message="Target text document could not be resolved.",
            details={"exception": str(exc)},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except Exception as exc:  # pragma: no cover
        LOGGER.exception(
            "append_text_document failed with unexpected error",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="failed",
                error_code="INTERNAL_ERROR",
                project_path=request.get("project_path"),
                container_path=request.get("container_path"),
                object_name=request.get("object_name"),
            ),
        )
        return error_response(
            tool_name=TOOL_NAME,
            code="INTERNAL_ERROR",
            message="Unexpected error while appending text document.",
            details={"exception": str(exc)},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )


def _validate_request(request: dict[str, Any]) -> AppendTextDocumentRequest:
    return AppendTextDocumentRequest(
        project_path=require_absolute_path(
            "project_path",
            request.get("project_path"),
            AppendTextDocumentValidationError,
        ),
        container_path=require_non_empty_string(
            "container_path",
            request.get("container_path"),
            AppendTextDocumentValidationError,
        ),
        object_name=require_non_empty_string(
            "object_name",
            request.get("object_name"),
            AppendTextDocumentValidationError,
        ),
        document_kind=require_document_kind(
            request.get("document_kind"),
            AppendTextDocumentValidationError,
        ),
        text_to_append=require_ascii_text(
            "text_to_append",
            require_non_empty_string(
                "text_to_append",
                request.get("text_to_append"),
                AppendTextDocumentValidationError,
            ),
            AppendTextDocumentValidationError,
        ),
    )
