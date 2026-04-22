"""Tool registry for the local server assembly."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from codesys_mcp_server.models.tooling import ToolDefinition


ToolHandler = Callable[[dict[str, Any], str | None], dict[str, Any]]


@dataclass(frozen=True)
class RegisteredTool:
    """One registered tool and its handler."""

    definition: ToolDefinition
    handler: ToolHandler


class ToolRegistry:
    """Simple in-process registry for exposed tools."""

    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        handler: ToolHandler,
    ) -> None:
        if name in self._tools:
            raise ValueError("Tool '%s' is already registered." % name)
        self._tools[name] = RegisteredTool(
            definition=ToolDefinition(
                name=name,
                description=description,
                input_schema=input_schema,
            ),
            handler=handler,
        )

    def get(self, name: str) -> RegisteredTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError("Tool '%s' is not registered." % name) from exc

    def list_definitions(self) -> list[ToolDefinition]:
        return [registered.definition for registered in self._tools.values()]
