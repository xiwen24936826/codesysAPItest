"""Bridge script executed by the CODESYS scripting runtime.

This file must stay compatible with the Python runtime embedded in
EcoStruxure Motion Expert / CODESYS scripting.
"""

from __future__ import print_function

import json
import os
import re
import traceback

import scriptengine


REQUEST_ENV = "CODESYS_BRIDGE_REQUEST"
RESPONSE_ENV = "CODESYS_BRIDGE_RESPONSE"


def _load_request():
    request_path = os.environ.get(REQUEST_ENV)
    if not request_path:
        raise RuntimeError("%s is not set" % REQUEST_ENV)

    with open(request_path, "r") as handle:
        return json.load(handle)


def _write_response(payload):
    response_path = os.environ.get(RESPONSE_ENV)
    if not response_path:
        raise RuntimeError("%s is not set" % RESPONSE_ENV)

    with open(response_path, "w") as handle:
        json.dump(payload, handle)


def _no_updates_flag():
    return scriptengine.VersionUpdateFlags.NoUpdates


def _open_project(request):
    return scriptengine.projects.open(
        request["project_path"],
        primary=True,
        update_flags=_no_updates_flag(),
    )


def _get_object_name(obj):
    try:
        return obj.get_name(resolve_localized_display_name=False)
    except TypeError:
        return obj.get_name()


def _find_child(parent, name):
    for child in parent.get_children(False):
        if _get_object_name(child) == name:
            return child
    raise LookupError("Object '%s' could not be found." % name)


def _resolve_container(project, container_path):
    container = project
    if container_path in (None, "", "/"):
        return container
    for part in [item for item in container_path.split("/") if item]:
        container = _find_child(container, part)
    return container


def _resolve_target_object(project, container_path, object_name):
    container = _resolve_container(project, container_path)
    return _find_child(container, object_name)


def _resolve_language(language_name):
    normalized = (language_name or "ST").strip().upper()
    mapping = {
        "ST": scriptengine.ImplementationLanguages.st,
        "IL": scriptengine.ImplementationLanguages.instruction_list,
        "LD": scriptengine.ImplementationLanguages.ladder,
        "FBD": scriptengine.ImplementationLanguages.fbd,
        "CFC": scriptengine.ImplementationLanguages.cfc,
        "SFC": scriptengine.ImplementationLanguages.sfc,
    }
    if normalized not in mapping:
        raise LookupError("Unsupported IEC language: %s" % normalized)
    return mapping[normalized]


def _normalize_interfaces(interfaces):
    if interfaces is None:
        return None
    if isinstance(interfaces, list):
        return ", ".join([item for item in interfaces if item])
    return interfaces


def _get_text_document(target_object, document_kind):
    if document_kind == "declaration":
        if not target_object.has_textual_declaration:
            raise LookupError("Target object has no textual declaration.")
        return target_object.textual_declaration

    if document_kind == "implementation":
        if not target_object.has_textual_implementation:
            raise LookupError("Target object has no textual implementation.")
        return target_object.textual_implementation

    raise LookupError("Unsupported document kind: %s" % document_kind)


def _normalize_newlines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _first_mismatch_index(expected_text, actual_text):
    shared_length = min(len(expected_text), len(actual_text))
    for index in range(shared_length):
        if expected_text[index] != actual_text[index]:
            return index
    return shared_length


def _verify_roundtrip(expected_text, actual_text, verify_mode):
    if expected_text == actual_text:
        return {"ok": True, "mismatch_index": None}
    if verify_mode == "normalize_newlines":
        normalized_expected = _normalize_newlines(expected_text)
        normalized_actual = _normalize_newlines(actual_text)
        if normalized_expected == normalized_actual:
            return {"ok": True, "mismatch_index": None}
        return {
            "ok": False,
            "mismatch_index": _first_mismatch_index(normalized_expected, normalized_actual),
        }
    return {
        "ok": False,
        "mismatch_index": _first_mismatch_index(expected_text, actual_text),
    }


IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
VAR_BLOCK_PATTERN = re.compile(
    r"\bVAR(?:_[A-Z]+)?\b(.*?)\bEND_VAR\b", re.IGNORECASE | re.DOTALL
)
ST_KEYWORDS = {
    "AND",
    "ARRAY",
    "BY",
    "CASE",
    "CONSTANT",
    "DO",
    "ELSE",
    "ELSIF",
    "END_CASE",
    "END_FOR",
    "END_FUNCTION",
    "END_FUNCTION_BLOCK",
    "END_IF",
    "END_METHOD",
    "END_PROGRAM",
    "END_REPEAT",
    "END_VAR",
    "END_WHILE",
    "EXIT",
    "FALSE",
    "FOR",
    "FUNCTION",
    "FUNCTION_BLOCK",
    "IF",
    "MOD",
    "NOT",
    "OF",
    "OR",
    "PROGRAM",
    "REPEAT",
    "RETURN",
    "THEN",
    "TO",
    "TRUE",
    "UNTIL",
    "VAR",
    "VAR_INPUT",
    "VAR_IN_OUT",
    "VAR_OUTPUT",
    "VAR_TEMP",
    "WHILE",
    "XOR",
}
IEC_TYPES = {
    "BOOL",
    "BYTE",
    "DATE",
    "DATE_AND_TIME",
    "DINT",
    "DWORD",
    "INT",
    "LDATE",
    "LDATE_AND_TIME",
    "LINT",
    "LREAL",
    "LTIME",
    "REAL",
    "SINT",
    "STRING",
    "TIME",
    "TIME_OF_DAY",
    "TOD",
    "UDINT",
    "UINT",
    "ULINT",
    "USINT",
    "WORD",
}


def _strip_st_comments(text):
    text = re.sub(r"\(\*.*?\*\)", " ", text, flags=re.DOTALL)
    text = re.sub(r"//.*", " ", text)
    return text


def _collect_declared_identifiers(declaration_text):
    identifiers = set()
    sanitized = _strip_st_comments(declaration_text)
    for match in VAR_BLOCK_PATTERN.finditer(sanitized):
        block = match.group(1)
        for raw_line in block.splitlines():
            line = raw_line.strip()
            if not line or ":" not in line or line.startswith("{"):
                continue
            left = line.split(":", 1)[0]
            left = re.sub(r"\bAT\b.*", "", left, flags=re.IGNORECASE).strip()
            if not left:
                continue
            for item in left.split(","):
                identifier_match = IDENTIFIER_PATTERN.search(item)
                if identifier_match:
                    identifiers.add(identifier_match.group(0))
    return identifiers


def _collect_referenced_identifiers(implementation_text):
    sanitized = _strip_st_comments(implementation_text)
    sanitized = re.sub(r"'(?:''|[^'])*'", " ", sanitized)
    identifiers = set()
    for match in IDENTIFIER_PATTERN.finditer(sanitized):
        identifier = match.group(0)
        normalized = identifier.upper()
        if normalized in ST_KEYWORDS or normalized in IEC_TYPES:
            continue
        if match.start() > 0 and sanitized[match.start() - 1] == ".":
            continue
        trailing = sanitized[match.end() :].lstrip()
        if trailing.startswith("("):
            continue
        identifiers.add(identifier)
    return identifiers


def _find_missing_declarations(declaration_text, implementation_text):
    if not implementation_text.strip():
        return []
    declared_identifiers = _collect_declared_identifiers(declaration_text)
    referenced_identifiers = _collect_referenced_identifiers(implementation_text)
    missing = sorted(
        [identifier for identifier in referenced_identifiers if identifier not in declared_identifiers]
    )
    return missing


def _resolve_container_with_fallback(project, container_path):
    try:
        return _resolve_container(project, container_path), container_path
    except LookupError:
        normalized = (container_path or "").strip()
        if normalized not in ("/", "Application", "/Application"):
            raise
        resolved = _find_container_path_by_name(project, "Application")
        if resolved is None:
            return _resolve_container(project, container_path), container_path
        return _resolve_container(project, resolved), resolved


def _find_container_path_by_name(parent, target_name, max_depth=8):
    queue = [("/", parent, 0)]
    seen = set()
    while queue:
        current_path, current_obj, depth = queue.pop(0)
        if current_path in seen or depth > max_depth:
            continue
        seen.add(current_path)
        try:
            children = list(current_obj.get_children(False))
        except Exception:
            children = []
        for child in children:
            child_name = _get_object_name(child)
            child_path = child_name if current_path in ("", "/") else "%s/%s" % (current_path.strip("/"), child_name)
            if child_name == target_name:
                return child_path
            try:
                list(child.get_children(False))
                can_browse = True
            except Exception:
                can_browse = False
            if can_browse:
                queue.append((child_path, child, depth + 1))
    return None


def _describe_children(parent):
    children = []
    for child in parent.get_children(False):
        try:
            grand_children = child.get_children(False)
            can_browse = True
            child_count = len(list(grand_children))
        except Exception:
            can_browse = False
            child_count = 0
        is_device = bool(getattr(child, "is_device", False))
        device_identification = None
        if is_device and hasattr(child, "get_device_identification"):
            try:
                raw_identification = child.get_device_identification()
                if isinstance(raw_identification, dict):
                    device_identification = raw_identification
                elif raw_identification is not None:
                    device_identification = {"value": str(raw_identification)}
            except Exception:
                device_identification = None
        children.append(
            {
                "name": _get_object_name(child),
                "is_folder": bool(getattr(child, "is_folder", False)),
                "can_browse": can_browse,
                "child_count": child_count,
                "is_device": is_device,
                "device_identification": device_identification,
            }
        )
    return children


def _describe_object(obj, path):
    try:
        grand_children = obj.get_children(False)
        can_browse = True
        child_count = len(list(grand_children))
    except Exception:
        can_browse = False
        child_count = 0
    is_device = bool(getattr(obj, "is_device", False))
    device_identification = None
    if is_device and hasattr(obj, "get_device_identification"):
        try:
            raw_identification = obj.get_device_identification()
            if isinstance(raw_identification, dict):
                device_identification = raw_identification
            elif raw_identification is not None:
                device_identification = {"value": str(raw_identification)}
        except Exception:
            device_identification = None
    return {
        "name": _get_object_name(obj),
        "path": path,
        "is_folder": bool(getattr(obj, "is_folder", False)),
        "can_browse": can_browse,
        "child_count": child_count,
        "is_device": is_device,
        "device_identification": device_identification,
    }


def _find_matching_objects(parent, current_path, target_name, recursive):
    matches = []
    for child in parent.get_children(False):
        child_name = _get_object_name(child)
        child_path = child_name if current_path in ("", "/") else "%s/%s" % (current_path.strip("/"), child_name)
        if child_name == target_name:
            matches.append(_describe_object(child, child_path))
        if recursive:
            try:
                child.get_children(False)
            except Exception:
                continue
            matches.extend(_find_matching_objects(child, child_path, target_name, recursive))
    return matches


def _handle_create(request):
    project = scriptengine.projects.create(
        request["project_path"],
        primary=request.get("primary", True),
    )
    project.save()
    result = {
        "project_path": project.path,
        "is_primary": project.primary,
    }
    project.close()
    return result


def _handle_open(request):
    project = scriptengine.projects.open(
        request["project_path"],
        primary=request.get("primary", True),
        update_flags=_no_updates_flag(),
    )
    result = {
        "project_path": project.path,
        "is_primary": project.primary,
    }
    project.close()
    return result


def _handle_save(request):
    project = _open_project(request)
    project.save()
    result = {
        "project_path": project.path,
        "saved": True,
    }
    project.close()
    return result


def _handle_save_as(request):
    project = _open_project(request)
    project.save_as(request["target_project_path"])
    result = {
        "project_path": request["target_project_path"],
        "saved": True,
    }
    project.close()
    return result


def _handle_add_controller_device(request):
    project = _open_project(request)

    module = request.get("module")
    project.add(
        request["device_name"],
        request["device_type"],
        request["device_id"],
        request["device_version"],
        module,
    )
    project.save()

    result = {
        "project_path": project.path,
        "device_name": request["device_name"],
        "device_type": request["device_type"],
        "device_id": request["device_id"],
        "device_version": request["device_version"],
        "module": module,
        "saved": True,
    }
    project.close()
    return result


def _handle_create_program(request):
    project = _open_project(request)
    container = _resolve_container(project, request["container_path"])
    created_object = container.create_pou(
        name=request["name"],
        type=scriptengine.PouType.Program,
        language=_resolve_language(request.get("language")),
        return_type=None,
        base_type=None,
        interfaces=None,
    )
    project.save()
    result = {
        "project_path": project.path,
        "container_path": request["container_path"],
        "name": _get_object_name(created_object),
        "language": request.get("language", "ST"),
        "object_type": "program",
    }
    project.close()
    return result


def _handle_create_function_block(request):
    project = _open_project(request)
    container = _resolve_container(project, request["container_path"])
    created_object = container.create_pou(
        name=request["name"],
        type=scriptengine.PouType.FunctionBlock,
        language=_resolve_language(request.get("language")),
        return_type=None,
        base_type=request.get("base_type"),
        interfaces=_normalize_interfaces(request.get("interfaces")),
    )
    project.save()
    result = {
        "project_path": project.path,
        "container_path": request["container_path"],
        "name": _get_object_name(created_object),
        "language": request.get("language", "ST"),
        "base_type": request.get("base_type"),
        "interfaces": request.get("interfaces", []),
        "object_type": "function_block",
    }
    project.close()
    return result


def _handle_create_function(request):
    project = _open_project(request)
    container = _resolve_container(project, request["container_path"])
    created_object = container.create_pou(
        name=request["name"],
        type=scriptengine.PouType.Function,
        language=_resolve_language(request.get("language")),
        return_type=request["return_type"],
        base_type=None,
        interfaces=None,
    )
    project.save()
    result = {
        "project_path": project.path,
        "container_path": request["container_path"],
        "name": _get_object_name(created_object),
        "language": request.get("language", "ST"),
        "return_type": request["return_type"],
        "object_type": "function",
    }
    project.close()
    return result


def _handle_read_text_document(request):
    project = _open_project(request)
    target_object = _resolve_target_object(
        project,
        request["container_path"],
        request["object_name"],
    )
    document = _get_text_document(target_object, request["document_kind"])
    result = {
        "project_path": project.path,
        "container_path": request["container_path"],
        "object_name": request["object_name"],
        "document_kind": request["document_kind"],
        "text": document.text,
    }
    project.close()
    return result


def _handle_replace_text_document(request):
    project = _open_project(request)
    target_object = _resolve_target_object(
        project,
        request["container_path"],
        request["object_name"],
    )
    document = _get_text_document(target_object, request["document_kind"])
    document.replace(new_text=request["new_text"])
    project.save()
    result = {
        "project_path": project.path,
        "object_name": request["object_name"],
        "document_kind": request["document_kind"],
        "updated": True,
    }
    project.close()
    return result


def _handle_append_text_document(request):
    project = _open_project(request)
    target_object = _resolve_target_object(
        project,
        request["container_path"],
        request["object_name"],
    )
    document = _get_text_document(target_object, request["document_kind"])
    document.append(request["text_to_append"])
    project.save()
    result = {
        "project_path": project.path,
        "object_name": request["object_name"],
        "document_kind": request["document_kind"],
        "updated": True,
    }
    project.close()
    return result


def _handle_insert_text_document(request):
    project = _open_project(request)
    target_object = _resolve_target_object(
        project,
        request["container_path"],
        request["object_name"],
    )
    document = _get_text_document(target_object, request["document_kind"])
    document.insert(
        text=request["text_to_insert"],
        offset=request["insertion_offset"],
    )
    project.save()
    result = {
        "project_path": project.path,
        "object_name": request["object_name"],
        "document_kind": request["document_kind"],
        "updated": True,
        "insertion_offset": request["insertion_offset"],
    }
    project.close()
    return result


def _handle_replace_text_line(request):
    project = _open_project(request)
    target_object = _resolve_target_object(
        project,
        request["container_path"],
        request["object_name"],
    )
    document = _get_text_document(target_object, request["document_kind"])
    document.replace_line(
        request["line_number"],
        request["new_text"],
    )
    project.save()
    result = {
        "project_path": project.path,
        "object_name": request["object_name"],
        "document_kind": request["document_kind"],
        "updated": True,
        "line_number": request["line_number"],
    }
    project.close()
    return result


def _handle_list_objects(request):
    project = _open_project(request)
    container_path = request.get("container_path", "/")
    container = _resolve_container(project, container_path)
    result = {
        "project_path": project.path,
        "container_path": container_path,
        "children": _describe_children(container),
    }
    project.close()
    return result


def _handle_find_objects(request):
    project = _open_project(request)
    container_path = request.get("container_path", "/")
    container = _resolve_container(project, container_path)
    result = {
        "project_path": project.path,
        "container_path": container_path,
        "matches": _find_matching_objects(
            parent=container,
            current_path=container_path,
            target_name=request["object_name"],
            recursive=request.get("recursive", True),
        ),
    }
    project.close()
    return result


def _normalize_scan_target(target):
    device_id = None
    raw_device_id = getattr(target, "device_id", None)
    if raw_device_id is not None:
        try:
            device_id = str(raw_device_id)
        except Exception:
            device_id = None

    block_driver = getattr(target, "block_driver", None)
    if block_driver is not None:
        try:
            block_driver = str(block_driver)
        except Exception:
            block_driver = None

    return {
        "device_name": getattr(target, "device_name", None),
        "type_name": getattr(target, "type_name", None),
        "vendor_name": getattr(target, "vendor_name", None),
        "device_id": device_id,
        "address": getattr(target, "address", None),
        "parent_address": getattr(target, "parent_address", None),
        "block_driver": block_driver,
        "block_driver_address": getattr(target, "block_driver_address", None),
    }


def _resolve_gateway(request):
    gateways = getattr(scriptengine.online, "gateways", None)
    if gateways is None or len(gateways) == 0:
        raise LookupError("No configured gateways are available.")

    gateway_name = request.get("gateway_name")
    if not gateway_name:
        return gateways[0]

    matches = [gateway for gateway in gateways if getattr(gateway, "name", None) == gateway_name]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise LookupError("Gateway '%s' is ambiguous." % gateway_name)
    raise LookupError("Gateway '%s' could not be found." % gateway_name)


def _handle_scan_network_devices(request):
    gateway = _resolve_gateway(request)
    use_cached_result = request.get("use_cached_result", False)
    if use_cached_result:
        raw_targets = gateway.get_cached_network_scan_result()
    else:
        raw_targets = gateway.perform_network_scan()

    result = {
        "gateway_name": gateway.name,
        "gateway_guid": str(gateway.guid),
        "use_cached_result": use_cached_result,
        "targets": [_normalize_scan_target(target) for target in raw_targets],
    }
    return result


def _handle_generate_pou_transaction(request):
    project = _open_project(request)
    verify_mode = request.get("verify_mode") or "normalize_newlines"
    requested_container_path = request.get("container_path")
    container, resolved_container_path = _resolve_container_with_fallback(project, requested_container_path)

    pou_kind = request.get("pou_kind")
    pou_type_mapping = {
        "program": scriptengine.PouType.Program,
        "function_block": scriptengine.PouType.FunctionBlock,
        "function": scriptengine.PouType.Function,
    }
    if pou_kind not in pou_type_mapping:
        project.close()
        raise LookupError("Unsupported pou_kind: %s" % pou_kind)

    return_type = None
    base_type = None
    interfaces = None
    if pou_kind == "function":
        return_type = request.get("return_type")
    elif pou_kind == "function_block":
        base_type = request.get("base_type")
        interfaces = _normalize_interfaces(request.get("interfaces"))

    created_object = container.create_pou(
        name=request["pou_name"],
        type=pou_type_mapping[pou_kind],
        language=_resolve_language(request.get("language")),
        return_type=return_type,
        base_type=base_type,
        interfaces=interfaces,
    )

    declaration_text = request.get("declaration_text", "")
    implementation_text = request.get("implementation_text", "")

    declaration_document = _get_text_document(created_object, "declaration")
    implementation_document = _get_text_document(created_object, "implementation")

    declaration_document.replace(new_text=declaration_text)
    implementation_document.replace(new_text=implementation_text)

    roundtrip_declaration = declaration_document.text
    roundtrip_implementation = implementation_document.text

    declaration_verification = _verify_roundtrip(
        declaration_text, roundtrip_declaration, verify_mode
    )
    implementation_verification = _verify_roundtrip(
        implementation_text, roundtrip_implementation, verify_mode
    )
    missing_identifiers = _find_missing_declarations(
        roundtrip_declaration, roundtrip_implementation
    )
    consistency_ok = len(missing_identifiers) == 0

    verification_ok = (
        declaration_verification["ok"]
        and implementation_verification["ok"]
        and consistency_ok
    )

    saved = False
    if verification_ok:
        project.save()
        saved = True

    result = {
        "project_path": project.path,
        "requested_container_path": requested_container_path,
        "resolved_container_path": resolved_container_path,
        "pou_name": _get_object_name(created_object),
        "pou_kind": pou_kind,
        "language": request.get("language", "ST"),
        "created": True,
        "written": {"declaration": True, "implementation": True},
        "verification": {
            "mode": verify_mode,
            "ok": verification_ok,
            "declaration_roundtrip_verified": declaration_verification["ok"],
            "implementation_roundtrip_verified": implementation_verification["ok"],
            "declaration_mismatch_index": declaration_verification["mismatch_index"],
            "implementation_mismatch_index": implementation_verification["mismatch_index"],
            "consistency_ok": consistency_ok,
            "missing_identifiers": missing_identifiers,
        },
        "saved": saved,
        "closed": True,
        "location": {
            "container_path": resolved_container_path,
            "object_name": _get_object_name(created_object),
        },
    }
    project.close()
    return result


def _apply_text_operations(current_text, operations):
    expected = current_text
    for operation in operations:
        op = operation.get("op")
        if op == "replace":
            expected = operation.get("new_text", "")
            continue
        if op == "append":
            expected = expected + operation.get("text", "")
            continue
        if op == "insert":
            text = operation.get("text", "")
            offset = int(operation.get("offset", 0))
            expected = expected[:offset] + text + expected[offset:]
            continue
        if op == "replace_line":
            line_number = int(operation.get("line_number", 0))
            new_text = operation.get("new_text", "")
            lines = expected.splitlines(True)
            if line_number < 1 or line_number > len(lines):
                raise ValueError("line_number is outside the document line range.")
            target_index = line_number - 1
            original_line = lines[target_index]
            line_ending = ""
            if original_line.endswith("\r\n"):
                line_ending = "\r\n"
            elif original_line.endswith("\n") or original_line.endswith("\r"):
                line_ending = original_line[-1]
            lines[target_index] = new_text + line_ending
            expected = "".join(lines)
            continue
        raise LookupError("Unsupported operation: %s" % op)
    return expected


def _handle_edit_pou_transaction(request):
    project = _open_project(request)
    verify_mode = request.get("verify_mode") or "normalize_newlines"
    requested_container_path = request.get("container_path")
    container, resolved_container_path = _resolve_container_with_fallback(project, requested_container_path)
    target_object = _find_child(container, request["pou_name"])

    operations = request.get("operations") or []
    operations_by_kind = {"declaration": [], "implementation": []}
    for operation in operations:
        operations_by_kind.get(operation.get("document_kind"), []).append(operation)

    declaration_document = _get_text_document(target_object, "declaration")
    implementation_document = _get_text_document(target_object, "implementation")
    before_declaration = declaration_document.text
    before_implementation = implementation_document.text

    expected_declaration = _apply_text_operations(
        before_declaration, operations_by_kind["declaration"]
    )
    expected_implementation = _apply_text_operations(
        before_implementation, operations_by_kind["implementation"]
    )

    for operation in operations_by_kind["declaration"]:
        op = operation.get("op")
        if op == "replace":
            declaration_document.replace(new_text=operation.get("new_text", ""))
        elif op == "append":
            declaration_document.append(operation.get("text", ""))
        elif op == "insert":
            declaration_document.insert(text=operation.get("text", ""), offset=int(operation.get("offset", 0)))
        elif op == "replace_line":
            declaration_document.replace_line(int(operation.get("line_number", 0)), operation.get("new_text", ""))
        else:
            project.close()
            raise LookupError("Unsupported operation: %s" % op)

    for operation in operations_by_kind["implementation"]:
        op = operation.get("op")
        if op == "replace":
            implementation_document.replace(new_text=operation.get("new_text", ""))
        elif op == "append":
            implementation_document.append(operation.get("text", ""))
        elif op == "insert":
            implementation_document.insert(text=operation.get("text", ""), offset=int(operation.get("offset", 0)))
        elif op == "replace_line":
            implementation_document.replace_line(int(operation.get("line_number", 0)), operation.get("new_text", ""))
        else:
            project.close()
            raise LookupError("Unsupported operation: %s" % op)

    roundtrip_declaration = declaration_document.text
    roundtrip_implementation = implementation_document.text

    declaration_verification = _verify_roundtrip(
        expected_declaration, roundtrip_declaration, verify_mode
    )
    implementation_verification = _verify_roundtrip(
        expected_implementation, roundtrip_implementation, verify_mode
    )
    missing_identifiers = _find_missing_declarations(
        roundtrip_declaration, roundtrip_implementation
    )
    consistency_ok = len(missing_identifiers) == 0

    verification_ok = (
        declaration_verification["ok"]
        and implementation_verification["ok"]
        and consistency_ok
    )

    saved = False
    if verification_ok:
        project.save()
        saved = True

    result = {
        "project_path": project.path,
        "requested_container_path": requested_container_path,
        "resolved_container_path": resolved_container_path,
        "pou_name": request["pou_name"],
        "operations_applied": operations,
        "verification": {
            "mode": verify_mode,
            "ok": verification_ok,
            "declaration_roundtrip_verified": declaration_verification["ok"],
            "implementation_roundtrip_verified": implementation_verification["ok"],
            "declaration_mismatch_index": declaration_verification["mismatch_index"],
            "implementation_mismatch_index": implementation_verification["mismatch_index"],
            "consistency_ok": consistency_ok,
            "missing_identifiers": missing_identifiers,
        },
        "saved": saved,
        "closed": True,
        "before": {
            "declaration_length": len(before_declaration),
            "implementation_length": len(before_implementation),
        },
        "after": {
            "declaration_length": len(roundtrip_declaration),
            "implementation_length": len(roundtrip_implementation),
        },
        "location": {
            "container_path": resolved_container_path,
            "object_name": request["pou_name"],
        },
    }
    project.close()
    return result


def main():
    request = _load_request()
    operation = request.get("operation")

    handlers = {
        "create": _handle_create,
        "open": _handle_open,
        "save": _handle_save,
        "save_as": _handle_save_as,
        "add_controller_device": _handle_add_controller_device,
        "create_program": _handle_create_program,
        "create_function_block": _handle_create_function_block,
        "create_function": _handle_create_function,
        "read_text_document": _handle_read_text_document,
        "replace_text_document": _handle_replace_text_document,
        "append_text_document": _handle_append_text_document,
        "insert_text_document": _handle_insert_text_document,
        "replace_text_line": _handle_replace_text_line,
        "list_objects": _handle_list_objects,
        "find_objects": _handle_find_objects,
        "scan_network_devices": _handle_scan_network_devices,
        "generate_pou_transaction": _handle_generate_pou_transaction,
        "edit_pou_transaction": _handle_edit_pou_transaction,
    }

    if operation not in handlers:
        raise RuntimeError("Unsupported operation: %s" % operation)

    data = handlers[operation](request)
    _write_response({"ok": True, "data": data})


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        _write_response(
            {
                "ok": False,
                "error": {
                    "message": str(exc),
                    "traceback": traceback.format_exc(),
                },
            }
        )
        raise
