from __future__ import print_function
import json, os, traceback
import scriptengine
out = os.environ.get('DEVICE_SEARCH_OUTPUT')
search = os.environ.get('DEVICE_SEARCH_TEXT', '')
try:
    devices = scriptengine.device_repository.get_all_devices(search, None)
    first = devices[0]
    info = first.device_info
    payload = {
        'count': len(devices),
        'device_dir': dir(first),
        'device_info_type': type(info).__name__,
        'device_info_dir': dir(info),
        'device_id_type': type(first.device_id).__name__,
        'device_id_dir': dir(first.device_id),
        'device_id_str': str(first.device_id),
    }
except Exception as exc:
    payload = {'error': str(exc), 'traceback': traceback.format_exc()}
with open(out, 'w') as f:
    json.dump(payload, f)
