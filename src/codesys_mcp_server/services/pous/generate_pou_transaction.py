"""Generate-POU transaction service for a single-IDE-run workflow."""

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
TOOL_NAME = "generate_pou_transaction"


class PouTransactionGenerator(Protocol):
    def generate_pou_transaction(
        self,
        project_path: str,
        container_path: str,
        pou_name: str,
        pou_kind: str,
        declaration_text: str,
        implementation_text: str,
        language: str | None = None,
        return_type: str | None = None,
        base_type: str | None = None,
        interfaces: list[str] | None = None,
        write_strategy: str | None = None,
        verify_mode: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(frozen=True)
class GeneratePouTransactionRequest:
    project_path: str
    container_path: str
    pou_name: str
    pou_kind: str
    declaration_text: str
    implementation_text: str
    language: str | None = None
    return_type: str | None = None
    base_type: str | None = None
    interfaces: list[str] | None = None
    write_strategy: str = "replace"
    verify_mode: str = "normalize_newlines"


@dataclass(frozen=True)
class GeneratePouTransactionValidationError(Exception):
    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def generate_pou_transaction(
    request: dict[str, Any],
    pou_transaction_generator: PouTransactionGenerator,
    request_id: str | None = None,
) -> dict[str, Any]:
    service_call = begin_service_call(request_id)

    try:
        validated_request = _validate_request(request)
        transaction_result = pou_transaction_generator.generate_pou_transaction(
            project_path=validated_request.project_path,
            container_path=validated_request.container_path,
            pou_name=validated_request.pou_name,
            pou_kind=validated_request.pou_kind,
            declaration_text=validated_request.declaration_text,
            implementation_text=validated_request.implementation_text,
            language=validated_request.language,
            return_type=validated_request.return_type,
            base_type=validated_request.base_type,
            interfaces=validated_request.interfaces,
            write_strategy=validated_request.write_strategy,
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
            "pou_kind": validated_request.pou_kind,
            "language": transaction_result.get("language", validated_request.language or "ST"),
            "created": transaction_result.get("created", True),
            "written": transaction_result.get(
                "written",
                {"declaration": True, "implementation": True},
            ),
            "verification": verification or transaction_result.get(
                "verification",
                {
                    "mode": validated_request.verify_mode,
                    "declaration_roundtrip_verified": True,
                    "implementation_roundtrip_verified": True,
                },
            ),
            "saved": transaction_result.get("saved", True),
            "closed": transaction_result.get("closed", True),
            "location": transaction_result.get("location"),
        }
        return success_response(
            tool_name=TOOL_NAME,
            data=response_data,
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except GeneratePouTransactionValidationError as exc:
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
            "generate_pou_transaction failed with unexpected error",
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
            message="Unexpected error while generating POU via transaction.",
            details={"exception": str(exc)},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )


def _validate_request(request: dict[str, Any]) -> GeneratePouTransactionRequest:
    pou_kind = request.get("pou_kind")
    if pou_kind not in ("program", "function_block", "function"):
        raise GeneratePouTransactionValidationError(
            message="Field 'pou_kind' must be one of: program, function_block, function.",
            details={"field": "pou_kind", "value": pou_kind},
        )

    declaration_text = request.get("declaration_text")
    if not isinstance(declaration_text, str):
        raise GeneratePouTransactionValidationError(
            message="Field 'declaration_text' must be a string.",
            details={"field": "declaration_text", "value": declaration_text},
        )

    implementation_text = request.get("implementation_text")
    if not isinstance(implementation_text, str):
        raise GeneratePouTransactionValidationError(
            message="Field 'implementation_text' must be a string.",
            details={"field": "implementation_text", "value": implementation_text},
        )

    interfaces = request.get("interfaces")
    if interfaces is not None and not (
        isinstance(interfaces, list) and all(isinstance(item, str) for item in interfaces)
    ):
        raise GeneratePouTransactionValidationError(
            message="Field 'interfaces' must be an array of strings.",
            details={"field": "interfaces", "value": interfaces},
        )

    write_strategy = request.get("write_strategy", "replace")
    if write_strategy not in ("replace",):
        raise GeneratePouTransactionValidationError(
            message="Field 'write_strategy' must be 'replace'.",
            details={"field": "write_strategy", "value": write_strategy},
        )

    verify_mode = request.get("verify_mode", "normalize_newlines")
    if verify_mode not in ("exact", "normalize_newlines"):
        raise GeneratePouTransactionValidationError(
            message="Field 'verify_mode' must be one of: exact, normalize_newlines.",
            details={"field": "verify_mode", "value": verify_mode},
        )

    return_type = request.get("return_type")
    if pou_kind == "function" and not isinstance(return_type, str):
        raise GeneratePouTransactionValidationError(
            message="Field 'return_type' must be provided for function POUs.",
            details={"field": "return_type", "value": return_type},
        )

    language = request.get("language")
    if language is not None and not isinstance(language, str):
        raise GeneratePouTransactionValidationError(
            message="Field 'language' must be a string.",
            details={"field": "language", "value": language},
        )

    base_type = request.get("base_type")
    if base_type is not None and not isinstance(base_type, str):
        raise GeneratePouTransactionValidationError(
            message="Field 'base_type' must be a string.",
            details={"field": "base_type", "value": base_type},
        )

    return GeneratePouTransactionRequest(
        project_path=require_absolute_path(
            "project_path",
            request.get("project_path"),
            GeneratePouTransactionValidationError,
        ),
        container_path=require_non_empty_string(
            "container_path",
            request.get("container_path"),
            GeneratePouTransactionValidationError,
        ),
        pou_name=require_non_empty_string(
            "pou_name",
            request.get("pou_name"),
            GeneratePouTransactionValidationError,
        ),
        pou_kind=pou_kind,
        declaration_text=declaration_text,
        implementation_text=implementation_text,
        language=language,
        return_type=return_type,
        base_type=base_type,
        interfaces=interfaces,
        write_strategy=write_strategy,
        verify_mode=verify_mode,
    )
