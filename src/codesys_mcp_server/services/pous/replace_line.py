"""Replace-line service for precise textual document updates."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Protocol

from .._service_common import begin_service_call, build_log_extra
from ._common import (
    execute_text_write_flow,
    error_response,
    replace_line_in_text,
    require_absolute_path,
    require_document_kind,
    require_non_empty_string,
    require_positive_int,
    success_response,
)


LOGGER = logging.getLogger(__name__)
TOOL_NAME = "replace_line"


class TextDocumentLineReplacer(Protocol):
    """Protocol for adapters that can replace one document line."""

    def replace_text_line(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        line_number: int,
        new_text: str,
    ) -> Any:
        """Replace one line in a textual document."""

    def read_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
    ) -> Any:
        """Read a textual document in the target project."""


@dataclass(frozen=True)
class ReplaceLineRequest:
    """Validated request payload for replace_line."""

    project_path: str
    container_path: str
    object_name: str
    document_kind: str
    line_number: int
    new_text: str


@dataclass(frozen=True)
class ReplaceLineValidationError(Exception):
    """Validation error for replace_line requests."""

    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def replace_line(
    request: dict[str, Any],
    text_document_line_replacer: TextDocumentLineReplacer,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Replace one line in a declaration or implementation document."""
    service_call = begin_service_call(request_id)

    try:
        validated_request = _validate_request(request)
        resolved_container_path, expected_text = execute_text_write_flow(
            adapter=text_document_line_replacer,
            validated_request=validated_request,
            validation_error_cls=ReplaceLineValidationError,
            build_expected_text=lambda current_text: replace_line_in_text(
                current_text=current_text,
                line_number=validated_request.line_number,
                new_text=validated_request.new_text,
                error_cls=ReplaceLineValidationError,
            ),
            perform_write=lambda container_path: text_document_line_replacer.replace_text_line(
                project_path=validated_request.project_path,
                container_path=container_path,
                object_name=validated_request.object_name,
                document_kind=validated_request.document_kind,
                line_number=validated_request.line_number,
                new_text=validated_request.new_text,
            ),
        )

        response_data = {
            "project_path": validated_request.project_path,
            "container_path": resolved_container_path,
            "object_name": validated_request.object_name,
            "document_kind": validated_request.document_kind,
            "line_number": validated_request.line_number,
            "updated": True,
            "text_length": len(expected_text),
            "roundtrip_verified": True,
        }
        return success_response(
            tool_name=TOOL_NAME,
            data=response_data,
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except ReplaceLineValidationError as exc:
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
            "replace_line failed with unexpected error",
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
            message="Unexpected error while replacing a document line.",
            details={"exception": str(exc)},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )


def _validate_request(request: dict[str, Any]) -> ReplaceLineRequest:
    new_text = request.get("new_text")
    if not isinstance(new_text, str):
        raise ReplaceLineValidationError(
            message="Field 'new_text' must be a string.",
            details={"field": "new_text", "value": new_text},
        )

    return ReplaceLineRequest(
        project_path=require_absolute_path(
            "project_path",
            request.get("project_path"),
            ReplaceLineValidationError,
        ),
        container_path=require_non_empty_string(
            "container_path",
            request.get("container_path"),
            ReplaceLineValidationError,
        ),
        object_name=require_non_empty_string(
            "object_name",
            request.get("object_name"),
            ReplaceLineValidationError,
        ),
        document_kind=require_document_kind(
            request.get("document_kind"),
            ReplaceLineValidationError,
        ),
        line_number=require_positive_int(
            "line_number",
            request.get("line_number"),
            ReplaceLineValidationError,
        ),
        new_text=new_text,
    )
