"""Server configuration models and loaders."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ServerSettings:
    """Configuration for the local server runtime."""

    backend_mode: str = "in_memory"
    bridge_script_path: str | None = None
    log_level: str = "INFO"
    log_json: bool = False

    @classmethod
    def from_env(cls) -> "ServerSettings":
        return cls(
            backend_mode=os.getenv("CODESYS_MCP_BACKEND", "in_memory").strip().lower(),
            bridge_script_path=_optional_str(
                os.getenv("CODESYS_MCP_BRIDGE_SCRIPT_PATH")
            ),
            log_level=os.getenv("CODESYS_MCP_LOG_LEVEL", "INFO").strip().upper(),
            log_json=_parse_bool(os.getenv("CODESYS_MCP_LOG_JSON", "false")),
        )


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _optional_str(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
