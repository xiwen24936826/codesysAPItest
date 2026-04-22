"""Unit tests for the save_project service module."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.services.projects.save_project import save_project


class FakeProjectSaver:
    """Simple project saver test double."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def save(self, path: str) -> None:
        self.calls.append({"method": "save", "path": path})

    def save_as(self, path: str, target_path: str) -> None:
        self.calls.append(
            {"method": "save_as", "path": path, "target_path": target_path}
        )


class MissingProjectSaver:
    """Project saver test double that simulates a missing file."""

    def save(self, path: str) -> None:
        raise FileNotFoundError(path)

    def save_as(self, path: str, target_path: str) -> None:
        raise FileNotFoundError(path)


class RaisingProjectSaver:
    """Project saver test double that simulates adapter failures."""

    def save(self, path: str) -> None:
        raise RuntimeError("adapter failure")

    def save_as(self, path: str, target_path: str) -> None:
        raise RuntimeError("adapter failure")


class SaveProjectTests(unittest.TestCase):
    """Behavioral tests for the save_project MCP service."""

    def test_save_project_returns_success_response_for_save_mode(self) -> None:
        saver = FakeProjectSaver()

        response = save_project(
            request={
                "project_path": "D:/Projects/demo.project",
                "save_mode": "save",
            },
            project_saver=saver,
            request_id="req-201",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["tool"], "save_project")
        self.assertIsNone(response["error"])
        self.assertEqual(response["data"]["project_path"], "D:/Projects/demo.project")
        self.assertEqual(response["data"]["save_mode"], "save")
        self.assertTrue(response["data"]["saved"])
        self.assertEqual(response["meta"]["request_id"], "req-201")
        self.assertEqual(
            saver.calls,
            [{"method": "save", "path": "D:/Projects/demo.project"}],
        )

    def test_save_project_returns_success_response_for_save_as_mode(self) -> None:
        saver = FakeProjectSaver()

        response = save_project(
            request={
                "project_path": "D:/Projects/demo.project",
                "save_mode": "save_as",
                "target_project_path": "D:/Projects/demo_copy.project",
            },
            project_saver=saver,
            request_id="req-202",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["data"]["project_path"], "D:/Projects/demo_copy.project")
        self.assertEqual(response["data"]["save_mode"], "save_as")
        self.assertTrue(response["data"]["saved"])
        self.assertEqual(
            saver.calls,
            [
                {
                    "method": "save_as",
                    "path": "D:/Projects/demo.project",
                    "target_path": "D:/Projects/demo_copy.project",
                }
            ],
        )

    def test_save_project_rejects_missing_path(self) -> None:
        saver = FakeProjectSaver()

        response = save_project(
            request={"save_mode": "save"},
            project_saver=saver,
            request_id="req-203",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "project_path")
        self.assertEqual(saver.calls, [])

    def test_save_project_rejects_missing_target_for_save_as(self) -> None:
        saver = FakeProjectSaver()

        response = save_project(
            request={
                "project_path": "D:/Projects/demo.project",
                "save_mode": "save_as",
            },
            project_saver=saver,
            request_id="req-204",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "target_project_path")
        self.assertEqual(saver.calls, [])

    def test_save_project_maps_missing_file_to_project_not_found(self) -> None:
        response = save_project(
            request={
                "project_path": "D:/Projects/missing.project",
                "save_mode": "save",
            },
            project_saver=MissingProjectSaver(),
            request_id="req-205",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "PROJECT_NOT_FOUND")
        self.assertEqual(
            response["error"]["details"]["project_path"],
            "D:/Projects/missing.project",
        )

    def test_save_project_wraps_unexpected_adapter_errors(self) -> None:
        response = save_project(
            request={
                "project_path": "D:/Projects/demo.project",
                "save_mode": "save",
            },
            project_saver=RaisingProjectSaver(),
            request_id="req-206",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "SAVE_FAILED")
        self.assertEqual(response["meta"]["request_id"], "req-206")


if __name__ == "__main__":
    unittest.main()

