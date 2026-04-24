"""Tool registry for the local server assembly."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from codesys_mcp_server.models.tooling import ToolDefinition
from codesys_mcp_server.tools.catalog import ToolCatalogEntry


ToolHandler = Callable[[dict[str, Any], str | None], dict[str, Any]]


@dataclass(frozen=True)
class RegisteredTool:
    """One registered tool and its handler."""

    catalog_entry: ToolCatalogEntry
    definition: ToolDefinition
    handler: ToolHandler


class ToolRegistry:
    """Simple in-process registry for exposed tools."""

    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(
        self,
        catalog_entry: ToolCatalogEntry,
        handler: ToolHandler,
    ) -> None:
        if catalog_entry.name in self._tools:
            raise ValueError("Tool '%s' is already registered." % catalog_entry.name)
        self._tools[catalog_entry.name] = RegisteredTool(
            catalog_entry=catalog_entry,
            definition=ToolDefinition(
                name=catalog_entry.name,
                description=catalog_entry.description,
                input_schema=catalog_entry.input_schema,
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
