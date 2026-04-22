from __future__ import print_function

import json
import os
import traceback

import scriptengine


SEARCH_TEXT = os.environ.get("DEVICE_SEARCH_TEXT", "")
OUTPUT_PATH = os.environ.get("DEVICE_SEARCH_OUTPUT")

if not OUTPUT_PATH:
    raise SystemExit("DEVICE_SEARCH_OUTPUT is not set")

try:
    devices = scriptengine.device_repository.get_all_devices(SEARCH_TEXT, None)
    payload = []

    for device in devices:
        entry = {
            "name": device.device_info.name,
            "vendor": device.device_info.vendor,
            "default_instance_name": device.device_info.default_instance_name,
            "order_number": device.device_info.order_number,
            "description": device.device_info.description,
            "type": device.device_id.type,
            "id": device.device_id.id,
            "version": device.device_id.version,
        }
        payload.append(entry)

    result = {"ok": True, "devices": payload}
except Exception as exc:
    result = {
        "ok": False,
        "error": str(exc),
        "traceback": traceback.format_exc(),
    }

with open(OUTPUT_PATH, "w") as handle:
    json.dump(result, handle)
