"""Replace-text-document service for the first MCP implementation phase."""

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
TOOL_NAME = "replace_text_document"


class TextDocumentReplacer(Protocol):
    """Protocol for adapters that can replace textual documents."""

    def replace_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        new_text: str,
    ) -> Any:
        """Replace a textual document in the target project."""

    def read_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
    ) -> Any:
        """Read a textual document in the target project."""


@dataclass(frozen=True)
class ReplaceTextDocumentRequest:
    """Validated request payload for replace_text_document."""

    project_path: str
    container_path: str
    object_name: str
    document_kind: str
    new_text: str


@dataclass(frozen=True)
class ReplaceTextDocumentValidationError(Exception):
    """Validation error for replace_text_document requests."""

    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def replace_text_document(
    request: dict[str, Any],
    text_document_replacer: TextDocumentReplacer,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Replace the target text document and return a structured response."""
    started_at = time.perf_counter()
    resolved_request_id = request_id or str(uuid4())

    try:
        validated_request = _validate_request(request)
        resolved_container_path = resolve_effective_container_path(
            browser=text_document_replacer,
            project_path=validated_request.project_path,
            requested_container_path=validated_request.container_path,
        )
        if validated_request.document_kind == "declaration":
            candidate_declaration = validated_request.new_text
            current_implementation = read_document_text(
                adapter=text_document_replacer,
                project_path=validated_request.project_path,
                container_path=resolved_container_path,
                object_name=validated_request.object_name,
                document_kind="implementation",
            )
            validate_declaration_implementation_consistency(
                declaration_text=candidate_declaration,
                implementation_text=current_implementation,
                error_cls=ReplaceTextDocumentValidationError,
            )
        else:
            current_declaration = read_document_text(
                adapter=text_document_replacer,
                project_path=validated_request.project_path,
                container_path=resolved_container_path,
                object_name=validated_request.object_name,
                document_kind="declaration",
            )
            validate_declaration_implementation_consistency(
                declaration_text=current_declaration,
                implementation_text=validated_request.new_text,
                error_cls=ReplaceTextDocumentValidationError,
            )
        text_document_replacer.replace_text_document(
            project_path=validated_request.project_path,
            container_path=resolved_container_path,
            object_name=validated_request.object_name,
            document_kind=validated_request.document_kind,
            new_text=validated_request.new_text,
        )
        verify_roundtrip_text(
            adapter=text_document_replacer,
            project_path=validated_request.project_path,
            container_path=resolved_container_path,
            object_name=validated_request.object_name,
            document_kind=validated_request.document_kind,
            expected_text=validated_request.new_text,
            error_cls=ReplaceTextDocumentValidationError,
        )

        response_data = {
            "project_path": validated_request.project_path,
            "container_path": resolved_container_path,
            "object_name": validated_request.object_name,
            "document_kind": validated_request.document_kind,
            "updated": True,
            "text_length": len(validated_request.new_text),
            "roundtrip_verified": True,
        }
        return success_response(
            tool_name=TOOL_NAME,
            data=response_data,
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except ReplaceTextDocumentValidationError as exc:
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
            "replace_text_document failed with unexpected error",
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
            message="Unexpected error while replacing text document.",
            details={"exception": str(exc)},
            request_id=resolved_request_id,
            started_at=started_at,
        )


def _validate_request(request: dict[str, Any]) -> ReplaceTextDocumentRequest:
    new_text = request.get("new_text")
    if not isinstance(new_text, str):
        raise ReplaceTextDocumentValidationError(
            message="Field 'new_text' must be a string.",
            details={"field": "new_text", "value": new_text},
        )
    new_text = require_ascii_text(
        "new_text",
        new_text,
        ReplaceTextDocumentValidationError,
    )

    return ReplaceTextDocumentRequest(
        project_path=require_absolute_path(
            "project_path",
            request.get("project_path"),
            ReplaceTextDocumentValidationError,
        ),
        container_path=require_non_empty_string(
            "container_path",
            request.get("container_path"),
            ReplaceTextDocumentValidationError,
        ),
        object_name=require_non_empty_string(
            "object_name",
            request.get("object_name"),
            ReplaceTextDocumentValidationError,
        ),
        document_kind=require_document_kind(
            request.get("document_kind"),
            ReplaceTextDocumentValidationError,
        ),
        new_text=new_text,
    )
