"""Factory for assembling tool handlers from the service layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from codesys_mcp_server.services.pous import (
    append_text_document,
    create_function,
    create_function_block,
    create_program,
    insert_text_document,
    read_textual_declaration,
    read_textual_implementation,
    replace_text_document,
)
from codesys_mcp_server.services.projects import (
    add_controller_device,
    create_project,
    find_project_objects,
    list_project_objects,
    open_project,
    save_project,
)
from codesys_mcp_server.tools.registry import ToolHandler, ToolRegistry


HandlerBuilder = Callable[[Any], ToolHandler]


@dataclass(frozen=True)
class ToolSpec:
    """Declarative specification for one registered tool."""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler_builder: HandlerBuilder


def _bind_create_project(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: create_project(
        request=request,
        project_creator=backend,
        request_id=request_id,
    )


def _bind_open_project(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: open_project(
        request=request,
        project_opener=backend,
        request_id=request_id,
    )


def _bind_list_project_objects(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: list_project_objects(
        request=request,
        project_object_lister=backend,
        request_id=request_id,
    )


def _bind_find_project_objects(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: find_project_objects(
        request=request,
        project_object_finder=backend,
        request_id=request_id,
    )


def _bind_save_project(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: save_project(
        request=request,
        project_saver=backend,
        request_id=request_id,
    )


def _bind_add_controller_device(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: add_controller_device(
        request=request,
        controller_device_adder=backend,
        request_id=request_id,
    )


def _bind_create_program(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: create_program(
        request=request,
        program_creator=backend,
        request_id=request_id,
    )


def _bind_create_function_block(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: create_function_block(
        request=request,
        function_block_creator=backend,
        request_id=request_id,
    )


def _bind_create_function(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: create_function(
        request=request,
        function_creator=backend,
        request_id=request_id,
    )


def _bind_read_textual_declaration(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: read_textual_declaration(
        request=request,
        text_document_reader=backend,
        request_id=request_id,
    )


def _bind_read_textual_implementation(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: read_textual_implementation(
        request=request,
        text_document_reader=backend,
        request_id=request_id,
    )


def _bind_replace_text_document(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: replace_text_document(
        request=request,
        text_document_replacer=backend,
        request_id=request_id,
    )


def _bind_append_text_document(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: append_text_document(
        request=request,
        text_document_appender=backend,
        request_id=request_id,
    )


def _bind_insert_text_document(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: insert_text_document(
        request=request,
        text_document_inserter=backend,
        request_id=request_id,
    )


TOOL_SPECS = [
    ToolSpec(
        name="create_project",
        description="Create a new CODESYS project.",
        input_schema={"type": "object", "required": ["project_path", "project_mode"]},
        handler_builder=_bind_create_project,
    ),
    ToolSpec(
        name="open_project",
        description="Open an existing CODESYS project.",
        input_schema={"type": "object", "required": ["project_path"]},
        handler_builder=_bind_open_project,
    ),
    ToolSpec(
        name="list_project_objects",
        description="List child objects below a logical container in the project tree.",
        input_schema={"type": "object", "required": ["project_path"]},
        handler_builder=_bind_list_project_objects,
    ),
    ToolSpec(
        name="find_project_objects",
        description="Find matching objects by name below a logical container in the project tree.",
        input_schema={"type": "object", "required": ["project_path", "object_name"]},
        handler_builder=_bind_find_project_objects,
    ),
    ToolSpec(
        name="save_project",
        description="Save or save-as an existing CODESYS project.",
        input_schema={"type": "object", "required": ["project_path", "save_mode"]},
        handler_builder=_bind_save_project,
    ),
    ToolSpec(
        name="add_controller_device",
        description="Add a top-level controller device to a project.",
        input_schema={
            "type": "object",
            "required": [
                "project_path",
                "device_name",
                "device_type",
                "device_id",
                "device_version",
            ],
        },
        handler_builder=_bind_add_controller_device,
    ),
    ToolSpec(
        name="create_program",
        description="Create a PRG in the selected container.",
        input_schema={"type": "object", "required": ["project_path", "container_path", "name"]},
        handler_builder=_bind_create_program,
    ),
    ToolSpec(
        name="create_function_block",
        description="Create a function block in the selected container.",
        input_schema={"type": "object", "required": ["project_path", "container_path", "name"]},
        handler_builder=_bind_create_function_block,
    ),
    ToolSpec(
        name="create_function",
        description="Create a function in the selected container.",
        input_schema={
            "type": "object",
            "required": ["project_path", "container_path", "name", "return_type"],
        },
        handler_builder=_bind_create_function,
    ),
    ToolSpec(
        name="read_textual_declaration",
        description="Read the textual declaration part of an object.",
        input_schema={
            "type": "object",
            "required": ["project_path", "container_path", "object_name"],
        },
        handler_builder=_bind_read_textual_declaration,
    ),
    ToolSpec(
        name="read_textual_implementation",
        description="Read the textual implementation part of an object.",
        input_schema={
            "type": "object",
            "required": ["project_path", "container_path", "object_name"],
        },
        handler_builder=_bind_read_textual_implementation,
    ),
    ToolSpec(
        name="replace_text_document",
        description="Replace a declaration or implementation document.",
        input_schema={
            "type": "object",
            "required": [
                "project_path",
                "container_path",
                "object_name",
                "document_kind",
                "new_text",
            ],
        },
        handler_builder=_bind_replace_text_document,
    ),
    ToolSpec(
        name="append_text_document",
        description="Append text to the end of a declaration or implementation document.",
        input_schema={
            "type": "object",
            "required": [
                "project_path",
                "container_path",
                "object_name",
                "document_kind",
                "text_to_append",
            ],
        },
        handler_builder=_bind_append_text_document,
    ),
    ToolSpec(
        name="insert_text_document",
        description="Insert text into a declaration or implementation document at a fixed offset.",
        input_schema={
            "type": "object",
            "required": [
                "project_path",
                "container_path",
                "object_name",
                "document_kind",
                "text_to_insert",
                "insertion_offset",
            ],
        },
        handler_builder=_bind_insert_text_document,
    ),
]


def build_tool_registry(backend: Any) -> ToolRegistry:
    """Build the default phase-1 registry on top of one backend."""
    registry = ToolRegistry()
    for spec in TOOL_SPECS:
        registry.register(
            spec.name,
            spec.description,
            spec.input_schema,
            spec.handler_builder(backend),
        )
    return registry
