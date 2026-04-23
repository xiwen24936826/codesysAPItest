"""Project-tree scan service for explicit container discovery."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any, Protocol

from .._service_common import begin_service_call, build_log_extra, error_response, success_response


LOGGER = logging.getLogger(__name__)
TOOL_NAME = "list_project_objects"


class ProjectObjectLister(Protocol):
    """Protocol for adapters that can list child objects in a project tree."""

    def list_objects(
        self,
        project_path: str,
        container_path: str = "/",
    ) -> Any:
        """Return child objects below the target logical container."""


@dataclass(frozen=True)
class ListProjectObjectsRequest:
    """Validated request payload for the list_project_objects tool."""

    project_path: str
    container_path: str = "/"


@dataclass(frozen=True)
class ListProjectObjectsValidationError(Exception):
    """Validation error for list_project_objects requests."""

    message: str
    details: dict[str, Any]
    code: str = "VALIDATION_ERROR"

    def __str__(self) -> str:
        return self.message


def list_project_objects(
    request: dict[str, Any],
    project_object_lister: ProjectObjectLister,
    request_id: str | None = None,
) -> dict[str, Any]:
    """List child objects below a project-tree container."""
    service_call = begin_service_call(request_id)

    try:
        validated_request = _validate_request(request)
        listing = project_object_lister.list_objects(
            project_path=validated_request.project_path,
            container_path=validated_request.container_path,
        )
        response_data = _normalize_listing(
            project_path=validated_request.project_path,
            requested_container_path=validated_request.container_path,
            listing=listing,
        )

        LOGGER.info(
            "list_project_objects succeeded",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="success",
                project_path=validated_request.project_path,
                container_path=response_data["container_path"],
            ),
        )
        return success_response(
            tool_name=TOOL_NAME,
            data=response_data,
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except ListProjectObjectsValidationError as exc:
        LOGGER.warning(
            "list_project_objects validation failed",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="failed",
                error_code=exc.code,
                project_path=request.get("project_path"),
                container_path=request.get("container_path"),
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
        LOGGER.warning(
            "list_project_objects target project was not found",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="failed",
                error_code="PROJECT_NOT_FOUND",
                project_path=request.get("project_path"),
                container_path=request.get("container_path"),
            ),
        )
        return error_response(
            tool_name=TOOL_NAME,
            code="PROJECT_NOT_FOUND",
            message="Project file was not found.",
            details={"project_path": request.get("project_path")},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )
    except LookupError as exc:
        LOGGER.warning(
            "list_project_objects could not resolve container",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="failed",
                error_code="CONTAINER_NOT_FOUND",
                project_path=request.get("project_path"),
                container_path=request.get("container_path", "/"),
            ),
        )
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
            "list_project_objects failed with unexpected error",
            extra=build_log_extra(
                tool_name=TOOL_NAME,
                request_id=service_call.request_id,
                status="failed",
                error_code="INTERNAL_ERROR",
                project_path=request.get("project_path"),
                container_path=request.get("container_path"),
            ),
        )
        return error_response(
            tool_name=TOOL_NAME,
            code="INTERNAL_ERROR",
            message="Unexpected error while listing project objects.",
            details={"exception": str(exc)},
            request_id=service_call.request_id,
            started_at=service_call.started_at,
        )


def _validate_request(request: dict[str, Any]) -> ListProjectObjectsRequest:
    project_path = request.get("project_path")
    if not isinstance(project_path, str) or not project_path.strip():
        raise ListProjectObjectsValidationError(
            message="Field 'project_path' is required.",
            details={"field": "project_path"},
        )

    if not Path(project_path).is_absolute():
        raise ListProjectObjectsValidationError(
            message="Field 'project_path' must be an absolute path.",
            details={"field": "project_path", "value": project_path},
        )

    container_path = request.get("container_path", "/")
    if not isinstance(container_path, str) or not container_path.strip():
        raise ListProjectObjectsValidationError(
            message="Field 'container_path' must be a non-empty string when provided.",
            details={"field": "container_path", "value": container_path},
        )

    return ListProjectObjectsRequest(
        project_path=project_path,
        container_path=container_path.strip(),
    )


def _normalize_listing(
    project_path: str,
    requested_container_path: str,
    listing: Any,
) -> dict[str, Any]:
    if not isinstance(listing, dict):
        raise TypeError("Project object lister returned an unsupported result.")

    resolved_container_path = listing.get("container_path")
    if not isinstance(resolved_container_path, str) or not resolved_container_path.strip():
        resolved_container_path = requested_container_path

    raw_children = listing.get("children", [])
    if not isinstance(raw_children, list):
        raise TypeError("Field 'children' must be a list.")

    children: list[dict[str, Any]] = []
    for child in raw_children:
        if not isinstance(child, dict):
            continue
        name = child.get("name")
        if not isinstance(name, str) or not name:
            continue

        normalized_child = {
            "name": name,
            "path": child.get("path") or _join_container_path(resolved_container_path, name),
            "is_folder": bool(child.get("is_folder", False)),
            "can_browse": bool(child.get("can_browse", child.get("is_folder", False))),
        }
        if "child_count" in child:
            normalized_child["child_count"] = child["child_count"]
        if "object_type" in child:
            normalized_child["object_type"] = child["object_type"]
        children.append(normalized_child)

    return {
        "project_path": project_path,
        "container_path": resolved_container_path,
        "children": children,
    }


def _join_container_path(parent_path: str, child_name: str) -> str:
    normalized_parent = (parent_path or "/").strip("/")
    if not normalized_parent:
        return child_name
    return "%s/%s" % (normalized_parent, child_name)
