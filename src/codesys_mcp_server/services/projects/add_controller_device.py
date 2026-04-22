"""Add-controller-device service for the first MCP implementation phase."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
import time
from typing import Any, Protocol
from uuid import uuid4


LOGGER = logging.getLogger(__name__)
TOOL_NAME = "add_controller_device"


class ControllerDeviceAdder(Protocol):
    """Protocol for adapters that can add a top-level controller device."""

    def add_controller(
        self,
        project_path: str,
        device_name: str,
        device_type: int | str,
        device_id: str,
        device_version: str,
        module: str | None = None,
    ) -> Any:
        """Add a top-level controller device to the target project."""


@dataclass(frozen=True)
class AddControllerDeviceRequest:
    """Validated request payload for the add_controller_device tool."""

    project_path: str
    device_name: str
    device_type: int | str
    device_id: str
    device_version: str
    module: str | None = None


@dataclass(frozen=True)
class AddControllerDeviceValidationError(Exception):
    """Validation error for add_controller_device requests."""

    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def add_controller_device(
    request: dict[str, Any],
    controller_device_adder: ControllerDeviceAdder,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Add a controller device and return a structured MCP-style response."""
    started_at = time.perf_counter()
    resolved_request_id = request_id or str(uuid4())

    try:
        validated_request = _validate_request(request)

        controller_device_adder.add_controller(
            project_path=validated_request.project_path,
            device_name=validated_request.device_name,
            device_type=validated_request.device_type,
            device_id=validated_request.device_id,
            device_version=validated_request.device_version,
            module=validated_request.module,
        )

        response_data = {
            "project_path": validated_request.project_path,
            "device_name": validated_request.device_name,
            "device_type": validated_request.device_type,
            "device_id": validated_request.device_id,
            "device_version": validated_request.device_version,
            "module": validated_request.module,
        }

        LOGGER.info(
            "add_controller_device succeeded",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": validated_request.project_path,
                "device_name": validated_request.device_name,
                "device_type": validated_request.device_type,
                "status": "success",
            },
        )
        return _success_response(
            data=response_data,
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except AddControllerDeviceValidationError as exc:
        LOGGER.warning(
            "add_controller_device validation failed",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": request.get("project_path"),
                "device_name": request.get("device_name"),
                "device_type": request.get("device_type"),
                "status": "failed",
                "error_code": exc.code,
            },
        )
        return _error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except FileNotFoundError:
        LOGGER.warning(
            "add_controller_device target project was not found",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": request.get("project_path"),
                "device_name": request.get("device_name"),
                "status": "failed",
                "error_code": "PROJECT_NOT_FOUND",
            },
        )
        return _error_response(
            code="PROJECT_NOT_FOUND",
            message="Project file was not found.",
            details={"project_path": request.get("project_path")},
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except LookupError as exc:
        LOGGER.warning(
            "add_controller_device could not resolve device metadata",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": request.get("project_path"),
                "device_name": request.get("device_name"),
                "device_type": request.get("device_type"),
                "status": "failed",
                "error_code": "DEVICE_TYPE_NOT_FOUND",
            },
        )
        return _error_response(
            code="DEVICE_TYPE_NOT_FOUND",
            message="Controller device metadata could not be resolved.",
            details={
                "device_type": request.get("device_type"),
                "device_id": request.get("device_id"),
                "device_version": request.get("device_version"),
                "exception": str(exc),
            },
            request_id=resolved_request_id,
            started_at=started_at,
        )
    except Exception as exc:  # pragma: no cover - adapter safety net
        LOGGER.exception(
            "add_controller_device failed with unexpected error",
            extra={
                "tool": TOOL_NAME,
                "request_id": resolved_request_id,
                "project_path": request.get("project_path"),
                "device_name": request.get("device_name"),
                "device_type": request.get("device_type"),
                "status": "failed",
                "error_code": "DEVICE_INSERT_FAILED",
            },
        )
        return _error_response(
            code="DEVICE_INSERT_FAILED",
            message="Unexpected error while adding controller device.",
            details={"exception": str(exc)},
            request_id=resolved_request_id,
            started_at=started_at,
        )


def _validate_request(request: dict[str, Any]) -> AddControllerDeviceRequest:
    project_path = request.get("project_path")
    device_name = request.get("device_name")
    device_type = request.get("device_type")
    device_id = request.get("device_id")
    device_version = request.get("device_version")
    module = request.get("module")

    if not isinstance(project_path, str) or not project_path.strip():
        raise AddControllerDeviceValidationError(
            message="Field 'project_path' is required.",
            details={"field": "project_path"},
        )

    if not Path(project_path).is_absolute():
        raise AddControllerDeviceValidationError(
            message="Field 'project_path' must be an absolute path.",
            details={"field": "project_path", "value": project_path},
        )

    if not isinstance(device_name, str) or not device_name.strip():
        raise AddControllerDeviceValidationError(
            message="Field 'device_name' is required.",
            details={"field": "device_name"},
        )

    if not _is_valid_device_type(device_type):
        raise AddControllerDeviceValidationError(
            message="Field 'device_type' must be a non-empty string or an integer.",
            details={"field": "device_type", "value": device_type},
        )

    if not isinstance(device_id, str) or not device_id.strip():
        raise AddControllerDeviceValidationError(
            message="Field 'device_id' is required.",
            details={"field": "device_id"},
        )

    if not isinstance(device_version, str) or not device_version.strip():
        raise AddControllerDeviceValidationError(
            message="Field 'device_version' is required.",
            details={"field": "device_version"},
        )

    if module is not None and (not isinstance(module, str) or not module.strip()):
        raise AddControllerDeviceValidationError(
            message="Field 'module' must be a non-empty string when provided.",
            details={"field": "module", "value": module},
        )

    return AddControllerDeviceRequest(
        project_path=project_path,
        device_name=device_name,
        device_type=device_type,
        device_id=device_id,
        device_version=device_version,
        module=module,
    )


def _is_valid_device_type(value: Any) -> bool:
    return isinstance(value, int) or (isinstance(value, str) and bool(value.strip()))


def _success_response(
    data: dict[str, Any],
    request_id: str,
    started_at: float,
) -> dict[str, Any]:
    return {
        "ok": True,
        "tool": TOOL_NAME,
        "data": data,
        "error": None,
        "meta": _build_meta(request_id=request_id, started_at=started_at),
    }


def _error_response(
    code: str,
    message: str,
    details: dict[str, Any],
    request_id: str,
    started_at: float,
) -> dict[str, Any]:
    return {
        "ok": False,
        "tool": TOOL_NAME,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "meta": _build_meta(request_id=request_id, started_at=started_at),
    }


def _build_meta(request_id: str, started_at: float) -> dict[str, Any]:
    return {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "request_id": request_id,
        "duration_ms": round((time.perf_counter() - started_at) * 1000),
    }

