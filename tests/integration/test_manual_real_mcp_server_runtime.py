"""Manual real-project integration for the assembled MCP server runtime."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.config import ServerSettings
from codesys_mcp_server.core import CodesysProjectAdapter
from codesys_mcp_server.server import create_runtime


MANUAL_PROJECT_PATH = os.environ.get("CODESYS_MANUAL_PROJECT_PATH")


@unittest.skipUnless(
    MANUAL_PROJECT_PATH,
    "Set CODESYS_MANUAL_PROJECT_PATH to run manual MCP server integration tests.",
)
class ManualRealMcpServerRuntimeTests(unittest.TestCase):
    """End-to-end runtime tests over a user-prepared SP20 project."""

    def setUp(self) -> None:
        self._bridge_script_path = str(
            PROJECT_ROOT / "src" / "codesys_mcp_server" / "core" / "codesys_bridge.py"
        )
        self._adapter = CodesysProjectAdapter.from_discovery(
            bridge_script_path=self._bridge_script_path
        )
        self._runtime = create_runtime(
            ServerSettings(
                backend_mode="real_ide",
                bridge_script_path=self._bridge_script_path,
            )
        )
        self._source_project_path = Path(MANUAL_PROJECT_PATH).resolve()
        self._temp_root = Path(tempfile.gettempdir())
        self._project_copy_path = self._temp_root / (
            "manual_runtime_test_%s.project" % uuid4().hex
        )
        shutil.copy2(self._source_project_path, self._project_copy_path)
        self._project_path = str(self._project_copy_path)

    def tearDown(self) -> None:
        for path in (
            self._project_copy_path,
            self._project_copy_path.with_suffix(".project.precompilecache"),
            self._project_copy_path.with_suffix(".precompilecache"),
        ):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

    def _resolve_test_container_path(self) -> str:
        root_listing = self._adapter.list_objects(
            project_path=self._project_path,
            container_path="/",
        )
        child_names = {child["name"] for child in root_listing["children"]}
        if "Application" in child_names:
            return "Application"
        return "/"

    def _call_tool(
        self,
        name: str,
        arguments: dict[str, object],
        request_id: str,
    ) -> dict[str, object]:
        response = self._runtime.handle_protocol_message(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": name,
                    "arguments": arguments,
                    "request_id": request_id,
                },
            }
        )
        assert response is not None
        return response["result"]["structuredContent"]

    def test_runtime_supports_manual_real_scan_create_write_flow(self) -> None:
        initialize_response = self._runtime.handle_protocol_message(
            {"jsonrpc": "2.0", "id": "init-1", "method": "initialize", "params": {}}
        )
        assert initialize_response is not None
        self.assertEqual(initialize_response["result"]["serverInfo"]["name"], "codesys-mcp-local")

        list_response = self._runtime.handle_protocol_message(
            {"jsonrpc": "2.0", "id": "list-1", "method": "tools/list", "params": {}}
        )
        assert list_response is not None
        tool_names = {tool["name"] for tool in list_response["result"]["tools"]}
        self.assertIn("create_program", tool_names)
        self.assertIn("list_project_objects", tool_names)
        self.assertIn("insert_text_document", tool_names)

        program_name = "RuntimeProgram_%s" % uuid4().hex[:8]

        open_response = self._call_tool(
            "open_project",
            {"project_path": self._project_path},
            "runtime-open-001",
        )
        self.assertTrue(open_response["ok"], open_response)

        root_listing = self._call_tool(
            "list_project_objects",
            {
                "project_path": self._project_path,
                "container_path": "/",
            },
            "runtime-list-root-001",
        )
        self.assertTrue(root_listing["ok"], root_listing)

        container_path = self._resolve_application_path(root_listing["data"]["children"])
        self.assertIsNotNone(container_path)
        assert container_path is not None

        create_response = self._call_tool(
            "create_program",
            {
                "project_path": self._project_path,
                "container_path": container_path,
                "name": program_name,
                "language": "ST",
            },
            "runtime-create-001",
        )
        self.assertTrue(create_response["ok"], create_response)

        declaration_response = self._call_tool(
            "replace_text_document",
            {
                "project_path": self._project_path,
                "container_path": container_path,
                "object_name": program_name,
                "document_kind": "declaration",
                "new_text": (
                    "PROGRAM %s\nVAR\n    Counter: INT;\nEND_VAR" % program_name
                ),
            },
            "runtime-declaration-001",
        )
        self.assertTrue(declaration_response["ok"], declaration_response)
        self.assertTrue(declaration_response["data"]["roundtrip_verified"])

        replace_response = self._call_tool(
            "replace_text_document",
            {
                "project_path": self._project_path,
                "container_path": container_path,
                "object_name": program_name,
                "document_kind": "implementation",
                "new_text": "Counter := 10;\nCounter := Counter + 5;",
            },
            "runtime-replace-001",
        )
        self.assertTrue(replace_response["ok"], replace_response)
        self.assertTrue(replace_response["data"]["roundtrip_verified"])

        read_response = self._call_tool(
            "read_textual_implementation",
            {
                "project_path": self._project_path,
                "container_path": container_path,
                "object_name": program_name,
            },
            "runtime-read-001",
        )
        self.assertTrue(read_response["ok"], read_response)
        final_text = read_response["data"]["text"]
        self.assertIn("Counter := 10;", final_text)
        self.assertIn("Counter := Counter + 5;", final_text)

    def _resolve_application_path(self, root_children: list[dict[str, object]]) -> str | None:
        queue = [child["path"] for child in root_children if child.get("path")]
        for child in root_children:
            if child.get("name") == "Application":
                return child.get("path")  # type: ignore[return-value]

        visited: set[str] = set()
        while queue:
            current = queue.pop(0)
            if not isinstance(current, str) or current in visited:
                continue
            visited.add(current)
            listing = self._call_tool(
                "list_project_objects",
                {
                    "project_path": self._project_path,
                    "container_path": current,
                },
                "runtime-list-%s" % len(visited),
            )
            if not listing["ok"]:
                continue
            for child in listing["data"]["children"]:
                if child.get("name") == "Application":
                    return child.get("path")  # type: ignore[return-value]
                if child.get("path"):
                    queue.append(child["path"])
        return None
