"""Unit tests for config and logging helpers."""

from __future__ import annotations

from pathlib import Path
import logging
import os
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.config import ServerSettings
from codesys_mcp_server.logging import configure_logging


class ConfigAndLoggingTests(unittest.TestCase):
    def test_settings_from_env(self) -> None:
        previous = {
            "CODESYS_MCP_BACKEND": os.environ.get("CODESYS_MCP_BACKEND"),
            "CODESYS_MCP_LOG_LEVEL": os.environ.get("CODESYS_MCP_LOG_LEVEL"),
            "CODESYS_MCP_LOG_JSON": os.environ.get("CODESYS_MCP_LOG_JSON"),
        }
        try:
            os.environ["CODESYS_MCP_BACKEND"] = "in_memory"
            os.environ["CODESYS_MCP_LOG_LEVEL"] = "debug"
            os.environ["CODESYS_MCP_LOG_JSON"] = "true"
            settings = ServerSettings.from_env()
            self.assertEqual(settings.backend_mode, "in_memory")
            self.assertEqual(settings.log_level, "DEBUG")
            self.assertTrue(settings.log_json)
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_configure_logging_sets_root_level(self) -> None:
        configure_logging(level="WARNING", json_output=False)
        self.assertEqual(logging.getLogger().level, logging.WARNING)
