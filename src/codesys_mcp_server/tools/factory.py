"""Factory for assembling tool handlers from the service layer."""

from __future__ import annotations

from typing import Any, Callable

from codesys_mcp_server.services.pous import (
    append_text_document,
    create_function,
    create_function_block,
    create_program,
    edit_pou_transaction,
    generate_pou_transaction,
    insert_text_document,
    read_textual_declaration,
    read_textual_implementation,
    replace_line,
    replace_text_document,
)
from codesys_mcp_server.services.online import scan_network_devices
from codesys_mcp_server.services.projects import (
    add_controller_device,
    create_project,
    find_project_objects,
    list_project_objects,
    open_project,
    save_project,
)
from codesys_mcp_server.tools.catalog import TOOL_CATALOG, ToolCatalogEntry
from codesys_mcp_server.tools.registry import ToolHandler, ToolRegistry


HandlerBuilder = Callable[[Any], ToolHandler]


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


def _bind_scan_network_devices(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: scan_network_devices(
        request=request,
        network_device_scanner=backend,
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


def _bind_replace_line(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: replace_line(
        request=request,
        text_document_line_replacer=backend,
        request_id=request_id,
    )


def _bind_generate_pou_transaction(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: generate_pou_transaction(
        request=request,
        pou_transaction_generator=backend,
        request_id=request_id,
    )


def _bind_edit_pou_transaction(backend: Any) -> ToolHandler:
    return lambda request, request_id=None: edit_pou_transaction(
        request=request,
        pou_transaction_editor=backend,
        request_id=request_id,
    )


HANDLER_BUILDERS: dict[str, HandlerBuilder] = {
    "create_project": _bind_create_project,
    "open_project": _bind_open_project,
    "list_project_objects": _bind_list_project_objects,
    "find_project_objects": _bind_find_project_objects,
    "scan_network_devices": _bind_scan_network_devices,
    "save_project": _bind_save_project,
    "add_controller_device": _bind_add_controller_device,
    "create_program": _bind_create_program,
    "create_function_block": _bind_create_function_block,
    "create_function": _bind_create_function,
    "read_textual_declaration": _bind_read_textual_declaration,
    "read_textual_implementation": _bind_read_textual_implementation,
    "replace_text_document": _bind_replace_text_document,
    "append_text_document": _bind_append_text_document,
    "insert_text_document": _bind_insert_text_document,
    "replace_line": _bind_replace_line,
    "generate_pou_transaction": _bind_generate_pou_transaction,
    "edit_pou_transaction": _bind_edit_pou_transaction,
}


def build_tool_registry(backend: Any) -> ToolRegistry:
    """Build the default phase-1 registry on top of one backend."""
    registry = ToolRegistry()
    for entry in TOOL_CATALOG:
        registry.register(
            catalog_entry=entry,
            handler=_resolve_handler_builder(entry)(backend),
        )
    return registry


def _resolve_handler_builder(entry: ToolCatalogEntry) -> HandlerBuilder:
    try:
        return HANDLER_BUILDERS[entry.handler_key]
    except KeyError as exc:
        raise KeyError("Missing handler builder for tool catalog entry '%s'." % entry.name) from exc
