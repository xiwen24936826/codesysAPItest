"""Append-text-document service for the first MCP implementation phase."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from typing import Any, Protocol
from uuid import uuid4

from ._common import (
    error_response,
    read_document_text,
    require_absolute_path,
    require_ascii_text,
    require_document_kind,
    require_non_empty_string,
    resolve_effective_container_path,
    success_response,
    validate_declaration_implementation_consistency,
    verify_roundtrip_text,
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
    started_at = time.perf_counter()
    resolved_request_id = request_id or str(uuid4())

    try:
        validated_request = _validate_request(request)
        resolved_container_path = resolve_effective_container_path(
            browser=text_document_appender,
            project_path=validated_request.project_path,
            requested_container_path=validated_request.container_path,
        )
        current_text = read_document_text(
            adapter=text_document_appender,
            project_path=validated_request.project_path,
            container_path=resolved_container_path,
            object_name=validated_request.object_name,
            document_kind=validated_request.document_kind,
        )
        expected_text = current_text + validated_request.text_to_append
        if validated_request.document_kind == "declaration":
            current_implementation = read_document_text(
                adapter=text_document_appender,
                project_path=validated_request.project_path,
                container_path=resolved_container_path,
                object_name=validated_request.object_name,
                document_kind="implementation",
            )
            validate_declaration_implementation_consistency(
                declaration_text=expected_text,
                implementation_text=current_implementation,
                error_cls=AppendTextDocumentValidationError,
            )
        else:
            current_declaration = read_document_text(
                adapter=text_document_appender,
                project_path=validated_request.project_path,
                container_path=resolved_container_path,
                object_name=validated_request.object_name,
                document_kind="declaration",
            )
            validate_declaration_implementation_consistency(
                declaration_text=current_declaration,
                implementation_text=expected_text,
                error_cls=AppendTextDocumentValidationError,
            )
        text_document_appender.append_text_document(
            project_path=validated_request.project_path,
            container_path=resolved_container_path,
            object_name=validated_request.object_name,
            document_kind=validated_request.document_kind,
            text_to_append=validated_request.text_to_append,
        )
        verify_roundtrip_text(
            adapter=text_document_appender,
            project_path=validated_request.project_path,
            container_path=resolved_container_path,
            object_name=validated_request.object_name,
            document_kind=validated_request.document_kind,
            expected_text=expected_text,
            error_cls=AppendTextDocumentValidationError,
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
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except AppendTextDocumentValidationError as exc:
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
            code="TEXT_DOCUMENT_NOT_FOUND",
            message="Target text document could not be resolved.",
            details={"exception": str(exc)},
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except Exception as exc:  # pragma: no cover
        LOGGER.exception(
            "append_text_document failed with unexpected error",
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
            message="Unexpected error while appending text document.",
            details={"exception": str(exc)},
            request_id=resolved_request_id,
            started_at=started_at,
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
