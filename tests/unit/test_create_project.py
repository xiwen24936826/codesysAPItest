"""Unit tests for the create_project service module."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.services.projects.create_project import create_project


class FakeProjectCreator:
    """Simple project creator test double."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, path: str, primary: bool = True) -> None:
        self.calls.append({"path": path, "primary": primary})


class RaisingProjectCreator:
    """Project creator test double that simulates adapter failures."""

    def create(self, path: str, primary: bool = True) -> None:
        raise RuntimeError("adapter failure")


class CreateProjectTests(unittest.TestCase):
    """Behavioral tests for the create_project MCP service."""

    def test_create_project_returns_success_response_for_empty_mode(self) -> None:
        creator = FakeProjectCreator()

        response = create_project(
            request={
                "project_path": "D:/Projects/demo.project",
                "project_mode": "empty",
                "set_as_primary": True,
            },
            project_creator=creator,
            request_id="req-001",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["tool"], "create_project")
        self.assertIsNone(response["error"])
        self.assertEqual(response["data"]["project_path"], "D:/Projects/demo.project")
        self.assertEqual(response["data"]["project_name"], "demo")
        self.assertEqual(response["data"]["project_mode"], "empty")
        self.assertTrue(response["data"]["is_primary"])
        self.assertEqual(response["meta"]["request_id"], "req-001")
        self.assertEqual(
            creator.calls,
            [{"path": "D:/Projects/demo.project", "primary": True}],
        )

    def test_create_project_rejects_relative_paths(self) -> None:
        creator = FakeProjectCreator()

        response = create_project(
            request={
                "project_path": "relative/demo.project",
                "project_mode": "empty",
            },
            project_creator=creator,
            request_id="req-002",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "project_path")
        self.assertEqual(creator.calls, [])

    def test_create_project_requires_template_path_for_template_mode(self) -> None:
        creator = FakeProjectCreator()

        response = create_project(
            request={
                "project_path": "D:/Projects/demo.project",
                "project_mode": "template",
            },
            project_creator=creator,
            request_id="req-003",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "template_project_path")
        self.assertEqual(creator.calls, [])

    def test_create_project_reports_template_mode_as_not_implemented_in_phase1(self) -> None:
        creator = FakeProjectCreator()

        response = create_project(
            request={
                "project_path": "D:/Projects/demo.project",
                "project_mode": "template",
                "template_project_path": "D:/Templates/base.project",
            },
            project_creator=creator,
            request_id="req-004",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("not implemented", response["error"]["message"])
        self.assertEqual(creator.calls, [])

    def test_create_project_wraps_unexpected_adapter_errors(self) -> None:
        response = create_project(
            request={
                "project_path": "D:/Projects/demo.project",
                "project_mode": "empty",
            },
            project_creator=RaisingProjectCreator(),
            request_id="req-005",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "INTERNAL_ERROR")
        self.assertEqual(response["meta"]["request_id"], "req-005")


if __name__ == "__main__":
    unittest.main()
