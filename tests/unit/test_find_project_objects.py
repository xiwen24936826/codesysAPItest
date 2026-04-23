"""Unit tests for the find_project_objects service module."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.services.projects.find_project_objects import (  # noqa: E402
    find_project_objects,
)


class FakeProjectObjectFinder:
    """Simple object-finding test double."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def find_objects(
        self,
        project_path: str,
        object_name: str,
        container_path: str = "/",
        recursive: bool = True,
    ) -> dict[str, object]:
        self.calls.append(
            {
                "project_path": project_path,
                "object_name": object_name,
                "container_path": container_path,
                "recursive": recursive,
            }
        )
        return {
            "project_path": project_path,
            "container_path": container_path,
            "matches": [
                {
                    "name": object_name,
                    "path": "MyController/Plc Logic/Application/%s" % object_name,
                    "is_folder": False,
                    "can_browse": False,
                    "child_count": 0,
                    "is_device": False,
                    "device_identification": None,
                    "object_type": "program",
                }
            ],
        }


class FailingProjectObjectFinder:
    """Object finder that simulates a missing container."""

    def find_objects(
        self,
        project_path: str,
        object_name: str,
        container_path: str = "/",
        recursive: bool = True,
    ) -> dict[str, object]:
        raise LookupError("Container '%s' was not found." % container_path)


class FindProjectObjectsTests(unittest.TestCase):
    """Behavioral tests for the find_project_objects MCP service."""

    def test_find_project_objects_returns_structured_matches(self) -> None:
        finder = FakeProjectObjectFinder()

        response = find_project_objects(
            request={
                "project_path": "D:/Projects/demo.project",
                "object_name": "PLC_PRG",
                "container_path": "/",
                "recursive": True,
            },
            project_object_finder=finder,
            request_id="req-find-001",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["tool"], "find_project_objects")
        self.assertEqual(response["data"]["object_name"], "PLC_PRG")
        self.assertTrue(response["data"]["recursive"])
        self.assertEqual(response["data"]["matches"][0]["name"], "PLC_PRG")
        self.assertEqual(
            response["data"]["matches"][0]["path"],
            "MyController/Plc Logic/Application/PLC_PRG",
        )
        self.assertFalse(response["data"]["matches"][0]["is_device"])
        self.assertEqual(response["data"]["matches"][0]["object_type"], "program")
        self.assertEqual(response["meta"]["request_id"], "req-find-001")
        self.assertEqual(
            finder.calls,
            [
                {
                    "project_path": "D:/Projects/demo.project",
                    "object_name": "PLC_PRG",
                    "container_path": "/",
                    "recursive": True,
                }
            ],
        )

    def test_find_project_objects_rejects_missing_object_name(self) -> None:
        response = find_project_objects(
            request={"project_path": "D:/Projects/demo.project"},
            project_object_finder=FakeProjectObjectFinder(),
            request_id="req-find-002",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "object_name")

    def test_find_project_objects_rejects_non_boolean_recursive(self) -> None:
        response = find_project_objects(
            request={
                "project_path": "D:/Projects/demo.project",
                "object_name": "Application",
                "recursive": "yes",
            },
            project_object_finder=FakeProjectObjectFinder(),
            request_id="req-find-003",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "recursive")

    def test_find_project_objects_reports_missing_container(self) -> None:
        response = find_project_objects(
            request={
                "project_path": "D:/Projects/demo.project",
                "object_name": "Application",
                "container_path": "Missing",
            },
            project_object_finder=FailingProjectObjectFinder(),
            request_id="req-find-004",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "CONTAINER_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
