"""Project-tree search service for explicit object lookup."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any, Protocol

from .._service_common import begin_service_call, build_log_extra, error_response, success_response


LOGGER = logging.getLogger(__name__)
TOOL_NAME = "find_project_objects"


class ProjectObjectFinder(Protocol):
    """Protocol for adapters that can search objects in a project tree."""

    def find_objects(
        self,
        project_path: str,
        object_name: str,
        container_path: str = "/",
        recursive: bool = True,
    ) -> Any:
        """Return matching objects below the target logical container."""


@dataclass(frozen=True)
class FindProjectObjectsRequest:
    """Validated request payload for the find_project_objects tool."""

    project_path: str
    object_name: str
    container_path: str = "/"
    recursive: bool = True


@dataclass(frozen=True)
class FindProjectObjectsValidationError(Exception):
    """Validation error for find_project_objects requests."""

    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def find_project_objects(
    request: dict[str, Any],
    project_object_finder: ProjectObjectFinder,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Find matching objects below a project-tree container."""
    service_call = begin_service_call(request_id)

    try:
        validated_request = _validate_request(request)
        listing = project_object_finder.find_objects(
            project_path=validated_request.project_path,
            object_name=validated_request.object_name,
            container_path=validated_request.container_path,
            recursive=validated_request.recursive,
        )
        response_data = _normalize_matches(
            project_path=validated_request.project_path,
            requested_container_path=validated_request.container_path,
            object_name=validated_request.object_name,
            recursive=validated_request.recursive,
            listing=listing,
        )

        LOGGER.info(
            "find_project_objects succeeded",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="success",
                project_path=validated_request.project_path,
                container_path=response_data["container_path"],
                object_name=validated_request.object_name,
                match_count=len(response_data["matches"]),
            ),
        )
        return success_response(
            tool_name=TOOL_NAME,
            data=response_data,
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except FindProjectObjectsValidationError as exc:
        LOGGER.warning(
            "find_project_objects validation failed",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="failed",
                error_code=exc.code,
                project_path=request.get("project_path"),
                container_path=request.get("container_path"),
                object_name=request.get("object_name"),
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
            code="CONTAINER_NOT_FOUND",
            message="Project container could not be resolved.",
            details={
                "container_path": request.get("container_path", "/"),
                "exception": str(exc),
            },
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except Exception as exc:  # pragma: no cover - adapter safety net
        LOGGER.exception(
            "find_project_objects failed with unexpected error",
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
            message="Unexpected error while finding project objects.",
            details={"exception": str(exc)},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )


def _validate_request(request: dict[str, Any]) -> FindProjectObjectsRequest:
    project_path = request.get("project_path")
    if not isinstance(project_path, str) or not project_path.strip():
        raise FindProjectObjectsValidationError(
            message="Field 'project_path' is required.",
            details={"field": "project_path"},
        )

    if not Path(project_path).is_absolute():
        raise FindProjectObjectsValidationError(
            message="Field 'project_path' must be an absolute path.",
            details={"field": "project_path", "value": project_path},
        )

    object_name = request.get("object_name")
    if not isinstance(object_name, str) or not object_name.strip():
        raise FindProjectObjectsValidationError(
            message="Field 'object_name' is required.",
            details={"field": "object_name"},
        )

    container_path = request.get("container_path", "/")
    if not isinstance(container_path, str) or not container_path.strip():
        raise FindProjectObjectsValidationError(
            message="Field 'container_path' must be a non-empty string when provided.",
            details={"field": "container_path", "value": container_path},
        )

    recursive = request.get("recursive", True)
    if not isinstance(recursive, bool):
        raise FindProjectObjectsValidationError(
            message="Field 'recursive' must be a boolean when provided.",
            details={"field": "recursive", "value": recursive},
        )

    return FindProjectObjectsRequest(
        project_path=project_path,
        object_name=object_name.strip(),
        container_path=container_path.strip(),
        recursive=recursive,
    )


def _normalize_matches(
    project_path: str,
    requested_container_path: str,
    object_name: str,
    recursive: bool,
    listing: Any,
) -> dict[str, Any]:
    if not isinstance(listing, dict):
        raise TypeError("Project object finder returned an unsupported result.")

    resolved_container_path = listing.get("container_path")
    if not isinstance(resolved_container_path, str) or not resolved_container_path.strip():
        resolved_container_path = requested_container_path

    raw_matches = listing.get("matches", [])
    if not isinstance(raw_matches, list):
        raise TypeError("Field 'matches' must be a list.")

    matches: list[dict[str, Any]] = []
    for match in raw_matches:
        if not isinstance(match, dict):
            continue
        name = match.get("name")
        if not isinstance(name, str) or not name:
            continue

        normalized_match = {
            "name": name,
            "path": match.get("path"),
            "is_folder": bool(match.get("is_folder", False)),
            "can_browse": bool(match.get("can_browse", match.get("is_folder", False))),
            "is_device": bool(match.get("is_device", False)),
        }
        if "child_count" in match:
            normalized_match["child_count"] = match["child_count"]
        if "object_type" in match:
            normalized_match["object_type"] = match["object_type"]
        device_identification = match.get("device_identification")
        if isinstance(device_identification, dict):
            normalized_match["device_identification"] = device_identification
        elif device_identification is None:
            normalized_match["device_identification"] = None
        matches.append(normalized_match)

    return {
        "project_path": project_path,
        "container_path": resolved_container_path,
        "object_name": object_name,
        "recursive": recursive,
        "matches": matches,
    }
