"""Edit-POU transaction service for a single-IDE-run workflow."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Protocol

from .._service_common import begin_service_call, build_log_extra
from ._common import (
    error_response,
    require_absolute_path,
    require_non_empty_string,
    success_response,
)


LOGGER = logging.getLogger(__name__)
TOOL_NAME = "edit_pou_transaction"


class PouTransactionEditor(Protocol):
    def edit_pou_transaction(
        self,
        project_path: str,
        container_path: str,
        pou_name: str,
        operations: list[dict[str, Any]],
        verify_mode: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(frozen=True)
class EditPouTransactionRequest:
    project_path: str
    container_path: str
    pou_name: str
    operations: list[dict[str, Any]]
    verify_mode: str = "normalize_newlines"


@dataclass(frozen=True)
class EditPouTransactionValidationError(Exception):
    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def edit_pou_transaction(
    request: dict[str, Any],
    pou_transaction_editor: PouTransactionEditor,
    request_id: str | None = None,
) -> dict[str, Any]:
    service_call = begin_service_call(request_id)

    try:
        validated_request = _validate_request(request)
        transaction_result = pou_transaction_editor.edit_pou_transaction(
            project_path=validated_request.project_path,
            container_path=validated_request.container_path,
            pou_name=validated_request.pou_name,
            operations=validated_request.operations,
            verify_mode=validated_request.verify_mode,
        )
        verification = transaction_result.get("verification", {})
        if isinstance(verification, dict) and verification.get("ok") is False:
            return error_response(
                tool_name=TOOL_NAME,
                code="POU_TRANSACTION_VERIFICATION_FAILED",
                message="POU transaction verification failed.",
                details={
                    "verification": verification,
                    "location": transaction_result.get("location"),
                },
                request_id=service_call.request_id,
                started_at=service_call.started_at,
            )
        response_data = {
            "project_path": validated_request.project_path,
            "requested_container_path": validated_request.container_path,
            "resolved_container_path": transaction_result.get(
                "resolved_container_path", validated_request.container_path
            ),
            "pou_name": validated_request.pou_name,
            "operations_applied": transaction_result.get("operations_applied", []),
            "verification": verification or transaction_result.get(
                "verification",
                {"mode": validated_request.verify_mode, "roundtrip_verified": True},
            ),
            "saved": transaction_result.get("saved", True),
            "closed": transaction_result.get("closed", True),
            "before": transaction_result.get("before"),
            "after": transaction_result.get("after"),
            "location": transaction_result.get("location"),
        }
        return success_response(
            tool_name=TOOL_NAME,
            data=response_data,
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except EditPouTransactionValidationError as exc:
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
            code="TARGET_NOT_FOUND",
            message="Target container or object could not be resolved.",
            details={"exception": str(exc)},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except ValueError as exc:
        return error_response(
            tool_name=TOOL_NAME,
            code="TRANSACTION_VALIDATION_FAILED",
            message=str(exc),
            details={},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except Exception as exc:  # pragma: no cover
        LOGGER.exception(
            "edit_pou_transaction failed with unexpected error",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="failed",
                error_code="INTERNAL_ERROR",
                project_path=request.get("project_path"),
                container_path=request.get("container_path"),
                object_name=request.get("pou_name"),
            ),
        )
        return error_response(
            tool_name=TOOL_NAME,
            code="INTERNAL_ERROR",
            message="Unexpected error while editing POU via transaction.",
            details={"exception": str(exc)},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )


def _validate_request(request: dict[str, Any]) -> EditPouTransactionRequest:
    operations = request.get("operations")
    if not isinstance(operations, list) or len(operations) == 0:
        raise EditPouTransactionValidationError(
            message="Field 'operations' must be a non-empty array.",
            details={"field": "operations", "value": operations},
        )

    for index, operation in enumerate(operations):
        if not isinstance(operation, dict):
            raise EditPouTransactionValidationError(
                message="Each operation must be a JSON object.",
                details={"index": index, "value": operation},
            )
        document_kind = operation.get("document_kind")
        if document_kind not in ("declaration", "implementation"):
            raise EditPouTransactionValidationError(
                message="Operation field 'document_kind' must be declaration or implementation.",
                details={"index": index, "field": "document_kind", "value": document_kind},
            )
        op = operation.get("op")
        if op not in ("replace", "append", "insert", "replace_line"):
            raise EditPouTransactionValidationError(
                message="Operation field 'op' must be one of: replace, append, insert, replace_line.",
                details={"index": index, "field": "op", "value": op},
            )
        if op == "replace":
            new_text = operation.get("new_text")
            if not isinstance(new_text, str):
                raise EditPouTransactionValidationError(
                    message="Operation field 'new_text' must be a string for replace.",
                    details={"index": index, "field": "new_text", "value": new_text},
                )
        if op == "append":
            text = operation.get("text")
            if not isinstance(text, str):
                raise EditPouTransactionValidationError(
                    message="Operation field 'text' must be a string for append.",
                    details={"index": index, "field": "text", "value": text},
                )
        if op == "insert":
            text = operation.get("text")
            offset = operation.get("offset")
            if not isinstance(text, str) or not isinstance(offset, int):
                raise EditPouTransactionValidationError(
                    message="Operation fields 'text' (string) and 'offset' (integer) are required for insert.",
                    details={"index": index, "text": text, "offset": offset},
                )
        if op == "replace_line":
            new_text = operation.get("new_text")
            line_number = operation.get("line_number")
            if not isinstance(new_text, str) or not isinstance(line_number, int):
                raise EditPouTransactionValidationError(
                    message="Operation fields 'new_text' (string) and 'line_number' (integer) are required for replace_line.",
                    details={"index": index, "new_text": new_text, "line_number": line_number},
                )

    verify_mode = request.get("verify_mode", "normalize_newlines")
    if verify_mode not in ("exact", "normalize_newlines"):
        raise EditPouTransactionValidationError(
            message="Field 'verify_mode' must be one of: exact, normalize_newlines.",
            details={"field": "verify_mode", "value": verify_mode},
        )

    return EditPouTransactionRequest(
        project_path=require_absolute_path(
            "project_path",
            request.get("project_path"),
            EditPouTransactionValidationError,
        ),
        container_path=require_non_empty_string(
            "container_path",
            request.get("container_path"),
            EditPouTransactionValidationError,
        ),
        pou_name=require_non_empty_string(
            "pou_name",
            request.get("pou_name"),
            EditPouTransactionValidationError,
        ),
        operations=operations,
        verify_mode=verify_mode,
    )
