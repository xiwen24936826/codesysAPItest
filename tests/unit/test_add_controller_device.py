"""Unit tests for the add_controller_device service module."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.services.projects.add_controller_device import (
    add_controller_device,
)


class FakeControllerDeviceAdder:
    """Simple controller-device adder test double."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def add_controller(
        self,
        project_path: str,
        device_name: str,
        device_type: int | str,
        device_id: str,
        device_version: str,
        module: str | None = None,
    ) -> None:
        self.calls.append(
            {
                "project_path": project_path,
                "device_name": device_name,
                "device_type": device_type,
                "device_id": device_id,
                "device_version": device_version,
                "module": module,
            }
        )


class MissingProjectAdder:
    """Test double that simulates a missing project file."""

    def add_controller(
        self,
        project_path: str,
        device_name: str,
        device_type: int | str,
        device_id: str,
        device_version: str,
        module: str | None = None,
    ) -> None:
        raise FileNotFoundError(project_path)


class MissingDeviceMetadataAdder:
    """Test double that simulates unresolved device metadata."""

    def add_controller(
        self,
        project_path: str,
        device_name: str,
        device_type: int | str,
        device_id: str,
        device_version: str,
        module: str | None = None,
    ) -> None:
        raise LookupError("device metadata not found")


class RaisingControllerDeviceAdder:
    """Test double that simulates unexpected adapter failures."""

    def add_controller(
        self,
        project_path: str,
        device_name: str,
        device_type: int | str,
        device_id: str,
        device_version: str,
        module: str | None = None,
    ) -> None:
        raise RuntimeError("adapter failure")


class AddControllerDeviceTests(unittest.TestCase):
    """Behavioral tests for the add_controller_device MCP service."""

    def test_add_controller_device_returns_success_response(self) -> None:
        adder = FakeControllerDeviceAdder()

        response = add_controller_device(
            request={
                "project_path": "D:/Projects/demo.project",
                "device_name": "Schneider M310 Target",
                "device_type": 4102,
                "device_id": "1044 0006",
                "device_version": "3.5.20.55",
            },
            controller_device_adder=adder,
            request_id="req-301",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["tool"], "add_controller_device")
        self.assertIsNone(response["error"])
        self.assertEqual(response["data"]["project_path"], "D:/Projects/demo.project")
        self.assertEqual(response["data"]["device_name"], "Schneider M310 Target")
        self.assertEqual(response["data"]["device_type"], 4102)
        self.assertEqual(response["data"]["device_id"], "1044 0006")
        self.assertEqual(response["data"]["device_version"], "3.5.20.55")
        self.assertEqual(response["meta"]["request_id"], "req-301")
        self.assertEqual(
            adder.calls,
            [
                {
                    "project_path": "D:/Projects/demo.project",
                    "device_name": "Schneider M310 Target",
                    "device_type": 4102,
                    "device_id": "1044 0006",
                    "device_version": "3.5.20.55",
                    "module": None,
                }
            ],
        )

    def test_add_controller_device_rejects_relative_project_paths(self) -> None:
        adder = FakeControllerDeviceAdder()

        response = add_controller_device(
            request={
                "project_path": "relative/demo.project",
                "device_name": "Controller",
                "device_type": 4102,
                "device_id": "1044 0006",
                "device_version": "3.5.20.55",
            },
            controller_device_adder=adder,
            request_id="req-302",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "project_path")
        self.assertEqual(adder.calls, [])

    def test_add_controller_device_rejects_missing_device_name(self) -> None:
        adder = FakeControllerDeviceAdder()

        response = add_controller_device(
            request={
                "project_path": "D:/Projects/demo.project",
                "device_type": 4102,
                "device_id": "1044 0006",
                "device_version": "3.5.20.55",
            },
            controller_device_adder=adder,
            request_id="req-303",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "device_name")
        self.assertEqual(adder.calls, [])

    def test_add_controller_device_rejects_missing_device_id(self) -> None:
        adder = FakeControllerDeviceAdder()

        response = add_controller_device(
            request={
                "project_path": "D:/Projects/demo.project",
                "device_name": "Controller",
                "device_type": 4102,
                "device_version": "3.5.20.55",
            },
            controller_device_adder=adder,
            request_id="req-304",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "device_id")
        self.assertEqual(adder.calls, [])

    def test_add_controller_device_maps_missing_project_to_project_not_found(self) -> None:
        response = add_controller_device(
            request={
                "project_path": "D:/Projects/missing.project",
                "device_name": "Controller",
                "device_type": 4102,
                "device_id": "1044 0006",
                "device_version": "3.5.20.55",
            },
            controller_device_adder=MissingProjectAdder(),
            request_id="req-305",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "PROJECT_NOT_FOUND")
        self.assertEqual(
            response["error"]["details"]["project_path"],
            "D:/Projects/missing.project",
        )

    def test_add_controller_device_maps_missing_device_metadata(self) -> None:
        response = add_controller_device(
            request={
                "project_path": "D:/Projects/demo.project",
                "device_name": "Controller",
                "device_type": 4102,
                "device_id": "1044 0006",
                "device_version": "3.5.20.55",
            },
            controller_device_adder=MissingDeviceMetadataAdder(),
            request_id="req-306",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "DEVICE_TYPE_NOT_FOUND")
        self.assertEqual(response["error"]["details"]["device_type"], 4102)

    def test_add_controller_device_wraps_unexpected_adapter_errors(self) -> None:
        response = add_controller_device(
            request={
                "project_path": "D:/Projects/demo.project",
                "device_name": "Controller",
                "device_type": 4102,
                "device_id": "1044 0006",
                "device_version": "3.5.20.55",
            },
            controller_device_adder=RaisingControllerDeviceAdder(),
            request_id="req-307",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "DEVICE_INSERT_FAILED")
        self.assertEqual(response["meta"]["request_id"], "req-307")


if __name__ == "__main__":
    unittest.main()

