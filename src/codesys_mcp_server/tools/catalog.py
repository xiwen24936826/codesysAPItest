"""Canonical tool catalog for MCP metadata, routing guidance, and schema policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolCatalogEntry:
    """One canonical catalog entry for one exposed MCP tool."""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler_key: str
    domain: str
    workflow_ids: tuple[str, ...]
    risk_level: str = "safe"
    preferred_predecessors: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def to_public_dict(self) -> dict[str, Any]:
        """Return a machine-readable public view of the catalog entry."""
        payload = asdict(self)
        payload["code"] = tool_code_for(self.name)
        payload["category"] = tool_category_for(self.name)
        return payload


@dataclass(frozen=True)
class ToolArgumentSchemaError(Exception):
    """Raised when tool arguments violate the catalog schema contract."""

    message: str
    details: dict[str, Any]
    code: str = "TOOL_ARGUMENT_SCHEMA_VIOLATION"

    def __str__(self) -> str:
        return self.message


def _object_schema(
    *,
    required: list[str],
    properties: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "type": "object",
        "required": required,
        "properties": properties,
        "additionalProperties": False,
    }


TOOL_CODE_BY_NAME: dict[str, str] = {
    "create_project": "PRJ-001",
    "open_project": "PRJ-002",
    "list_project_objects": "PRJ-003",
    "find_project_objects": "PRJ-004",
    "save_project": "PRJ-005",
    "add_controller_device": "PRJ-006",
    "create_program": "POU-001",
    "create_function_block": "POU-002",
    "create_function": "POU-003",
    "read_textual_declaration": "POU-004",
    "read_textual_implementation": "POU-005",
    "replace_text_document": "POU-006",
    "append_text_document": "POU-007",
    "insert_text_document": "POU-008",
    "replace_line": "POU-009",
    "generate_pou_transaction": "POU-010",
    "edit_pou_transaction": "POU-011",
    "scan_network_devices": "DEV-001",
}


TOOL_CATEGORY_BY_NAME: dict[str, str] = {
    "create_project": "projects",
    "open_project": "projects",
    "list_project_objects": "projects",
    "find_project_objects": "projects",
    "save_project": "projects",
    "add_controller_device": "projects",
    "create_program": "pous",
    "create_function_block": "pous",
    "create_function": "pous",
    "read_textual_declaration": "pous",
    "read_textual_implementation": "pous",
    "replace_text_document": "pous",
    "append_text_document": "pous",
    "insert_text_document": "pous",
    "replace_line": "pous",
    "generate_pou_transaction": "pous",
    "edit_pou_transaction": "pous",
    "scan_network_devices": "devices",
}


TOOL_CATALOG: tuple[ToolCatalogEntry, ...] = (
    ToolCatalogEntry(
        name="create_project",
        description="Create a new CODESYS project.",
        input_schema=_object_schema(
            required=["project_path", "project_mode"],
            properties={
                "project_path": {"type": "string"},
                "project_mode": {"type": "string", "enum": ["empty", "template"]},
                "set_as_primary": {"type": "boolean"},
                "template_project_path": {"type": "string"},
            },
        ),
        handler_key="create_project",
        domain="projects",
        workflow_ids=("new_project_flow",),
        risk_level="dangerous",
        notes=(
            "Only for explicit new-project creation requests.",
            "Must not be used as a fallback during existing-project editing.",
        ),
    ),
    ToolCatalogEntry(
        name="open_project",
        description="Open an existing CODESYS project.",
        input_schema=_object_schema(
            required=["project_path"],
            properties={"project_path": {"type": "string"}},
        ),
        handler_key="open_project",
        domain="projects",
        workflow_ids=("existing_project_edit_flow", "new_project_flow", "online_operations_flow"),
        risk_level="safe",
    ),
    ToolCatalogEntry(
        name="list_project_objects",
        description="List child objects below a logical container in the project tree.",
        input_schema=_object_schema(
            required=["project_path"],
            properties={
                "project_path": {"type": "string"},
                "container_path": {"type": "string"},
            },
        ),
        handler_key="list_project_objects",
        domain="projects",
        workflow_ids=("existing_project_edit_flow", "new_project_flow"),
        risk_level="safe",
        preferred_predecessors=("open_project",),
        notes=("Prefer can_browse over is_folder when recursing the returned tree.",),
    ),
    ToolCatalogEntry(
        name="find_project_objects",
        description="Find matching objects by name below a logical container in the project tree.",
        input_schema=_object_schema(
            required=["project_path", "object_name"],
            properties={
                "project_path": {"type": "string"},
                "object_name": {"type": "string"},
                "container_path": {"type": "string"},
                "recursive": {"type": "boolean"},
            },
        ),
        handler_key="find_project_objects",
        domain="projects",
        workflow_ids=("existing_project_edit_flow", "new_project_flow"),
        risk_level="safe",
        preferred_predecessors=("open_project",),
    ),
    ToolCatalogEntry(
        name="scan_network_devices",
        description="Scan online targets through a configured CODESYS gateway.",
        input_schema=_object_schema(
            required=[],
            properties={
                "gateway_name": {"type": "string"},
                "use_cached_result": {"type": "boolean"},
            },
        ),
        handler_key="scan_network_devices",
        domain="online",
        workflow_ids=("network_scan_flow",),
        risk_level="safe",
    ),
    ToolCatalogEntry(
        name="save_project",
        description="Save or save-as an existing CODESYS project.",
        input_schema=_object_schema(
            required=["project_path", "save_mode"],
            properties={
                "project_path": {"type": "string"},
                "save_mode": {"type": "string", "enum": ["save", "save_as"]},
                "target_project_path": {"type": "string"},
            },
        ),
        handler_key="save_project",
        domain="projects",
        workflow_ids=("existing_project_edit_flow", "new_project_flow"),
        risk_level="caution",
    ),
    ToolCatalogEntry(
        name="add_controller_device",
        description="Add a top-level controller device to a project.",
        input_schema=_object_schema(
            required=[
                "project_path",
                "device_name",
                "device_type",
                "device_id",
                "device_version",
            ],
            properties={
                "project_path": {"type": "string"},
                "device_name": {"type": "string"},
                "device_type": {"type": ["string", "integer"]},
                "device_id": {"type": "string"},
                "device_version": {"type": "string"},
                "module": {"type": "string"},
            },
        ),
        handler_key="add_controller_device",
        domain="projects",
        workflow_ids=("new_project_flow",),
        risk_level="dangerous",
        preferred_predecessors=("create_project", "open_project"),
        notes=("Not part of the preferred existing-project POU editing flow.",),
    ),
    ToolCatalogEntry(
        name="create_program",
        description="Create a PRG in the selected container.",
        input_schema=_object_schema(
            required=["project_path", "container_path", "name"],
            properties={
                "project_path": {"type": "string"},
                "container_path": {"type": "string"},
                "name": {"type": "string"},
                "language": {"type": "string"},
            },
        ),
        handler_key="create_program",
        domain="pous",
        workflow_ids=("existing_project_edit_flow", "new_project_flow"),
        risk_level="caution",
        preferred_predecessors=("open_project", "list_project_objects"),
    ),
    ToolCatalogEntry(
        name="create_function_block",
        description="Create a function block in the selected container.",
        input_schema=_object_schema(
            required=["project_path", "container_path", "name"],
            properties={
                "project_path": {"type": "string"},
                "container_path": {"type": "string"},
                "name": {"type": "string"},
                "language": {"type": "string"},
                "base_type": {"type": "string"},
                "interfaces": {"type": "array", "items": {"type": "string"}},
            },
        ),
        handler_key="create_function_block",
        domain="pous",
        workflow_ids=("existing_project_edit_flow", "new_project_flow"),
        risk_level="caution",
        preferred_predecessors=("open_project", "list_project_objects"),
    ),
    ToolCatalogEntry(
        name="create_function",
        description="Create a function in the selected container.",
        input_schema=_object_schema(
            required=["project_path", "container_path", "name", "return_type"],
            properties={
                "project_path": {"type": "string"},
                "container_path": {"type": "string"},
                "name": {"type": "string"},
                "return_type": {"type": "string"},
                "language": {"type": "string"},
            },
        ),
        handler_key="create_function",
        domain="pous",
        workflow_ids=("existing_project_edit_flow", "new_project_flow"),
        risk_level="caution",
        preferred_predecessors=("open_project", "list_project_objects"),
    ),
    ToolCatalogEntry(
        name="read_textual_declaration",
        description="Read the textual declaration part of an object.",
        input_schema=_object_schema(
            required=["project_path", "container_path", "object_name"],
            properties={
                "project_path": {"type": "string"},
                "container_path": {"type": "string"},
                "object_name": {"type": "string"},
            },
        ),
        handler_key="read_textual_declaration",
        domain="pous",
        workflow_ids=("existing_project_edit_flow",),
        risk_level="safe",
        preferred_predecessors=("open_project",),
    ),
    ToolCatalogEntry(
        name="read_textual_implementation",
        description="Read the textual implementation part of an object.",
        input_schema=_object_schema(
            required=["project_path", "container_path", "object_name"],
            properties={
                "project_path": {"type": "string"},
                "container_path": {"type": "string"},
                "object_name": {"type": "string"},
            },
        ),
        handler_key="read_textual_implementation",
        domain="pous",
        workflow_ids=("existing_project_edit_flow",),
        risk_level="safe",
        preferred_predecessors=("open_project",),
    ),
    ToolCatalogEntry(
        name="replace_text_document",
        description="Replace a declaration or implementation document.",
        input_schema=_object_schema(
            required=[
                "project_path",
                "container_path",
                "object_name",
                "document_kind",
                "new_text",
            ],
            properties={
                "project_path": {"type": "string"},
                "container_path": {"type": "string"},
                "object_name": {"type": "string"},
                "document_kind": {"type": "string", "enum": ["declaration", "implementation"]},
                "new_text": {"type": "string"},
            },
        ),
        handler_key="replace_text_document",
        domain="pous",
        workflow_ids=("existing_project_edit_flow",),
        risk_level="caution",
        preferred_predecessors=("open_project",),
    ),
    ToolCatalogEntry(
        name="append_text_document",
        description="Append text to the end of a declaration or implementation document.",
        input_schema=_object_schema(
            required=[
                "project_path",
                "container_path",
                "object_name",
                "document_kind",
                "text_to_append",
            ],
            properties={
                "project_path": {"type": "string"},
                "container_path": {"type": "string"},
                "object_name": {"type": "string"},
                "document_kind": {"type": "string", "enum": ["declaration", "implementation"]},
                "text_to_append": {"type": "string"},
            },
        ),
        handler_key="append_text_document",
        domain="pous",
        workflow_ids=("existing_project_edit_flow",),
        risk_level="caution",
        preferred_predecessors=("open_project",),
    ),
    ToolCatalogEntry(
        name="insert_text_document",
        description="Insert text into a declaration or implementation document at a fixed offset.",
        input_schema=_object_schema(
            required=[
                "project_path",
                "container_path",
                "object_name",
                "document_kind",
                "text_to_insert",
                "insertion_offset",
            ],
            properties={
                "project_path": {"type": "string"},
                "container_path": {"type": "string"},
                "object_name": {"type": "string"},
                "document_kind": {"type": "string", "enum": ["declaration", "implementation"]},
                "text_to_insert": {"type": "string"},
                "insertion_offset": {"type": "integer"},
            },
        ),
        handler_key="insert_text_document",
        domain="pous",
        workflow_ids=("existing_project_edit_flow",),
        risk_level="caution",
        preferred_predecessors=("open_project",),
    ),
    ToolCatalogEntry(
        name="replace_line",
        description="Replace one line in a declaration or implementation document.",
        input_schema=_object_schema(
            required=[
                "project_path",
                "container_path",
                "object_name",
                "document_kind",
                "line_number",
                "new_text",
            ],
            properties={
                "project_path": {"type": "string"},
                "container_path": {"type": "string"},
                "object_name": {"type": "string"},
                "document_kind": {"type": "string", "enum": ["declaration", "implementation"]},
                "line_number": {"type": "integer"},
                "new_text": {"type": "string"},
            },
        ),
        handler_key="replace_line",
        domain="pous",
        workflow_ids=("existing_project_edit_flow",),
        risk_level="caution",
        preferred_predecessors=("open_project",),
    ),
    ToolCatalogEntry(
        name="generate_pou_transaction",
        description="Open a project, create a POU, write declaration/implementation, save, and close in a single IDE run.",
        input_schema=_object_schema(
            required=[
                "project_path",
                "container_path",
                "pou_name",
                "pou_kind",
                "declaration_text",
                "implementation_text",
            ],
            properties={
                "project_path": {"type": "string"},
                "container_path": {"type": "string"},
                "pou_name": {"type": "string"},
                "pou_kind": {
                    "type": "string",
                    "enum": ["program", "function_block", "function"],
                },
                "language": {"type": "string"},
                "return_type": {"type": "string"},
                "base_type": {"type": "string"},
                "interfaces": {"type": "array", "items": {"type": "string"}},
                "declaration_text": {"type": "string"},
                "implementation_text": {"type": "string"},
                "write_strategy": {
                    "type": "string",
                    "enum": ["replace"],
                },
                "verify_mode": {
                    "type": "string",
                    "enum": ["exact", "normalize_newlines"],
                },
            },
        ),
        handler_key="generate_pou_transaction",
        domain="pous",
        workflow_ids=("existing_project_edit_flow", "new_project_flow"),
        risk_level="dangerous",
        preferred_predecessors=("open_project",),
        notes=(
            "This tool always saves and closes the project when it succeeds.",
            "Prefer this tool over many small edits when IDE startup time dominates.",
        ),
    ),
    ToolCatalogEntry(
        name="edit_pou_transaction",
        description="Open a project, edit one POU by applying a patch plan, verify, save, and close in a single IDE run.",
        input_schema=_object_schema(
            required=["project_path", "container_path", "pou_name", "operations"],
            properties={
                "project_path": {"type": "string"},
                "container_path": {"type": "string"},
                "pou_name": {"type": "string"},
                "operations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "document_kind": {
                                "type": "string",
                                "enum": ["declaration", "implementation"],
                            },
                            "op": {
                                "type": "string",
                                "enum": ["replace", "append", "insert", "replace_line"],
                            },
                            "new_text": {"type": "string"},
                            "text": {"type": "string"},
                            "offset": {"type": "integer"},
                            "line_number": {"type": "integer"},
                        },
                    },
                },
                "verify_mode": {
                    "type": "string",
                    "enum": ["exact", "normalize_newlines"],
                },
            },
        ),
        handler_key="edit_pou_transaction",
        domain="pous",
        workflow_ids=("existing_project_edit_flow",),
        risk_level="dangerous",
        preferred_predecessors=("open_project",),
        notes=(
            "Applies operations in order.",
            "Verification includes a round-trip readback of any edited documents.",
        ),
    ),
)


TOOL_CATALOG_BY_NAME = {entry.name: entry for entry in TOOL_CATALOG}


def get_tool_catalog() -> tuple[ToolCatalogEntry, ...]:
    """Return the canonical immutable tool catalog."""
    return TOOL_CATALOG


def tool_code_for(tool_name: str) -> str:
    """Return the stable display code for one tool."""
    return TOOL_CODE_BY_NAME.get(tool_name, "UNMAPPED")


def tool_category_for(tool_name: str) -> str:
    """Return the stable business category for one tool."""
    return TOOL_CATEGORY_BY_NAME.get(tool_name, "uncategorized")


def export_tool_catalog() -> list[dict[str, Any]]:
    """Export the canonical machine-readable catalog view."""
    return [entry.to_public_dict() for entry in TOOL_CATALOG]


def validate_tool_arguments(entry: ToolCatalogEntry, arguments: Any) -> None:
    """Validate one tool call against the catalog schema."""
    schema = entry.input_schema
    if schema.get("type") != "object":
        return

    if not isinstance(arguments, dict):
        raise ToolArgumentSchemaError(
            message="Tool arguments must be a JSON object.",
            details={"tool": entry.name, "value": arguments},
        )

    properties = schema.get("properties", {})
    required = schema.get("required", [])

    missing = [field for field in required if field not in arguments]
    if missing:
        raise ToolArgumentSchemaError(
            message="Missing required tool arguments.",
            details={"tool": entry.name, "missing_fields": missing},
        )

    if schema.get("additionalProperties") is False:
        unexpected = sorted(set(arguments.keys()) - set(properties.keys()))
        if unexpected:
            raise ToolArgumentSchemaError(
                message="Unexpected tool arguments are not allowed for this tool.",
                details={"tool": entry.name, "unexpected_fields": unexpected},
            )

    for field_name, value in arguments.items():
        field_schema = properties.get(field_name)
        if field_schema is None:
            continue
        _validate_field_schema(entry=entry, field_name=field_name, value=value, field_schema=field_schema)


def _validate_field_schema(
    *,
    entry: ToolCatalogEntry,
    field_name: str,
    value: Any,
    field_schema: dict[str, Any],
) -> None:
    expected_type = field_schema.get("type")
    if expected_type is not None and not _matches_type(value, expected_type, field_schema):
        raise ToolArgumentSchemaError(
            message="Tool argument has an invalid type.",
            details={
                "tool": entry.name,
                "field": field_name,
                "expected_type": expected_type,
                "value": value,
            },
        )

    if "enum" in field_schema and value not in field_schema["enum"]:
        raise ToolArgumentSchemaError(
            message="Tool argument value is not allowed by the catalog schema.",
            details={
                "tool": entry.name,
                "field": field_name,
                "allowed_values": field_schema["enum"],
                "value": value,
            },
        )

    if field_schema.get("type") == "array" and isinstance(value, list):
        item_schema = field_schema.get("items")
        if isinstance(item_schema, dict):
            for item in value:
                if not _matches_type(item, item_schema.get("type"), item_schema):
                    raise ToolArgumentSchemaError(
                        message="Tool argument array contains an invalid item type.",
                        details={
                            "tool": entry.name,
                            "field": field_name,
                            "expected_type": item_schema.get("type"),
                            "value": item,
                        },
                    )


def _matches_type(value: Any, expected_type: Any, field_schema: dict[str, Any]) -> bool:
    if isinstance(expected_type, list):
        return any(_matches_type(value, item_type, field_schema) for item_type in expected_type)

    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    return True
