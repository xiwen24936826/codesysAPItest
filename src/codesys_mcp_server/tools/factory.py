"""Factory for assembling tool handlers from the service layer."""

from __future__ import annotations

from typing import Any

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
    open_project,
    save_project,
)
from codesys_mcp_server.tools.registry import ToolRegistry


def build_tool_registry(backend: Any) -> ToolRegistry:
    """Build the default phase-1 registry on top of one backend."""
    registry = ToolRegistry()

    registry.register(
        "create_project",
        "Create a new CODESYS project.",
        {"type": "object", "required": ["project_path", "project_mode"]},
        lambda request, request_id=None: create_project(
            request=request,
            project_creator=backend,
            request_id=request_id,
        ),
    )
    registry.register(
        "open_project",
        "Open an existing CODESYS project.",
        {"type": "object", "required": ["project_path"]},
        lambda request, request_id=None: open_project(
            request=request,
            project_opener=backend,
            request_id=request_id,
        ),
    )
    registry.register(
        "save_project",
        "Save or save-as an existing CODESYS project.",
        {"type": "object", "required": ["project_path", "save_mode"]},
        lambda request, request_id=None: save_project(
            request=request,
            project_saver=backend,
            request_id=request_id,
        ),
    )
    registry.register(
        "add_controller_device",
        "Add a top-level controller device to a project.",
        {
            "type": "object",
            "required": [
                "project_path",
                "device_name",
                "device_type",
                "device_id",
                "device_version",
            ],
        },
        lambda request, request_id=None: add_controller_device(
            request=request,
            controller_device_adder=backend,
            request_id=request_id,
        ),
    )
    registry.register(
        "create_program",
        "Create a PRG in the selected container.",
        {"type": "object", "required": ["project_path", "container_path", "name"]},
        lambda request, request_id=None: create_program(
            request=request,
            program_creator=backend,
            request_id=request_id,
        ),
    )
    registry.register(
        "create_function_block",
        "Create a function block in the selected container.",
        {"type": "object", "required": ["project_path", "container_path", "name"]},
        lambda request, request_id=None: create_function_block(
            request=request,
            function_block_creator=backend,
            request_id=request_id,
        ),
    )
    registry.register(
        "create_function",
        "Create a function in the selected container.",
        {
            "type": "object",
            "required": ["project_path", "container_path", "name", "return_type"],
        },
        lambda request, request_id=None: create_function(
            request=request,
            function_creator=backend,
            request_id=request_id,
        ),
    )
    registry.register(
        "read_textual_declaration",
        "Read the textual declaration part of an object.",
        {
            "type": "object",
            "required": ["project_path", "container_path", "object_name"],
        },
        lambda request, request_id=None: read_textual_declaration(
            request=request,
            text_document_reader=backend,
            request_id=request_id,
        ),
    )
    registry.register(
        "read_textual_implementation",
        "Read the textual implementation part of an object.",
        {
            "type": "object",
            "required": ["project_path", "container_path", "object_name"],
        },
        lambda request, request_id=None: read_textual_implementation(
            request=request,
            text_document_reader=backend,
            request_id=request_id,
        ),
    )
    registry.register(
        "replace_text_document",
        "Replace a declaration or implementation document.",
        {
            "type": "object",
            "required": [
                "project_path",
                "container_path",
                "object_name",
                "document_kind",
                "new_text",
            ],
        },
        lambda request, request_id=None: replace_text_document(
            request=request,
            text_document_replacer=backend,
            request_id=request_id,
        ),
    )
    registry.register(
        "append_text_document",
        "Append text to the end of a declaration or implementation document.",
        {
            "type": "object",
            "required": [
                "project_path",
                "container_path",
                "object_name",
                "document_kind",
                "text_to_append",
            ],
        },
        lambda request, request_id=None: append_text_document(
            request=request,
            text_document_appender=backend,
            request_id=request_id,
        ),
    )
    registry.register(
        "insert_text_document",
        "Insert text into a declaration or implementation document at a fixed offset.",
        {
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
        lambda request, request_id=None: insert_text_document(
            request=request,
            text_document_inserter=backend,
            request_id=request_id,
        ),
    )
    return registry
