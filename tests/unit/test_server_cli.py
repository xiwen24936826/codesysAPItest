"""Unit tests for the local server CLI."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import json
import os
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.server.cli import main


class ServerCliTests(unittest.TestCase):
    def test_list_tools_prints_registered_tools(self) -> None:
        stream = StringIO()
        with redirect_stdout(stream):
            exit_code = main(["list-tools"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(stream.getvalue())
        names = [tool["name"] for tool in payload]
        self.assertIn("create_program", names)

    def test_call_tool_returns_structured_payload(self) -> None:
        stream = StringIO()
        with redirect_stdout(stream):
            exit_code = main(
                [
                    "call-tool",
                    "create_project",
                    "--arguments",
                    json.dumps(
                        {
                            "project_path": "D:/Projects/demo.project",
                            "project_mode": "empty",
                            "set_as_primary": True,
                        }
                    ),
                    "--request-id",
                    "cli-001",
                ]
            )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stream.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["meta"]["request_id"], "cli-001")

    def test_serve_stdio_handles_list_tools(self) -> None:
        input_stream = StringIO('{"jsonrpc":"2.0","id":"list-1","method":"tools/list"}\n')
        output_stream = StringIO()
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        try:
            sys.stdin = input_stream
            sys.stdout = output_stream
            exit_code = main(["serve-stdio"])
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        self.assertEqual(exit_code, 0)
        payload = json.loads(output_stream.getvalue().strip())
        self.assertEqual(payload["jsonrpc"], "2.0")
        self.assertEqual(payload["id"], "list-1")
        self.assertGreater(len(payload["result"]["tools"]), 0)

    def test_serve_jsonl_alias_uses_same_protocol(self) -> None:
        input_stream = StringIO('{"jsonrpc":"2.0","id":"ping-1","method":"ping"}\n')
        output_stream = StringIO()
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        try:
            sys.stdin = input_stream
            sys.stdout = output_stream
            exit_code = main(["serve-jsonl"])
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        self.assertEqual(exit_code, 0)
        payload = json.loads(output_stream.getvalue().strip())
        self.assertEqual(payload["result"]["pong"], True)

    def test_cli_accepts_logging_options(self) -> None:
        stream = StringIO()
        previous = {
            "CODESYS_MCP_LOG_LEVEL": os.environ.get("CODESYS_MCP_LOG_LEVEL"),
            "CODESYS_MCP_LOG_JSON": os.environ.get("CODESYS_MCP_LOG_JSON"),
        }
        try:
            with redirect_stdout(stream):
                exit_code = main(["--log-level", "DEBUG", "--log-json", "list-tools"])
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        self.assertEqual(exit_code, 0)
        payload = json.loads(stream.getvalue())
        self.assertGreater(len(payload), 0)
