"""Factory helpers for server-side assembly."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codesys_mcp_server.core import CodesysProjectAdapter

from .application import ServerApplication
from .in_memory_backend import InMemoryCodesysBackend


def create_server_application(backend: Any) -> ServerApplication:
    """Create the default local server application."""
    return ServerApplication.from_backend(backend)


def create_in_memory_server_application() -> ServerApplication:
    """Create a server application backed by the in-memory demo backend."""
    return create_server_application(InMemoryCodesysBackend())


def create_real_ide_server_application(
    bridge_script_path: str | None = None,
) -> ServerApplication:
    """Create a server application backed by the installed SP20 IDE."""
    return create_server_application(
        CodesysProjectAdapter.from_discovery(
            bridge_script_path=bridge_script_path or str(_default_bridge_script_path())
        )
    )


def _default_bridge_script_path() -> Path:
    return Path(__file__).resolve().parents[1] / "core" / "codesys_bridge.py"
