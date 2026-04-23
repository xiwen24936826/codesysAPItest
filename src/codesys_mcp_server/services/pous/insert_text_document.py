"""Insert-text-document service for the first MCP implementation phase."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from typing import Any, Protocol
from uuid import uuid4

from ._common import (
    error_response,
    raise_validation_error,
    read_document_text,
    require_absolute_path,
    require_ascii_text,
    require_document_kind,
    require_non_empty_string,
    require_non_negative_int,
    resolve_effective_container_path,
    success_response,
    validate_declaration_implementation_consistency,
    verify_roundtrip_text,
)


LOGGER = logging.getLogger(__name__)
TOOL_NAME = "insert_text_document"


class TextDocumentInserter(Protocol):
    """Protocol for adapters that can insert text at a fixed offset."""

    def insert_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        text_to_insert: str,
        insertion_offset: int,
    ) -> Any:
        """Insert text into the target document."""

    def read_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
    ) -> Any:
        """Read a textual document in the target project."""


@dataclass(frozen=True)
class InsertTextDocumentRequest:
    """Validated request payload for insert_text_document."""

    project_path: str
    container_path: str
    object_name: str
    document_kind: str
    text_to_insert: str
    insertion_offset: int


@dataclass(frozen=True)
class InsertTextDocumentValidationError(Exception):
    """Validation error for insert_text_document requests."""

    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def insert_text_document(
    request: dict[str, Any],
    text_document_inserter: TextDocumentInserter,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Insert text into the target document and return a structured response."""
    started_at = time.perf_counter()
    resolved_request_id = request_id or str(uuid4())

    try:
        validated_request = _validate_request(request)
        resolved_container_path = resolve_effective_container_path(
            browser=text_document_inserter,
            project_path=validated_request.project_path,
            requested_container_path=validated_request.container_path,
        )
        current_text = read_document_text(
            adapter=text_document_inserter,
            project_path=validated_request.project_path,
            container_path=resolved_container_path,
            object_name=validated_request.object_name,
            document_kind=validated_request.document_kind,
        )
        if validated_request.insertion_offset > len(current_text):
            raise_validation_error(
                error_cls=InsertTextDocumentValidationError,
                message="Field 'insertion_offset' must not exceed the current document length.",
                details={
                    "field": "insertion_offset",
                    "value": validated_request.insertion_offset,
                    "document_length": len(current_text),
                },
            )
        expected_text = (
            current_text[: validated_request.insertion_offset]
            + validated_request.text_to_insert
            + current_text[validated_request.insertion_offset :]
        )
        if validated_request.document_kind == "declaration":
            current_implementation = read_document_text(
                adapter=text_document_inserter,
                project_path=validated_request.project_path,
                container_path=resolved_container_path,
                object_name=validated_request.object_name,
                document_kind="implementation",
            )
            validate_declaration_implementation_consistency(
                declaration_text=expected_text,
                implementation_text=current_implementation,
                error_cls=InsertTextDocumentValidationError,
            )
        else:
            current_declaration = read_document_text(
                adapter=text_document_inserter,
                project_path=validated_request.project_path,
                container_path=resolved_container_path,
                object_name=validated_request.object_name,
                document_kind="declaration",
            )
            validate_declaration_implementation_consistency(
                declaration_text=current_declaration,
                implementation_text=expected_text,
                error_cls=InsertTextDocumentValidationError,
            )
        text_document_inserter.insert_text_document(
            project_path=validated_request.project_path,
            container_path=resolved_container_path,
            object_name=validated_request.object_name,
            document_kind=validated_request.document_kind,
            text_to_insert=validated_request.text_to_insert,
            insertion_offset=validated_request.insertion_offset,
        )
        verify_roundtrip_text(
            adapter=text_document_inserter,
            project_path=validated_request.project_path,
            container_path=resolved_container_path,
            object_name=validated_request.object_name,
            document_kind=validated_request.document_kind,
            expected_text=expected_text,
            error_cls=InsertTextDocumentValidationError,
        )

        response_data = {
            "project_path": validated_request.project_path,
            "container_path": resolved_container_path,
            "object_name": validated_request.object_name,
            "document_kind": validated_request.document_kind,
            "updated": True,
            "inserted_length": len(validated_request.text_to_insert),
            "insertion_offset": validated_request.insertion_offset,
            "roundtrip_verified": True,
        }
        return success_response(
            tool_name=TOOL_NAME,
            data=response_data,
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except InsertTextDocumentValidationError as exc:
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
            "insert_text_document failed with unexpected error",
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
            message="Unexpected error while inserting text document.",
            details={"exception": str(exc)},
            request_id=resolved_request_id,
            started_at=started_at,
        )


def _validate_request(request: dict[str, Any]) -> InsertTextDocumentRequest:
    return InsertTextDocumentRequest(
        project_path=require_absolute_path(
            "project_path",
            request.get("project_path"),
            InsertTextDocumentValidationError,
        ),
        container_path=require_non_empty_string(
            "container_path",
            request.get("container_path"),
            InsertTextDocumentValidationError,
        ),
        object_name=require_non_empty_string(
            "object_name",
            request.get("object_name"),
            InsertTextDocumentValidationError,
        ),
        document_kind=require_document_kind(
            request.get("document_kind"),
            InsertTextDocumentValidationError,
        ),
        text_to_insert=require_ascii_text(
            "text_to_insert",
            require_non_empty_string(
                "text_to_insert",
                request.get("text_to_insert"),
                InsertTextDocumentValidationError,
            ),
            InsertTextDocumentValidationError,
        ),
        insertion_offset=require_non_negative_int(
            "insertion_offset",
            request.get("insertion_offset"),
            InsertTextDocumentValidationError,
        ),
    )
