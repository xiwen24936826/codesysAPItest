"""Local server application assembly for tool dispatch."""

from __future__ import annotations

from typing import Any

from codesys_mcp_server.models.tooling import ToolCall, ToolDefinition, ToolResult
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

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        request_id: str | None = None,
    ) -> ToolResult:
        registered = self._registry.get(name)
        payload = registered.handler(arguments, request_id)
        return ToolResult(payload=payload)

    def handle_call(self, call: ToolCall) -> ToolResult:
        return self.call_tool(call.name, call.arguments, call.request_id)
