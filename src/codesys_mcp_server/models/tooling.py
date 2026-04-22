"""Shared tool-facing models for server and client code."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolDefinition:
    """Static metadata describing one exposed tool."""

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolCall:
    """A tool invocation request."""

    name: str
    arguments: dict[str, Any]
    request_id: str | None = None


@dataclass(frozen=True)
class ToolResult:
    """A structured tool invocation result."""

    payload: dict[str, Any]

    @property
    def ok(self) -> bool:
        return bool(self.payload.get("ok"))

    @property
    def error(self) -> dict[str, Any] | None:
        value = self.payload.get("error")
        return value if isinstance(value, dict) else None
