from __future__ import print_function

import json
import os
import sys

import scriptengine


output_path = os.environ.get("CODESYS_SMOKE_OUTPUT")

payload = {
    "argv": sys.argv,
    "projects_type": type(scriptengine.projects).__name__,
    "primary_exists": scriptengine.projects.primary is not None,
}

if not output_path:
    raise SystemExit("CODESYS_SMOKE_OUTPUT is not set")

with open(output_path, "w") as handle:
    json.dump(payload, handle)

print("Smoke test finished")
