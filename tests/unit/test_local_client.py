"""Unit tests for the local client SDK."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_client_sdk import LocalCodesysMcpClient, ToolExecutionError, ToolNotFoundError
from codesys_mcp_server.server import create_server_application


class FakeBackend:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def create(self, path: str, primary: bool = True) -> None: return None
    def open(self, path: str) -> None: return None
    def save(self, path: str) -> None: return None
    def save_as(self, path: str, target_path: str) -> None: return None
    def add_controller(self, *args, **kwargs) -> None:
        self.calls.append(("add_controller", args, kwargs))

    def create_program(self, *args, **kwargs) -> None:
        self.calls.append(("create_program", args, kwargs))

    def create_function_block(self, *args, **kwargs) -> None:
        self.calls.append(("create_function_block", args, kwargs))

    def create_function(self, *args, **kwargs) -> None:
        self.calls.append(("create_function", args, kwargs))

    def read_text_document(self, *args, **kwargs) -> dict[str, str]:
        self.calls.append(("read_text_document", args, kwargs))
        return {"text": "PROGRAM MainProgram"}

    def replace_text_document(self, *args, **kwargs) -> None:
        self.calls.append(("replace_text_document", args, kwargs))

    def append_text_document(self, *args, **kwargs) -> None:
        self.calls.append(("append_text_document", args, kwargs))

    def insert_text_document(self, *args, **kwargs) -> None:
        self.calls.append(("insert_text_document", args, kwargs))


class LocalClientTests(unittest.TestCase):
    def test_client_lists_tools(self) -> None:
        client = LocalCodesysMcpClient(create_server_application(FakeBackend()))
        names = [tool.name for tool in client.list_tools()]
        self.assertIn("create_program", names)

    def test_client_raises_for_unknown_tool(self) -> None:
        client = LocalCodesysMcpClient(create_server_application(FakeBackend()))
        with self.assertRaises(ToolNotFoundError):
            client.call_tool("missing_tool", {})

    def test_client_calls_convenience_wrapper(self) -> None:
        client = LocalCodesysMcpClient(create_server_application(FakeBackend()))
        result = client.create_program(
            project_path="D:/Projects/demo.project",
            container_path="Application",
            name="MainProgram",
            request_id="client-001",
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.payload["meta"]["request_id"], "client-001")

    def test_client_raises_on_tool_error_payload(self) -> None:
        client = LocalCodesysMcpClient(create_server_application(FakeBackend()))
        with self.assertRaises(ToolExecutionError):
            client.create_program(
                project_path="relative.project",
                container_path="Application",
                name="MainProgram",
            )

    def test_client_supports_project_and_pou_methods(self) -> None:
        backend = FakeBackend()
        client = LocalCodesysMcpClient(create_server_application(backend))

        self.assertTrue(
            client.create_project("D:/Projects/demo.project").ok
        )
        self.assertTrue(
            client.open_project("D:/Projects/demo.project").ok
        )
        self.assertTrue(
            client.save_project(
                "D:/Projects/demo.project",
                save_mode="save_as",
                target_project_path="D:/Projects/demo_copy.project",
            ).ok
        )
        self.assertTrue(
            client.add_controller_device(
                project_path="D:/Projects/demo.project",
                device_name="Controller",
                device_type=4102,
                device_id="0000 0001",
                device_version="1.0.0.0",
            ).ok
        )
        self.assertTrue(
            client.create_function_block(
                project_path="D:/Projects/demo.project",
                container_path="Application",
                name="MotorControl",
            ).ok
        )
        self.assertTrue(
            client.create_function(
                project_path="D:/Projects/demo.project",
                container_path="Application",
                name="ComputeSpeed",
                return_type="INT",
            ).ok
        )
        self.assertTrue(
            client.read_textual_declaration(
                project_path="D:/Projects/demo.project",
                container_path="Application",
                object_name="MotorControl",
            ).ok
        )
