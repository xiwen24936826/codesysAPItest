"""Server configuration models and loaders."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ServerSettings:
    """Configuration for the local server runtime."""

    backend_mode: str = "in_memory"
    log_level: str = "INFO"
    log_json: bool = False

    @classmethod
    def from_env(cls) -> "ServerSettings":
        return cls(
            backend_mode=os.getenv("CODESYS_MCP_BACKEND", "in_memory").strip().lower(),
            log_level=os.getenv("CODESYS_MCP_LOG_LEVEL", "INFO").strip().upper(),
            log_json=_parse_bool(os.getenv("CODESYS_MCP_LOG_JSON", "false")),
        )


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}
