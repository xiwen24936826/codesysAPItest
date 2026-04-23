"""Bridge script executed by the CODESYS scripting runtime.

This file must stay compatible with the Python runtime embedded in
EcoStruxure Motion Expert / CODESYS scripting.
"""

from __future__ import print_function

import json
import os
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
        children.append(
            {
                "name": _get_object_name(child),
                "is_folder": bool(getattr(child, "is_folder", False)),
                "can_browse": can_browse,
                "child_count": child_count,
            }
        )
    return children


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
        "list_objects": _handle_list_objects,
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
