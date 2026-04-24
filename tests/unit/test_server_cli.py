"""Unit tests for the local server CLI."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.server.cli import main


class ServerCliTests(unittest.TestCase):
    def test_list_tools_prints_summary_table_by_default(self) -> None:
        stream = StringIO()
        with redirect_stdout(stream):
            exit_code = main(["list-tools"])
        self.assertEqual(exit_code, 0)
        output = stream.getvalue()
        self.assertIn("| Category | Name | Function | Code |", output)
        self.assertIn("create_program", output)
        self.assertIn("POU-001", output)

    def test_list_tools_json_view_prints_machine_readable_catalog(self) -> None:
        stream = StringIO()
        with redirect_stdout(stream):
            exit_code = main(["list-tools", "--view", "json"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(stream.getvalue())
        names = [tool["name"] for tool in payload]
        self.assertIn("create_program", names)
        create_program_tool = next(tool for tool in payload if tool["name"] == "create_program")
        self.assertEqual(create_program_tool["code"], "POU-001")
        self.assertEqual(create_program_tool["category"], "pous")

    def test_call_tool_returns_structured_payload(self) -> None:
        stream = StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "call-tool",
                        "create_project",
                        "--arguments",
                        json.dumps(
                            {
                                "project_path": str(Path(temp_dir) / "demo.project"),
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
                exit_code = main(["--log-level", "DEBUG", "--log-json", "list-tools", "--view", "json"])
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        self.assertEqual(exit_code, 0)
        payload = json.loads(stream.getvalue())
        self.assertGreater(len(payload), 0)

    def test_cli_supports_real_ide_backend_option(self) -> None:
        fake_runtime = type(
            "FakeRuntime",
            (),
            {
                "list_tools": staticmethod(lambda: []),
                "export_tool_catalog": staticmethod(lambda: []),
                "serve_stdio": staticmethod(lambda: 0),
                "serve_jsonl": staticmethod(lambda: 0),
                "call_tool": staticmethod(lambda **kwargs: {"ok": True}),
            },
        )()
        with patch(
            "codesys_mcp_server.server.cli.create_runtime",
            return_value=fake_runtime,
        ) as create_runtime:
            stream = StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--backend",
                        "real_ide",
                        "--bridge-script-path",
                        "D:/bridge/codesys_bridge.py",
                        "list-tools",
                    ]
                )
        self.assertEqual(exit_code, 0)
        settings = create_runtime.call_args.args[0]
        self.assertEqual(settings.backend_mode, "real_ide")
        self.assertEqual(settings.bridge_script_path, "D:/bridge/codesys_bridge.py")
