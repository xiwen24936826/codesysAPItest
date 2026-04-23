"""Unit tests for standardized server runtime."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
import json
import sys
import unittest
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.config import ServerSettings
from codesys_mcp_server.server import create_runtime


class ServerRuntimeTests(unittest.TestCase):
    def test_runtime_lists_tools(self) -> None:
        runtime = create_runtime(ServerSettings())
        names = [tool["name"] for tool in runtime.list_tools()]
        self.assertIn("create_program", names)
        self.assertIn("list_project_objects", names)
        create_program_tool = next(
            tool for tool in runtime.list_tools() if tool["name"] == "create_program"
        )
        self.assertIn("inputSchema", create_program_tool)

    def test_runtime_serves_jsonl(self) -> None:
        runtime = create_runtime(ServerSettings())
        stdin = StringIO('{"jsonrpc":"2.0","id":"req-1","method":"tools/list"}\n')
        stdout = StringIO()
        exit_code = runtime.serve_jsonl(stdin=stdin, stdout=stdout)
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue().strip())
        self.assertEqual(payload["jsonrpc"], "2.0")
        self.assertEqual(payload["id"], "req-1")
        self.assertGreater(len(payload["result"]["tools"]), 0)

    def test_runtime_handles_initialize(self) -> None:
        runtime = create_runtime(ServerSettings())
        response = runtime.handle_protocol_message(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"},
            }
        )
        assert response is not None
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], 1)
        self.assertIn("serverInfo", response["result"])
        self.assertIn("capabilities", response["result"])
        self.assertEqual(response["result"]["protocolVersion"], "2025-06-18")

    def test_runtime_handles_tool_call(self) -> None:
        runtime = create_runtime(ServerSettings())
        response = runtime.handle_protocol_message(
            {
                "jsonrpc": "2.0",
                "id": "call-1",
                "method": "tools/call",
                "params": {
                    "name": "create_project",
                    "arguments": {
                        "project_path": "D:/Projects/demo.project",
                        "project_mode": "empty",
                        "set_as_primary": True,
                    },
                },
            }
        )
        assert response is not None
        self.assertFalse(response["result"]["isError"])
        self.assertTrue(response["result"]["structuredContent"]["ok"])
        self.assertGreater(len(response["result"]["content"]), 0)
        self.assertEqual(response["id"], "call-1")

    def test_runtime_returns_protocol_error_for_unknown_method(self) -> None:
        runtime = create_runtime(ServerSettings())
        response = runtime.handle_protocol_message(
            {"jsonrpc": "2.0", "id": "bad-1", "method": "missing/method"}
        )
        assert response is not None
        self.assertEqual(response["error"]["code"], -32601)

    def test_runtime_returns_protocol_error_for_unknown_tool(self) -> None:
        runtime = create_runtime(ServerSettings())
        response = runtime.handle_protocol_message(
            {
                "jsonrpc": "2.0",
                "id": "tool-404",
                "method": "tools/call",
                "params": {"name": "missing_tool", "arguments": {}},
            }
        )
        assert response is not None
        self.assertEqual(response["error"]["code"], -32602)

    def test_runtime_supports_real_ide_backend_selection(self) -> None:
        fake_app = object()
        with patch(
            "codesys_mcp_server.server.runtime.create_real_ide_server_application",
            return_value=fake_app,
        ) as create_real:
            runtime = create_runtime(
                ServerSettings(
                    backend_mode="real_ide",
                    bridge_script_path="D:/bridge/codesys_bridge.py",
                )
            )
        self.assertIs(runtime._app, fake_app)
        create_real.assert_called_once_with(
            bridge_script_path="D:/bridge/codesys_bridge.py"
        )
