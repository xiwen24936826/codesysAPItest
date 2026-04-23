"""Unit tests for the list_project_objects service module."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.services.projects.list_project_objects import (  # noqa: E402
    list_project_objects,
)


class FakeProjectObjectLister:
    """Simple object-listing test double."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def list_objects(
        self,
        project_path: str,
        container_path: str = "/",
    ) -> dict[str, object]:
        self.calls.append(
            {
                "project_path": project_path,
                "container_path": container_path,
            }
        )
        if container_path == "/":
            return {
                "project_path": project_path,
                "container_path": "/",
                "children": [
                    {
                        "name": "MyController",
                        "is_folder": False,
                        "can_browse": True,
                        "child_count": 3,
                        "is_device": True,
                        "device_identification": {"type": "controller", "id": "Schneider_M310"},
                    },
                    {
                        "name": "Project Information",
                        "is_folder": False,
                        "can_browse": False,
                        "child_count": 0,
                        "is_device": False,
                        "device_identification": None,
                    },
                ],
            }
        return {
            "project_path": project_path,
            "container_path": container_path,
            "children": [
                {
                    "name": "Application",
                    "is_folder": False,
                    "can_browse": True,
                    "child_count": 6,
                    "is_device": False,
                    "device_identification": None,
                },
                {
                    "name": "PLC_PRG",
                    "is_folder": False,
                    "can_browse": False,
                    "child_count": 0,
                    "object_type": "program",
                    "is_device": False,
                    "device_identification": None,
                },
            ],
        }


class FailingProjectObjectLister:
    """Object lister that simulates a missing container."""

    def list_objects(
        self,
        project_path: str,
        container_path: str = "/",
    ) -> dict[str, object]:
        raise LookupError("Container '%s' was not found." % container_path)


class ListProjectObjectsTests(unittest.TestCase):
    """Behavioral tests for the list_project_objects MCP service."""

    def test_list_project_objects_returns_root_children(self) -> None:
        lister = FakeProjectObjectLister()

        response = list_project_objects(
            request={"project_path": "D:/Projects/demo.project"},
            project_object_lister=lister,
            request_id="req-list-001",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["tool"], "list_project_objects")
        self.assertEqual(response["data"]["container_path"], "/")
        self.assertEqual(response["data"]["children"][0]["name"], "MyController")
        self.assertEqual(response["data"]["children"][0]["path"], "MyController")
        self.assertTrue(response["data"]["children"][0]["can_browse"])
        self.assertEqual(response["data"]["children"][0]["child_count"], 3)
        self.assertTrue(response["data"]["children"][0]["is_device"])
        self.assertEqual(
            response["data"]["children"][0]["device_identification"],
            {"type": "controller", "id": "Schneider_M310"},
        )
        self.assertEqual(response["meta"]["request_id"], "req-list-001")
        self.assertEqual(
            lister.calls,
            [{"project_path": "D:/Projects/demo.project", "container_path": "/"}],
        )

    def test_list_project_objects_preserves_nested_container_and_paths(self) -> None:
        lister = FakeProjectObjectLister()

        response = list_project_objects(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "MyController/PLCLogic",
            },
            project_object_lister=lister,
            request_id="req-list-002",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["data"]["container_path"], "MyController/PLCLogic")
        self.assertEqual(
            response["data"]["children"],
            [
                {
                    "name": "Application",
                    "path": "MyController/PLCLogic/Application",
                    "is_folder": False,
                    "can_browse": True,
                    "child_count": 6,
                    "is_device": False,
                    "device_identification": None,
                },
                {
                    "name": "PLC_PRG",
                    "path": "MyController/PLCLogic/PLC_PRG",
                    "is_folder": False,
                    "can_browse": False,
                    "child_count": 0,
                    "is_device": False,
                    "device_identification": None,
                    "object_type": "program",
                },
            ],
        )

    def test_list_project_objects_rejects_relative_project_paths(self) -> None:
        response = list_project_objects(
            request={"project_path": "demo.project"},
            project_object_lister=FakeProjectObjectLister(),
            request_id="req-list-003",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "project_path")

    def test_list_project_objects_reports_missing_container(self) -> None:
        response = list_project_objects(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application/POUs",
            },
            project_object_lister=FailingProjectObjectLister(),
            request_id="req-list-004",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "CONTAINER_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
