"""Unit tests for server-side tool dispatch."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.server import create_server_application


class FakeBackend:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, path: str, primary: bool = True) -> None:
        self.calls.append({"tool": "create_project", "path": path, "primary": primary})

    def open(self, path: str) -> None:
        self.calls.append({"tool": "open_project", "path": path})

    def save(self, path: str) -> None:
        self.calls.append({"tool": "save_project", "path": path})

    def save_as(self, path: str, target_path: str) -> None:
        self.calls.append({"tool": "save_project", "path": path, "target": target_path})

    def add_controller(self, *args, **kwargs) -> None:
        return None

    def create_program(
        self,
        project_path: str,
        container_path: str,
        name: str,
        language: str = "ST",
    ) -> None:
        self.calls.append(
            {
                "tool": "create_program",
                "project_path": project_path,
                "container_path": container_path,
                "name": name,
                "language": language,
            }
        )

    def create_function_block(self, *args, **kwargs) -> None: return None
    def create_function(self, *args, **kwargs) -> None: return None
    def read_text_document(self, *args, **kwargs) -> dict[str, str]: return {"text": "x"}
    def replace_text_document(self, *args, **kwargs) -> None: return None
    def append_text_document(self, *args, **kwargs) -> None: return None
    def insert_text_document(self, *args, **kwargs) -> None: return None
    def list_objects(self, project_path: str, container_path: str = "/") -> dict[str, object]:
        self.calls.append(
            {
                "tool": "list_project_objects",
                "project_path": project_path,
                "container_path": container_path,
            }
        )
        return {
            "project_path": project_path,
            "container_path": container_path,
            "children": [{"name": "Application", "is_folder": True}],
        }


class ServerApplicationTests(unittest.TestCase):
    def test_list_tools_returns_registered_tool_metadata(self) -> None:
        app = create_server_application(FakeBackend())
        names = [tool.name for tool in app.list_tools()]
        self.assertIn("create_program", names)
        self.assertIn("list_project_objects", names)
        self.assertIn("read_textual_implementation", names)

    def test_call_tool_dispatches_to_service_handler(self) -> None:
        backend = FakeBackend()
        app = create_server_application(backend)
        result = app.call_tool(
            name="create_program",
            arguments={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "name": "MainProgram",
            },
            request_id="server-001",
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.payload["meta"]["request_id"], "server-001")
        self.assertEqual(backend.calls[0]["tool"], "list_project_objects")
        self.assertEqual(backend.calls[-1]["tool"], "create_program")

    def test_call_tool_dispatches_project_scan(self) -> None:
        backend = FakeBackend()
        app = create_server_application(backend)
        result = app.call_tool(
            name="list_project_objects",
            arguments={"project_path": "D:/Projects/demo.project"},
            request_id="server-002",
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.payload["data"]["children"][0]["name"], "Application")
        self.assertEqual(result.payload["meta"]["request_id"], "server-002")
        self.assertEqual(backend.calls[0]["tool"], "list_project_objects")
