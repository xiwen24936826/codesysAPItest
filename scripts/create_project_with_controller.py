from __future__ import print_function

import json
import os
import traceback

import scriptengine


REQUEST_PATH = os.environ.get("PROJECT_CREATE_REQUEST")
RESPONSE_PATH = os.environ.get("PROJECT_CREATE_RESPONSE")

if not REQUEST_PATH or not RESPONSE_PATH:
    raise SystemExit("PROJECT_CREATE_REQUEST and PROJECT_CREATE_RESPONSE must be set")


def main():
    with open(REQUEST_PATH, "r") as handle:
        request = json.load(handle)

    project = scriptengine.projects.create(
        request["project_path"],
        primary=True,
    )

    device = project.add(
        request["device_name"],
        request["device_type"],
        request["device_id"],
        request["device_version"],
    )

    project.save()

    children = []
    try:
        for child in project.get_children():
            children.append(str(child))
    except Exception:
        pass

    device_name = request["device_name"]
    try:
        device_name = device.get_name(False)
    except Exception:
        pass

    response = {
        "ok": True,
        "data": {
            "project_path": project.path,
            "device_name": device_name,
            "device_type": request["device_type"],
            "device_id": request["device_id"],
            "device_version": request["device_version"],
            "project_children": children,
        },
    }

    project.close()

    _write_json(response)


def _write_json(payload):
    with open(RESPONSE_PATH, "w") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        _write_json(
            {
                "ok": False,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
        raise
