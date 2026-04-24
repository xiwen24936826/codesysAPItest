"""Unit tests for the scan_network_devices service module."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.services.online.scan_network_devices import scan_network_devices


class FakeNetworkDeviceScanner:
    """Simple online-scan test double."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def scan_network_devices(
        self,
        gateway_name: str | None = None,
        use_cached_result: bool = False,
    ) -> dict[str, object]:
        self.calls.append(
            {
                "gateway_name": gateway_name,
                "use_cached_result": use_cached_result,
            }
        )
        return {
            "gateway_name": gateway_name or "Local Gateway",
            "gateway_guid": "guid-1",
            "use_cached_result": use_cached_result,
            "targets": [
                {
                    "device_name": "PLC_A",
                    "type_name": "M310",
                    "vendor_name": "Schneider",
                    "device_id": "dev-1",
                    "address": "1.2.3",
                    "parent_address": "1.2",
                    "block_driver": "Gateway",
                    "block_driver_address": "127.0.0.1",
                }
            ],
        }


class MissingGatewayScanner:
    def scan_network_devices(
        self,
        gateway_name: str | None = None,
        use_cached_result: bool = False,
    ) -> dict[str, object]:
        raise LookupError("Gateway not found")


class ScanNetworkDevicesTests(unittest.TestCase):
    def test_scan_network_devices_returns_targets(self) -> None:
        scanner = FakeNetworkDeviceScanner()

        response = scan_network_devices(
            request={"gateway_name": "Local Gateway", "use_cached_result": True},
            network_device_scanner=scanner,
            request_id="req-scan-001",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["data"]["gateway_name"], "Local Gateway")
        self.assertTrue(response["data"]["use_cached_result"])
        self.assertEqual(response["data"]["targets"][0]["device_name"], "PLC_A")
        self.assertEqual(scanner.calls[0]["gateway_name"], "Local Gateway")

    def test_scan_network_devices_rejects_non_boolean_use_cached_result(self) -> None:
        response = scan_network_devices(
            request={"use_cached_result": "yes"},
            network_device_scanner=FakeNetworkDeviceScanner(),
            request_id="req-scan-002",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "use_cached_result")

    def test_scan_network_devices_reports_missing_gateway(self) -> None:
        response = scan_network_devices(
            request={"gateway_name": "Missing"},
            network_device_scanner=MissingGatewayScanner(),
            request_id="req-scan-003",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "GATEWAY_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
