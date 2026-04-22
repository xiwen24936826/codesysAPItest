"""Client SDK exception types."""

from __future__ import annotations


class CodesysClientError(Exception):
    """Base client-side exception."""


class ToolNotFoundError(CodesysClientError):
    """Raised when a requested tool is not registered."""


class ToolExecutionError(CodesysClientError):
    """Raised when a tool returns an error payload."""

    def __init__(self, message: str, error: dict | None = None) -> None:
        super().__init__(message)
        self.error = error or {}
