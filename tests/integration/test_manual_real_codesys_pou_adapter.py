"""Optional real-IDE tests that operate on a user-prepared SP20 project."""

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

from codesys_mcp_server.core.project_adapter import CodesysProjectAdapter
from codesys_mcp_server.services.projects import open_project
from codesys_mcp_server.services.pous import (
    append_text_document,
    create_program,
    insert_text_document,
    read_textual_implementation,
    replace_text_document,
)


MANUAL_PROJECT_PATH = os.environ.get("CODESYS_MANUAL_PROJECT_PATH")


@unittest.skipUnless(
    MANUAL_PROJECT_PATH,
    "Set CODESYS_MANUAL_PROJECT_PATH to run manual SP20 POU integration tests.",
)
class ManualRealCodesysPouAdapterTests(unittest.TestCase):
    """Integration tests that require a user-created SP20 project."""

    def setUp(self) -> None:
        bridge_script = PROJECT_ROOT / "src" / "codesys_mcp_server" / "core" / "codesys_bridge.py"
        self._adapter = CodesysProjectAdapter.from_discovery(
            bridge_script_path=str(bridge_script)
        )
        self._source_project_path = Path(MANUAL_PROJECT_PATH).resolve()
        self._temp_root = Path(tempfile.gettempdir())
        self._project_copy_path = self._temp_root / (
            "manual_pou_test_%s.project" % uuid4().hex
        )
        shutil.copy2(self._source_project_path, self._project_copy_path)
        self._project_path = str(self._project_copy_path)

    def tearDown(self) -> None:
        try:
            self._project_copy_path.unlink(missing_ok=True)
        except OSError:
            pass

    def test_manual_project_supports_pou_create_and_text_updates(self) -> None:
        program_name = "AutoProgram_%s" % uuid4().hex[:8]

        open_response = open_project(
            request={"project_path": self._project_path},
            project_opener=self._adapter,
            request_id="manual-open-001",
        )
        self.assertTrue(open_response["ok"], open_response)

        create_response = create_program(
            request={
                "project_path": self._project_path,
                "container_path": "Application",
                "name": program_name,
                "language": "ST",
            },
            program_creator=self._adapter,
            request_id="manual-program-001",
        )
        self.assertTrue(create_response["ok"], create_response)

        replace_response = replace_text_document(
            request={
                "project_path": self._project_path,
                "container_path": "Application",
                "object_name": program_name,
                "document_kind": "implementation",
                "new_text": "Counter := 1;",
            },
            text_document_replacer=self._adapter,
            request_id="manual-replace-001",
        )
        self.assertTrue(replace_response["ok"], replace_response)

        append_response = append_text_document(
            request={
                "project_path": self._project_path,
                "container_path": "Application",
                "object_name": program_name,
                "document_kind": "implementation",
                "text_to_append": "\nCounter := Counter + 1;",
            },
            text_document_appender=self._adapter,
            request_id="manual-append-001",
        )
        self.assertTrue(append_response["ok"], append_response)

        insert_response = insert_text_document(
            request={
                "project_path": self._project_path,
                "container_path": "Application",
                "object_name": program_name,
                "document_kind": "implementation",
                "text_to_insert": "// inserted by Codex\n",
                "insertion_offset": 0,
            },
            text_document_inserter=self._adapter,
            request_id="manual-insert-001",
        )
        self.assertTrue(insert_response["ok"], insert_response)

        read_response = read_textual_implementation(
            request={
                "project_path": self._project_path,
                "container_path": "Application",
                "object_name": program_name,
            },
            text_document_reader=self._adapter,
            request_id="manual-read-001",
        )
        self.assertTrue(read_response["ok"], read_response)
        self.assertIn("// inserted by Codex", read_response["data"]["text"])
        self.assertIn("Counter := Counter + 1;", read_response["data"]["text"])


if __name__ == "__main__":
    unittest.main()
