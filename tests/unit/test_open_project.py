"""Unit tests for the open_project service module."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.services.projects.open_project import open_project


class FakeProjectOpener:
    """Simple project opener test double."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def open(self, path: str) -> None:
        self.calls.append({"path": path})


class MissingProjectOpener:
    """Project opener test double that simulates a missing file."""

    def open(self, path: str) -> None:
        raise FileNotFoundError(path)


class RaisingProjectOpener:
    """Project opener test double that simulates adapter failures."""

    def open(self, path: str) -> None:
        raise RuntimeError("adapter failure")


class OpenProjectTests(unittest.TestCase):
    """Behavioral tests for the open_project MCP service."""

    def test_open_project_returns_success_response(self) -> None:
        opener = FakeProjectOpener()

        response = open_project(
            request={"project_path": "D:/Projects/demo.project"},
            project_opener=opener,
            request_id="req-101",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["tool"], "open_project")
        self.assertIsNone(response["error"])
        self.assertEqual(response["data"]["project_path"], "D:/Projects/demo.project")
        self.assertEqual(response["data"]["project_name"], "demo")
        self.assertTrue(response["data"]["is_primary"])
        self.assertEqual(response["meta"]["request_id"], "req-101")
        self.assertEqual(opener.calls, [{"path": "D:/Projects/demo.project"}])

    def test_open_project_rejects_missing_path(self) -> None:
        opener = FakeProjectOpener()

        response = open_project(
            request={},
            project_opener=opener,
            request_id="req-102",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "project_path")
        self.assertEqual(opener.calls, [])

    def test_open_project_rejects_relative_paths(self) -> None:
        opener = FakeProjectOpener()

        response = open_project(
            request={"project_path": "relative/demo.project"},
            project_opener=opener,
            request_id="req-103",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "project_path")
        self.assertEqual(opener.calls, [])

    def test_open_project_maps_missing_file_to_project_not_found(self) -> None:
        response = open_project(
            request={"project_path": "D:/Projects/missing.project"},
            project_opener=MissingProjectOpener(),
            request_id="req-104",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "PROJECT_NOT_FOUND")
        self.assertEqual(
            response["error"]["details"]["project_path"],
            "D:/Projects/missing.project",
        )

    def test_open_project_wraps_unexpected_adapter_errors(self) -> None:
        response = open_project(
            request={"project_path": "D:/Projects/demo.project"},
            project_opener=RaisingProjectOpener(),
            request_id="req-105",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "INTERNAL_ERROR")
        self.assertEqual(response["meta"]["request_id"], "req-105")


if __name__ == "__main__":
    unittest.main()

