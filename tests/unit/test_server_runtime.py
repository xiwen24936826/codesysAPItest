"""Unit tests for standardized server runtime."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
import json
import sys
import unittest


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
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        )
        assert response is not None
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], 1)
        self.assertIn("serverInfo", response["result"])
        self.assertIn("capabilities", response["result"])

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
        self.assertTrue(response["result"]["ok"])
        self.assertEqual(response["id"], "call-1")

    def test_runtime_returns_protocol_error_for_unknown_method(self) -> None:
        runtime = create_runtime(ServerSettings())
        response = runtime.handle_protocol_message(
            {"jsonrpc": "2.0", "id": "bad-1", "method": "missing/method"}
        )
        assert response is not None
        self.assertEqual(response["error"]["code"], -32601)
