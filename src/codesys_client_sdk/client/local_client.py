"""In-process client wrapper for the local server application."""

from __future__ import annotations

from typing import Any

from codesys_client_sdk.exceptions import ToolExecutionError, ToolNotFoundError
from codesys_client_sdk.models import ToolCall, ToolDefinition, ToolResult
from codesys_mcp_server.server import ServerApplication


class LocalCodesysMcpClient:
    """Local in-process client for the assembled server application."""

    def __init__(self, server: ServerApplication) -> None:
        self._server = server

    def list_tools(self) -> list[ToolDefinition]:
        return self._server.list_tools()

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        request_id: str | None = None,
    ) -> ToolResult:
        try:
            result = self._server.handle_call(
                ToolCall(name=name, arguments=arguments, request_id=request_id)
            )
        except KeyError as exc:
            raise ToolNotFoundError(str(exc)) from exc

        if not result.ok:
            error = result.error or {}
            raise ToolExecutionError(
                error.get("message", "Tool execution failed."),
                error=error,
            )
        return result

    def create_program(
        self,
        project_path: str,
        container_path: str,
        name: str,
        language: str = "ST",
        request_id: str | None = None,
    ) -> ToolResult:
        return self.call_tool(
            "create_program",
            {
                "project_path": project_path,
                "container_path": container_path,
                "name": name,
                "language": language,
            },
            request_id=request_id,
        )

    def create_project(
        self,
        project_path: str,
        project_mode: str = "empty",
        set_as_primary: bool = True,
        request_id: str | None = None,
    ) -> ToolResult:
        return self.call_tool(
            "create_project",
            {
                "project_path": project_path,
                "project_mode": project_mode,
                "set_as_primary": set_as_primary,
            },
            request_id=request_id,
        )

    def open_project(
        self,
        project_path: str,
        request_id: str | None = None,
    ) -> ToolResult:
        return self.call_tool(
            "open_project",
            {"project_path": project_path},
            request_id=request_id,
        )

    def save_project(
        self,
        project_path: str,
        save_mode: str = "save",
        target_project_path: str | None = None,
        request_id: str | None = None,
    ) -> ToolResult:
        arguments = {"project_path": project_path, "save_mode": save_mode}
        if target_project_path is not None:
            arguments["target_project_path"] = target_project_path
        return self.call_tool("save_project", arguments, request_id=request_id)

    def add_controller_device(
        self,
        project_path: str,
        device_name: str,
        device_type: int | str,
        device_id: str,
        device_version: str,
        module: str | None = None,
        request_id: str | None = None,
    ) -> ToolResult:
        return self.call_tool(
            "add_controller_device",
            {
                "project_path": project_path,
                "device_name": device_name,
                "device_type": device_type,
                "device_id": device_id,
                "device_version": device_version,
                "module": module,
            },
            request_id=request_id,
        )

    def create_function_block(
        self,
        project_path: str,
        container_path: str,
        name: str,
        language: str = "ST",
        base_type: str | None = None,
        interfaces: list[str] | None = None,
        request_id: str | None = None,
    ) -> ToolResult:
        return self.call_tool(
            "create_function_block",
            {
                "project_path": project_path,
                "container_path": container_path,
                "name": name,
                "language": language,
                "base_type": base_type,
                "interfaces": interfaces or [],
            },
            request_id=request_id,
        )

    def create_function(
        self,
        project_path: str,
        container_path: str,
        name: str,
        return_type: str,
        language: str = "ST",
        request_id: str | None = None,
    ) -> ToolResult:
        return self.call_tool(
            "create_function",
            {
                "project_path": project_path,
                "container_path": container_path,
                "name": name,
                "return_type": return_type,
                "language": language,
            },
            request_id=request_id,
        )

    def read_textual_declaration(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        request_id: str | None = None,
    ) -> ToolResult:
        return self.call_tool(
            "read_textual_declaration",
            {
                "project_path": project_path,
                "container_path": container_path,
                "object_name": object_name,
            },
            request_id=request_id,
        )

    def read_textual_implementation(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        request_id: str | None = None,
    ) -> ToolResult:
        return self.call_tool(
            "read_textual_implementation",
            {
                "project_path": project_path,
                "container_path": container_path,
                "object_name": object_name,
            },
            request_id=request_id,
        )

    def replace_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        new_text: str,
        request_id: str | None = None,
    ) -> ToolResult:
        return self.call_tool(
            "replace_text_document",
            {
                "project_path": project_path,
                "container_path": container_path,
                "object_name": object_name,
                "document_kind": document_kind,
                "new_text": new_text,
            },
            request_id=request_id,
        )

    def append_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        text_to_append: str,
        request_id: str | None = None,
    ) -> ToolResult:
        return self.call_tool(
            "append_text_document",
            {
                "project_path": project_path,
                "container_path": container_path,
                "object_name": object_name,
                "document_kind": document_kind,
                "text_to_append": text_to_append,
            },
            request_id=request_id,
        )

    def insert_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        text_to_insert: str,
        insertion_offset: int,
        request_id: str | None = None,
    ) -> ToolResult:
        return self.call_tool(
            "insert_text_document",
            {
                "project_path": project_path,
                "container_path": container_path,
                "object_name": object_name,
                "document_kind": document_kind,
                "text_to_insert": text_to_insert,
                "insertion_offset": insertion_offset,
            },
            request_id=request_id,
        )
