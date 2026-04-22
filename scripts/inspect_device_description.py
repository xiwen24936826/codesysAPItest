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
    first = devices[0] if len(devices) else None
    payload = {
        "count": len(devices),
        "type_name": type(first).__name__ if first is not None else None,
        "dir": dir(first) if first is not None else [],
    }
except Exception as exc:
    payload = {
        "error": str(exc),
        "traceback": traceback.format_exc(),
    }

with open(OUTPUT_PATH, "w") as handle:
    json.dump(payload, handle)
