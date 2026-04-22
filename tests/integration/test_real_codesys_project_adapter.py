"""Optional integration tests against a locally installed SP20 IDE."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.core.project_adapter import CodesysProjectAdapter
from codesys_mcp_server.services.projects import (
    create_project,
    open_project,
    save_project,
)


class RealCodesysProjectAdapterTests(unittest.TestCase):
    """Integration tests that exercise the real installed IDE."""

    def setUp(self) -> None:
        self._temp_root = Path(tempfile.gettempdir())
        self._paths_to_cleanup: list[Path] = []
        bridge_script = PROJECT_ROOT / "src" / "codesys_mcp_server" / "core" / "codesys_bridge.py"
        self._adapter = CodesysProjectAdapter.from_discovery(
            bridge_script_path=str(bridge_script)
        )

    def tearDown(self) -> None:
        for path in self._paths_to_cleanup:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

    def test_create_open_and_save_as_with_real_ide(self) -> None:
        suffix = uuid4().hex
        project_path = self._temp_root / ("integration_demo_%s.project" % suffix)
        copied_project_path = self._temp_root / ("integration_demo_%s_copy.project" % suffix)
        self._paths_to_cleanup.extend([project_path, copied_project_path])

        create_response = create_project(
            request={
                "project_path": str(project_path),
                "project_mode": "empty",
                "set_as_primary": True,
            },
            project_creator=self._adapter,
            request_id="real-create-001",
        )
        self.assertTrue(create_response["ok"], create_response)
        self.assertTrue(project_path.exists())

        open_response = open_project(
            request={"project_path": str(project_path)},
            project_opener=self._adapter,
            request_id="real-open-001",
        )
        self.assertTrue(open_response["ok"], open_response)

        save_response = save_project(
            request={
                "project_path": str(project_path),
                "save_mode": "save_as",
                "target_project_path": str(copied_project_path),
            },
            project_saver=self._adapter,
            request_id="real-save-001",
        )
        self.assertTrue(save_response["ok"], save_response)
        self.assertTrue(copied_project_path.exists())


if __name__ == "__main__":
    unittest.main()
