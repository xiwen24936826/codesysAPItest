"""Unit tests for the in-memory offline backend."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.server import InMemoryCodesysBackend


class InMemoryBackendTests(unittest.TestCase):
    def test_program_and_text_flow(self) -> None:
        backend = InMemoryCodesysBackend()
        project_path = "D:/Projects/demo.project"

        backend.create(project_path, primary=True)
        backend.create_program(project_path, "Application", "MainProgram", language="ST")
        backend.replace_text_document(
            project_path,
            "Application",
            "MainProgram",
            "implementation",
            "Counter := 1;",
        )
        backend.append_text_document(
            project_path,
            "Application",
            "MainProgram",
            "implementation",
            "\nCounter := Counter + 1;",
        )
        backend.insert_text_document(
            project_path,
            "Application",
            "MainProgram",
            "implementation",
            "// inserted\n",
            0,
        )

        result = backend.read_text_document(
            project_path,
            "Application",
            "MainProgram",
            "implementation",
        )
        self.assertIn("// inserted", result["text"])
        self.assertIn("Counter := Counter + 1;", result["text"])

    def test_missing_container_raises_lookup_error(self) -> None:
        backend = InMemoryCodesysBackend()
        backend.create("D:/Projects/demo.project")
        with self.assertRaises(LookupError):
            backend.create_program("D:/Projects/demo.project", "Missing", "MainProgram")
