"""Shared helpers for POU services."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import time
from typing import Any


DEFAULT_LANGUAGE = "ST"
VALID_DOCUMENT_KINDS = {"declaration", "implementation"}
DEFAULT_CONTAINER_ALIASES = {"/", "Application", "/Application"}
APPLICATION_CONTAINER_NAME = "Application"


def success_response(
    tool_name: str,
    data: dict[str, Any],
    request_id: str,
    started_at: float,
) -> dict[str, Any]:
    return {
        "ok": True,
        "tool": tool_name,
        "data": data,
        "error": None,
        "meta": build_meta(request_id=request_id, started_at=started_at),
    }


def error_response(
    tool_name: str,
    code: str,
    message: str,
    details: dict[str, Any],
    request_id: str,
    started_at: float,
) -> dict[str, Any]:
    return {
        "ok": False,
        "tool": tool_name,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "meta": build_meta(request_id=request_id, started_at=started_at),
    }


def build_meta(request_id: str, started_at: float) -> dict[str, Any]:
    return {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "request_id": request_id,
        "duration_ms": round((time.perf_counter() - started_at) * 1000),
    }


def require_absolute_path(
    field: str,
    value: Any,
    error_cls: type[Exception],
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise error_cls(
            message="Field '%s' is required." % field,
            details={"field": field},
        )

    if not Path(value).is_absolute():
        raise error_cls(
            message="Field '%s' must be an absolute path." % field,
            details={"field": field, "value": value},
        )

    return value


def require_non_empty_string(
    field: str,
    value: Any,
    error_cls: type[Exception],
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise error_cls(
            message="Field '%s' is required." % field,
            details={"field": field},
        )
    return value.strip()


def optional_non_empty_string(
    field: str,
    value: Any,
    error_cls: type[Exception],
) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str) or not value.strip():
        raise error_cls(
            message="Field '%s' must be a non-empty string when provided." % field,
            details={"field": field, "value": value},
        )
    return value.strip()


def resolve_language(
    value: Any,
    error_cls: type[Exception],
) -> str:
    if value is None:
        return DEFAULT_LANGUAGE

    if not isinstance(value, str) or not value.strip():
        raise error_cls(
            message="Field 'language' must be a non-empty string when provided.",
            details={"field": "language", "value": value},
        )
    return value.strip().upper()


def require_document_kind(
    value: Any,
    error_cls: type[Exception],
) -> str:
    if not isinstance(value, str) or value not in VALID_DOCUMENT_KINDS:
        raise error_cls(
            message="Field 'document_kind' must be one of: declaration, implementation.",
            details={"field": "document_kind", "value": value},
        )
    return value


def require_string_list(
    field: str,
    value: Any,
    error_cls: type[Exception],
) -> list[str]:
    if value is None:
        return []

    if not isinstance(value, list):
        raise error_cls(
            message="Field '%s' must be a list of strings when provided." % field,
            details={"field": field, "value": value},
        )

    cleaned: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise error_cls(
                message="Field '%s' must contain only non-empty strings." % field,
                details={"field": field, "value": value},
            )
        cleaned.append(item.strip())

    return cleaned


def require_non_negative_int(
    field: str,
    value: Any,
    error_cls: type[Exception],
) -> int:
    if not isinstance(value, int) or value < 0:
        raise error_cls(
            message="Field '%s' must be a non-negative integer." % field,
            details={"field": field, "value": value},
        )
    return value


def extract_text(result: Any) -> str:
    if isinstance(result, dict):
        text = result.get("text")
        if isinstance(text, str):
            return text
    if isinstance(result, str):
        return result
    raise TypeError("Text document adapter returned an unsupported result.")


def require_ascii_text(
    field: str,
    value: str,
    error_cls: type[Exception],
) -> str:
    try:
        value.encode("ascii")
    except UnicodeEncodeError:
        raise error_cls(
            message=(
                "Field '%s' must contain ASCII-only source text. "
                "Non-ASCII comments or literals are currently not supported "
                "by the real IDE automation path."
            )
            % field,
            details={"field": field, "value": value},
            code="NON_ASCII_TEXT_UNSUPPORTED",
        )
    return value


def resolve_effective_container_path(
    browser: Any,
    project_path: str,
    requested_container_path: str,
) -> str:
    normalized = (requested_container_path or "").strip()
    if normalized not in DEFAULT_CONTAINER_ALIASES:
        return requested_container_path

    if not hasattr(browser, "list_objects"):
        return requested_container_path

    discovered = _find_named_container_path(
        browser=browser,
        project_path=project_path,
        target_name=APPLICATION_CONTAINER_NAME,
    )
    return discovered or requested_container_path


def _find_named_container_path(
    browser: Any,
    project_path: str,
    target_name: str,
    max_depth: int = 8,
) -> str | None:
    queue: list[tuple[str, int]] = [("/", 0)]
    seen: set[str] = set()

    while queue:
        current_path, depth = queue.pop(0)
        if current_path in seen or depth > max_depth:
            continue
        seen.add(current_path)

        listing = browser.list_objects(
            project_path=project_path,
            container_path=current_path,
        )
        children = listing.get("children", []) if isinstance(listing, dict) else []

        for child in children:
            if not isinstance(child, dict):
                continue
            child_name = child.get("name")
            if not isinstance(child_name, str) or not child_name:
                continue

            child_path = _join_container_path(current_path, child_name)
            if child_name == target_name:
                return child_path
            queue.append((child_path, depth + 1))

    return None


def _join_container_path(parent_path: str, child_name: str) -> str:
    if parent_path in ("", "/"):
        return child_name
    return "%s/%s" % (parent_path.strip("/"), child_name)
