"""Local server application assembly for tool dispatch."""

from __future__ import annotations

from typing import Any

from codesys_mcp_server.models.tooling import ToolCall, ToolDefinition, ToolResult
from codesys_mcp_server.services._service_common import begin_service_call, error_response
from codesys_mcp_server.tools.catalog import ToolArgumentSchemaError, export_tool_catalog, validate_tool_arguments
from codesys_mcp_server.tools.factory import build_tool_registry
from codesys_mcp_server.tools.registry import ToolRegistry


class ServerApplication:
    """In-process MCP-style application facade."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    @classmethod
    def from_backend(cls, backend: Any) -> "ServerApplication":
        return cls(registry=build_tool_registry(backend))

    def list_tools(self) -> list[ToolDefinition]:
        return self._registry.list_definitions()

    def export_tool_catalog(self) -> list[dict[str, Any]]:
        """Export the canonical machine-readable tool catalog."""
        return export_tool_catalog()

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        request_id: str | None = None,
    ) -> ToolResult:
        registered = self._registry.get(name)
        service_call = begin_service_call(request_id)
        try:
            validate_tool_arguments(registered.catalog_entry, arguments)
        except ToolArgumentSchemaError as exc:
            return ToolResult(
                payload=error_response(
                    tool_name=name,
                    code=exc.code,
                    message=exc.message,
                    details=exc.details,
                    request_id=service_call.request_id,
                    started_at=service_call.started_at,
                )
            )
        payload = registered.handler(arguments, request_id)
        return ToolResult(payload=payload)

    def handle_call(self, call: ToolCall) -> ToolResult:
        return self.call_tool(call.name, call.arguments, call.request_id)
