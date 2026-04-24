"""Unit tests for the canonical tool catalog and schema validation."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.tools.catalog import (  # noqa: E402
    TOOL_CATALOG,
    TOOL_CATALOG_BY_NAME,
    ToolArgumentSchemaError,
    validate_tool_arguments,
)


class ToolCatalogTests(unittest.TestCase):
    def test_tool_catalog_names_are_unique(self) -> None:
        self.assertEqual(len(TOOL_CATALOG), len({entry.name for entry in TOOL_CATALOG}))

    def test_validate_tool_arguments_rejects_unexpected_fields(self) -> None:
        with self.assertRaises(ToolArgumentSchemaError):
            validate_tool_arguments(
                TOOL_CATALOG_BY_NAME["create_project"],
                {
                    "project_path": "D:/Projects/demo.project",
                    "project_mode": "empty",
                    "unexpected": True,
                },
            )

    def test_validate_tool_arguments_rejects_invalid_enum_values(self) -> None:
        with self.assertRaises(ToolArgumentSchemaError):
            validate_tool_arguments(
                TOOL_CATALOG_BY_NAME["save_project"],
                {
                    "project_path": "D:/Projects/demo.project",
                    "save_mode": "write",
                },
            )

    def test_validate_tool_arguments_accepts_valid_array_items(self) -> None:
        validate_tool_arguments(
            TOOL_CATALOG_BY_NAME["create_function_block"],
            {
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "name": "MotorControl",
                "interfaces": ["IStartable", "IResettable"],
            },
        )


if __name__ == "__main__":
    unittest.main()
