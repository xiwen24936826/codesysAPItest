"""Unit tests for the create_function_block service module."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.services.pous.create_function_block import create_function_block


class FakeFunctionBlockCreator:
    """Simple function block creator test double."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create_function_block(
        self,
        project_path: str,
        container_path: str,
        name: str,
        language: str = "ST",
        base_type: str | None = None,
        interfaces: list[str] | None = None,
    ) -> None:
        self.calls.append(
            {
                "project_path": project_path,
                "container_path": container_path,
                "name": name,
                "language": language,
                "base_type": base_type,
                "interfaces": interfaces,
            }
        )

    def list_objects(
        self,
        project_path: str,
        container_path: str = "/",
    ) -> dict[str, object]:
        if container_path == "/":
            return {"children": [{"name": "MyController", "is_folder": True}]}
        if container_path == "MyController":
            return {"children": [{"name": "PLC逻辑", "is_folder": True}]}
        if container_path == "MyController/PLC逻辑":
            return {"children": [{"name": "Application", "is_folder": True}]}
        return {"children": []}


class CreateFunctionBlockTests(unittest.TestCase):
    """Behavioral tests for the create_function_block MCP service."""

    def test_create_function_block_returns_success_response(self) -> None:
        creator = FakeFunctionBlockCreator()

        response = create_function_block(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "name": "MotorControl",
                "language": "st",
                "base_type": "BaseMotor",
                "interfaces": ["IMotor", "IStartable"],
            },
            function_block_creator=creator,
            request_id="req-fb-001",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["data"]["object_type"], "function_block")
        self.assertEqual(response["data"]["interfaces"], ["IMotor", "IStartable"])
        self.assertEqual(
            creator.calls,
            [
                {
                    "project_path": "D:/Projects/demo.project",
                    "container_path": "MyController/PLC逻辑/Application",
                    "name": "MotorControl",
                    "language": "ST",
                    "base_type": "BaseMotor",
                    "interfaces": ["IMotor", "IStartable"],
                }
            ],
        )

    def test_create_function_block_rejects_invalid_interfaces(self) -> None:
        creator = FakeFunctionBlockCreator()

        response = create_function_block(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "name": "MotorControl",
                "interfaces": "IMotor",
            },
            function_block_creator=creator,
            request_id="req-fb-002",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "interfaces")
        self.assertEqual(creator.calls, [])

    def test_create_function_block_auto_resolves_nested_application(self) -> None:
        creator = FakeFunctionBlockCreator()

        response = create_function_block(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "/",
                "name": "MotorControl",
            },
            function_block_creator=creator,
            request_id="req-fb-003",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(
            response["data"]["container_path"],
            "MyController/PLC逻辑/Application",
        )
        self.assertEqual(
            creator.calls[0]["container_path"],
            "MyController/PLC逻辑/Application",
        )


if __name__ == "__main__":
    unittest.main()
