"""Network-scan service for online device discovery."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Protocol

from .._service_common import begin_service_call, build_log_extra, error_response, success_response


LOGGER = logging.getLogger(__name__)
TOOL_NAME = "scan_network_devices"


class NetworkDeviceScanner(Protocol):
    """Protocol for adapters that can scan gateways for online devices."""

    def scan_network_devices(
        self,
        gateway_name: str | None = None,
        use_cached_result: bool = False,
    ) -> Any:
        """Return scanned online targets for one gateway."""


@dataclass(frozen=True)
class ScanNetworkDevicesRequest:
    """Validated request payload for scan_network_devices."""

    gateway_name: str | None = None
    use_cached_result: bool = False


@dataclass(frozen=True)
class ScanNetworkDevicesValidationError(Exception):
    """Validation error for scan_network_devices requests."""

    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def scan_network_devices(
    request: dict[str, Any],
    network_device_scanner: NetworkDeviceScanner,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Scan online devices through the configured gateway."""
    service_call = begin_service_call(request_id)

    try:
        validated_request = _validate_request(request)
        result = network_device_scanner.scan_network_devices(
            gateway_name=validated_request.gateway_name,
            use_cached_result=validated_request.use_cached_result,
        )
        response_data = _normalize_scan_result(validated_request, result)
        LOGGER.info(
            "scan_network_devices succeeded",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="success",
                gateway_name=response_data["gateway_name"],
                target_count=len(response_data["targets"]),
            ),
        )
        return success_response(
            tool_name=TOOL_NAME,
            data=response_data,
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except ScanNetworkDevicesValidationError as exc:
        LOGGER.warning(
            "scan_network_devices validation failed",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="failed",
                error_code=exc.code,
                gateway_name=request.get("gateway_name"),
            ),
        )
        return error_response(
            tool_name=TOOL_NAME,
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except LookupError as exc:
        return error_response(
            tool_name=TOOL_NAME,
            code="GATEWAY_NOT_FOUND",
            message="Requested gateway could not be resolved.",
            details={"gateway_name": request.get("gateway_name"), "exception": str(exc)},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except Exception as exc:  # pragma: no cover - adapter safety net
        LOGGER.exception(
            "scan_network_devices failed with unexpected error",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="failed",
                error_code="INTERNAL_ERROR",
                gateway_name=request.get("gateway_name"),
            ),
        )
        return error_response(
            tool_name=TOOL_NAME,
            code="INTERNAL_ERROR",
            message="Unexpected error while scanning network devices.",
            details={"exception": str(exc)},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )


def _validate_request(request: dict[str, Any]) -> ScanNetworkDevicesRequest:
    gateway_name = request.get("gateway_name")
    if gateway_name is not None:
        if not isinstance(gateway_name, str) or not gateway_name.strip():
            raise ScanNetworkDevicesValidationError(
                message="Field 'gateway_name' must be a non-empty string when provided.",
                details={"field": "gateway_name", "value": gateway_name},
            )
        gateway_name = gateway_name.strip()

    use_cached_result = request.get("use_cached_result", False)
    if not isinstance(use_cached_result, bool):
        raise ScanNetworkDevicesValidationError(
            message="Field 'use_cached_result' must be a boolean when provided.",
            details={"field": "use_cached_result", "value": use_cached_result},
        )

    return ScanNetworkDevicesRequest(
        gateway_name=gateway_name,
        use_cached_result=use_cached_result,
    )


def _normalize_scan_result(
    validated_request: ScanNetworkDevicesRequest,
    result: Any,
) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise TypeError("Network device scanner returned an unsupported result.")

    gateway_name = result.get("gateway_name") or validated_request.gateway_name
    if not isinstance(gateway_name, str) or not gateway_name:
        raise TypeError("Field 'gateway_name' must be present in the normalized result.")

    targets = result.get("targets", [])
    if not isinstance(targets, list):
        raise TypeError("Field 'targets' must be a list.")

    normalized_targets: list[dict[str, Any]] = []
    for target in targets:
        if not isinstance(target, dict):
            continue
        normalized_target = {
            "device_name": target.get("device_name"),
            "type_name": target.get("type_name"),
            "vendor_name": target.get("vendor_name"),
            "device_id": target.get("device_id"),
            "address": target.get("address"),
            "parent_address": target.get("parent_address"),
            "block_driver": target.get("block_driver"),
            "block_driver_address": target.get("block_driver_address"),
        }
        normalized_targets.append(normalized_target)

    return {
        "gateway_name": gateway_name,
        "gateway_guid": result.get("gateway_guid"),
        "use_cached_result": bool(result.get("use_cached_result", validated_request.use_cached_result)),
        "targets": normalized_targets,
    }
