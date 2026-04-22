"""Unit tests for the create_program service module."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.services.pous.create_program import create_program


class FakeProgramCreator:
    """Simple program creator test double."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create_program(
        self,
        project_path: str,
        container_path: str,
        name: str,
        language: str = "ST",
    ) -> None:
        self.calls.append(
            {
                "project_path": project_path,
                "container_path": container_path,
                "name": name,
                "language": language,
            }
        )


class LookupFailingProgramCreator:
    """Program creator that simulates missing containers."""

    def create_program(
        self,
        project_path: str,
        container_path: str,
        name: str,
        language: str = "ST",
    ) -> None:
        raise LookupError("Application/POUs was not found.")


class CreateProgramTests(unittest.TestCase):
    """Behavioral tests for the create_program MCP service."""

    def test_create_program_returns_success_response(self) -> None:
        creator = FakeProgramCreator()

        response = create_program(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "name": "MainProgram",
                "language": "st",
            },
            program_creator=creator,
            request_id="req-pou-001",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["tool"], "create_program")
        self.assertEqual(response["data"]["object_type"], "program")
        self.assertEqual(response["data"]["language"], "ST")
        self.assertEqual(response["meta"]["request_id"], "req-pou-001")
        self.assertEqual(
            creator.calls,
            [
                {
                    "project_path": "D:/Projects/demo.project",
                    "container_path": "Application",
                    "name": "MainProgram",
                    "language": "ST",
                }
            ],
        )

    def test_create_program_rejects_relative_project_paths(self) -> None:
        creator = FakeProgramCreator()

        response = create_program(
            request={
                "project_path": "demo.project",
                "container_path": "Application",
                "name": "MainProgram",
            },
            program_creator=creator,
            request_id="req-pou-002",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "project_path")
        self.assertEqual(creator.calls, [])

    def test_create_program_reports_missing_container(self) -> None:
        response = create_program(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application/POUs",
                "name": "MainProgram",
            },
            program_creator=LookupFailingProgramCreator(),
            request_id="req-pou-003",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "POU_CONTAINER_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
