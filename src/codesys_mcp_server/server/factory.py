"""Factory helpers for server-side assembly."""

from __future__ import annotations

from typing import Any

from .application import ServerApplication
from .in_memory_backend import InMemoryCodesysBackend


def create_server_application(backend: Any) -> ServerApplication:
    """Create the default local server application."""
    return ServerApplication.from_backend(backend)


def create_in_memory_server_application() -> ServerApplication:
    """Create a server application backed by the in-memory demo backend."""
    return create_server_application(InMemoryCodesysBackend())
