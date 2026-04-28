"""Unit tests for tool registry assembly."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.tools import ToolRegistry, build_tool_registry
from codesys_mcp_server.tools.catalog import TOOL_CATALOG_BY_NAME


class FakeBackend:
    def create(self, path: str, primary: bool = True) -> None: return None
    def open(self, path: str) -> None: return None
    def save(self, path: str) -> None: return None
    def save_as(self, path: str, target_path: str) -> None: return None
    def add_controller(self, *args, **kwargs) -> None: return None
    def create_program(self, *args, **kwargs) -> None: return None
    def create_function_block(self, *args, **kwargs) -> None: return None
    def create_function(self, *args, **kwargs) -> None: return None
    def read_text_document(self, *args, **kwargs) -> dict[str, str]: return {"text": ""}
    def replace_text_document(self, *args, **kwargs) -> None: return None
    def append_text_document(self, *args, **kwargs) -> None: return None
    def insert_text_document(self, *args, **kwargs) -> None: return None


class ToolRegistryTests(unittest.TestCase):
    def test_register_rejects_duplicate_names(self) -> None:
        registry = ToolRegistry()
        registry.register(
            TOOL_CATALOG_BY_NAME["create_project"],
            lambda request, request_id=None: {},
        )
        with self.assertRaises(ValueError):
            registry.register(
                TOOL_CATALOG_BY_NAME["create_project"],
                lambda request, request_id=None: {},
            )

    def test_build_tool_registry_contains_phase1_tools(self) -> None:
        registry = build_tool_registry(FakeBackend())
        names = [definition.name for definition in registry.list_definitions()]
        self.assertIn("create_project", names)
        self.assertIn("create_program", names)
        self.assertIn("insert_text_document", names)
