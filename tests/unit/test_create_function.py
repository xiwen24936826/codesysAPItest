"""Unit tests for the create_function service module."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.services.pous.create_function import create_function


class FakeFunctionCreator:
    """Simple function creator test double."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create_function(
        self,
        project_path: str,
        container_path: str,
        name: str,
        return_type: str,
        language: str = "ST",
    ) -> None:
        self.calls.append(
            {
                "project_path": project_path,
                "container_path": container_path,
                "name": name,
                "return_type": return_type,
                "language": language,
            }
        )


class MissingProjectFunctionCreator:
    """Function creator test double that simulates a missing project."""

    def create_function(
        self,
        project_path: str,
        container_path: str,
        name: str,
        return_type: str,
        language: str = "ST",
    ) -> None:
        raise FileNotFoundError(project_path)


class CreateFunctionTests(unittest.TestCase):
    """Behavioral tests for the create_function MCP service."""

    def test_create_function_returns_success_response(self) -> None:
        creator = FakeFunctionCreator()

        response = create_function(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "name": "CalculateSpeed",
                "return_type": "REAL",
                "language": "st",
            },
            function_creator=creator,
            request_id="req-fn-001",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["data"]["object_type"], "function")
        self.assertEqual(response["data"]["return_type"], "REAL")
        self.assertEqual(response["data"]["language"], "ST")

    def test_create_function_requires_return_type(self) -> None:
        creator = FakeFunctionCreator()

        response = create_function(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "name": "CalculateSpeed",
            },
            function_creator=creator,
            request_id="req-fn-002",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "return_type")
        self.assertEqual(creator.calls, [])

    def test_create_function_reports_missing_project(self) -> None:
        response = create_function(
            request={
                "project_path": "D:/Projects/missing.project",
                "container_path": "Application",
                "name": "CalculateSpeed",
                "return_type": "REAL",
            },
            function_creator=MissingProjectFunctionCreator(),
            request_id="req-fn-003",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "PROJECT_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
