"""Shared helpers for POU services."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Callable

from .._service_common import build_meta, error_response, success_response


DEFAULT_LANGUAGE = "ST"
VALID_DOCUMENT_KINDS = {"declaration", "implementation"}
DEFAULT_CONTAINER_ALIASES = {"/", "Application", "/Application"}
APPLICATION_CONTAINER_NAME = "Application"
IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
VAR_BLOCK_PATTERN = re.compile(r"\bVAR(?:_[A-Z]+)?\b(.*?)\bEND_VAR\b", re.IGNORECASE | re.DOTALL)
ST_KEYWORDS = {
    "AND",
    "ARRAY",
    "BY",
    "CASE",
    "CONSTANT",
    "DO",
    "ELSE",
    "ELSIF",
    "END_CASE",
    "END_FOR",
    "END_FUNCTION",
    "END_FUNCTION_BLOCK",
    "END_IF",
    "END_METHOD",
    "END_PROGRAM",
    "END_REPEAT",
    "END_VAR",
    "END_WHILE",
    "EXIT",
    "FALSE",
    "FOR",
    "FUNCTION",
    "FUNCTION_BLOCK",
    "IF",
    "MOD",
    "NOT",
    "OF",
    "OR",
    "PROGRAM",
    "REPEAT",
    "RETURN",
    "THEN",
    "TO",
    "TRUE",
    "UNTIL",
    "VAR",
    "VAR_INPUT",
    "VAR_IN_OUT",
    "VAR_OUTPUT",
    "VAR_TEMP",
    "WHILE",
    "XOR",
}
IEC_TYPES = {
    "BOOL",
    "BYTE",
    "DATE",
    "DATE_AND_TIME",
    "DINT",
    "DWORD",
    "INT",
    "LDATE",
    "LDATE_AND_TIME",
    "LINT",
    "LREAL",
    "LTIME",
    "REAL",
    "SINT",
    "STRING",
    "TIME",
    "TIME_OF_DAY",
    "TOD",
    "UDINT",
    "UINT",
    "ULINT",
    "USINT",
    "WORD",
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


def require_positive_int(
    field: str,
    value: Any,
    error_cls: type[Exception],
) -> int:
    if not isinstance(value, int) or value <= 0:
        raise error_cls(
            message="Field '%s' must be a positive integer." % field,
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


def raise_validation_error(
    error_cls: type[Exception],
    message: str,
    details: dict[str, Any],
    code: str = "VALIDATION_ERROR",
) -> None:
    raise error_cls(message=message, details=details, code=code)


def read_document_text(
    adapter: Any,
    project_path: str,
    container_path: str,
    object_name: str,
    document_kind: str,
) -> str:
    result = adapter.read_text_document(
        project_path=project_path,
        container_path=container_path,
        object_name=object_name,
        document_kind=document_kind,
    )
    return extract_text(result)


def verify_roundtrip_text(
    adapter: Any,
    project_path: str,
    container_path: str,
    object_name: str,
    document_kind: str,
    expected_text: str,
    error_cls: type[Exception],
) -> str:
    actual_text = read_document_text(
        adapter=adapter,
        project_path=project_path,
        container_path=container_path,
        object_name=object_name,
        document_kind=document_kind,
    )
    if actual_text == expected_text:
        return actual_text

    normalized_expected = _normalize_st_newlines(expected_text)
    normalized_actual = _normalize_st_newlines(actual_text)
    if normalized_actual == normalized_expected:
        return actual_text

    if actual_text != expected_text:
        raise_validation_error(
            error_cls=error_cls,
            message="Text write verification failed after round-trip readback.",
            details={
                "document_kind": document_kind,
                "expected_length": len(expected_text),
                "actual_length": len(actual_text),
                "mismatch_index": _first_mismatch_index(expected_text, actual_text),
                "expected_length_normalized": len(normalized_expected),
                "actual_length_normalized": len(normalized_actual),
                "mismatch_index_normalized": _first_mismatch_index(
                    normalized_expected, normalized_actual
                ),
            },
            code="TEXT_ROUNDTRIP_VERIFICATION_FAILED",
        )
    return actual_text


def _normalize_st_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def execute_text_write_flow(
    *,
    adapter: Any,
    validated_request: Any,
    validation_error_cls: type[Exception],
    build_expected_text: Callable[[str], str],
    perform_write: Callable[[str], None],
) -> tuple[str, str]:
    resolved_container_path = resolve_effective_container_path(
        browser=adapter,
        project_path=validated_request.project_path,
        requested_container_path=validated_request.container_path,
    )

    current_text = read_document_text(
        adapter=adapter,
        project_path=validated_request.project_path,
        container_path=resolved_container_path,
        object_name=validated_request.object_name,
        document_kind=validated_request.document_kind,
    )
    expected_text = build_expected_text(current_text)

    if validated_request.document_kind == "declaration":
        current_implementation = read_document_text(
            adapter=adapter,
            project_path=validated_request.project_path,
            container_path=resolved_container_path,
            object_name=validated_request.object_name,
            document_kind="implementation",
        )
        validate_declaration_implementation_consistency(
            declaration_text=expected_text,
            implementation_text=current_implementation,
            error_cls=validation_error_cls,
        )
    else:
        current_declaration = read_document_text(
            adapter=adapter,
            project_path=validated_request.project_path,
            container_path=resolved_container_path,
            object_name=validated_request.object_name,
            document_kind="declaration",
        )
        validate_declaration_implementation_consistency(
            declaration_text=current_declaration,
            implementation_text=expected_text,
            error_cls=validation_error_cls,
        )

    perform_write(resolved_container_path)
    verify_roundtrip_text(
        adapter=adapter,
        project_path=validated_request.project_path,
        container_path=resolved_container_path,
        object_name=validated_request.object_name,
        document_kind=validated_request.document_kind,
        expected_text=expected_text,
        error_cls=validation_error_cls,
    )
    return resolved_container_path, expected_text


def validate_declaration_implementation_consistency(
    declaration_text: str,
    implementation_text: str,
    error_cls: type[Exception],
) -> None:
    missing_identifiers = find_missing_declarations(
        declaration_text=declaration_text,
        implementation_text=implementation_text,
    )
    if missing_identifiers:
        raise_validation_error(
            error_cls=error_cls,
            message="Implementation references identifiers that are not declared.",
            details={"missing_identifiers": missing_identifiers},
            code="POU_SOURCE_VALIDATION_FAILED",
        )


def find_missing_declarations(
    declaration_text: str,
    implementation_text: str,
) -> list[str]:
    if not implementation_text.strip():
        return []

    declared_identifiers = collect_declared_identifiers(declaration_text)
    referenced_identifiers = collect_referenced_identifiers(implementation_text)
    missing = sorted(identifier for identifier in referenced_identifiers if identifier not in declared_identifiers)
    return missing


def collect_declared_identifiers(declaration_text: str) -> set[str]:
    identifiers: set[str] = set()
    for match in VAR_BLOCK_PATTERN.finditer(strip_st_comments(declaration_text)):
        block = match.group(1)
        for raw_line in block.splitlines():
            line = raw_line.strip()
            if not line or ":" not in line or line.startswith("{"):
                continue
            left = line.split(":", 1)[0]
            left = re.sub(r"\bAT\b.*", "", left, flags=re.IGNORECASE).strip()
            if not left:
                continue
            for item in left.split(","):
                identifier_match = IDENTIFIER_PATTERN.search(item)
                if identifier_match:
                    identifiers.add(identifier_match.group(0))
    return identifiers


def collect_referenced_identifiers(implementation_text: str) -> set[str]:
    sanitized = strip_st_comments(implementation_text)
    sanitized = re.sub(r"'(?:''|[^'])*'", " ", sanitized)

    identifiers: set[str] = set()
    for match in IDENTIFIER_PATTERN.finditer(sanitized):
        identifier = match.group(0)
        normalized = identifier.upper()
        if normalized in ST_KEYWORDS or normalized in IEC_TYPES:
            continue
        if match.start() > 0 and sanitized[match.start() - 1] == ".":
            continue
        trailing = sanitized[match.end() :].lstrip()
        if trailing.startswith("("):
            continue
        identifiers.add(identifier)
    return identifiers


def strip_st_comments(text: str) -> str:
    text = re.sub(r"\(\*.*?\*\)", " ", text, flags=re.DOTALL)
    text = re.sub(r"//.*", " ", text)
    return text


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
            can_browse = bool(child.get("can_browse", child.get("is_folder", False)))
            if can_browse:
                queue.append((child_path, depth + 1))

    return None


def _join_container_path(parent_path: str, child_name: str) -> str:
    if parent_path in ("", "/"):
        return child_name
    return "%s/%s" % (parent_path.strip("/"), child_name)


def _first_mismatch_index(expected_text: str, actual_text: str) -> int:
    shared_length = min(len(expected_text), len(actual_text))
    for index in range(shared_length):
        if expected_text[index] != actual_text[index]:
            return index
    return shared_length


def replace_line_in_text(
    *,
    current_text: str,
    line_number: int,
    new_text: str,
    error_cls: type[Exception],
) -> str:
    lines = current_text.splitlines(True)
    if line_number < 1 or line_number > len(lines):
        raise_validation_error(
            error_cls=error_cls,
            message="Field 'line_number' is outside the document line range.",
            details={
                "field": "line_number",
                "value": line_number,
                "line_count": len(lines),
            },
        )

    target_index = line_number - 1
    original_line = lines[target_index]
    line_ending = ""
    if original_line.endswith("\r\n"):
        line_ending = "\r\n"
    elif original_line.endswith("\n") or original_line.endswith("\r"):
        line_ending = original_line[-1]

    lines[target_index] = new_text + line_ending
    return "".join(lines)
