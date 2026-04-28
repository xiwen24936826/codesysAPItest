"""In-memory backend for offline server and SDK verification."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class InMemoryPou:
    """One in-memory IEC object."""

    name: str
    object_type: str
    language: str = "ST"
    declaration: str = ""
    implementation: str = ""
    return_type: str | None = None
    base_type: str | None = None
    interfaces: list[str] = field(default_factory=list)


@dataclass
class InMemoryProject:
    """One in-memory project state."""

    path: str
    primary: bool = True
    root_objects: dict[str, dict[str, InMemoryPou]] = field(
        default_factory=lambda: {"Application": {}}
    )


class InMemoryCodesysBackend:
    """Backend that simulates the phase-1 tool surface in memory."""

    def __init__(self) -> None:
        self._projects: dict[str, InMemoryProject] = {}

    def create(self, path: str, primary: bool = True) -> dict[str, object]:
        self._projects[path] = InMemoryProject(path=path, primary=primary)
        return {"project_path": path, "is_primary": primary}

    def open(self, path: str) -> dict[str, object]:
        self._require_project(path)
        return {"project_path": path, "is_primary": self._projects[path].primary}

    def save(self, path: str) -> dict[str, object]:
        self._require_project(path)
        return {"project_path": path, "saved": True}

    def save_as(self, path: str, target_path: str) -> dict[str, object]:
        project = deepcopy(self._require_project(path))
        project.path = target_path
        self._projects[target_path] = project
        return {"project_path": target_path, "saved": True}

    def add_controller(
        self,
        project_path: str,
        device_name: str,
        device_type: int | str,
        device_id: str,
        device_version: str,
        module: str | None = None,
    ) -> dict[str, object]:
        project = self._require_project(project_path)
        project.root_objects.setdefault(device_name, {})
        return {
            "project_path": project_path,
            "device_name": device_name,
            "device_type": device_type,
            "device_id": device_id,
            "device_version": device_version,
            "module": module,
        }

    def create_program(
        self,
        project_path: str,
        container_path: str,
        name: str,
        language: str = "ST",
    ) -> dict[str, object]:
        container = self._require_container(project_path, container_path)
        self._ensure_missing(container, name)
        container[name] = InMemoryPou(
            name=name,
            object_type="program",
            language=language,
            declaration="PROGRAM %s\nVAR\nEND_VAR" % name,
            implementation="",
        )
        return {"name": name}

    def create_function_block(
        self,
        project_path: str,
        container_path: str,
        name: str,
        language: str = "ST",
        base_type: str | None = None,
        interfaces: list[str] | None = None,
    ) -> dict[str, object]:
        container = self._require_container(project_path, container_path)
        self._ensure_missing(container, name)
        container[name] = InMemoryPou(
            name=name,
            object_type="function_block",
            language=language,
            declaration="FUNCTION_BLOCK %s\nVAR\nEND_VAR" % name,
            implementation="",
            base_type=base_type,
            interfaces=interfaces or [],
        )
        return {"name": name}

    def create_function(
        self,
        project_path: str,
        container_path: str,
        name: str,
        return_type: str,
        language: str = "ST",
    ) -> dict[str, object]:
        container = self._require_container(project_path, container_path)
        self._ensure_missing(container, name)
        container[name] = InMemoryPou(
            name=name,
            object_type="function",
            language=language,
            declaration="FUNCTION %s : %s\nVAR\nEND_VAR" % (name, return_type),
            implementation="",
            return_type=return_type,
        )
        return {"name": name}

    def read_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
    ) -> dict[str, str]:
        pou = self._require_object(project_path, container_path, object_name)
        if document_kind == "declaration":
            return {"text": pou.declaration}
        if document_kind == "implementation":
            return {"text": pou.implementation}
        raise LookupError("Unsupported document kind: %s" % document_kind)

    def replace_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        new_text: str,
    ) -> None:
        pou = self._require_object(project_path, container_path, object_name)
        if document_kind == "declaration":
            pou.declaration = new_text
            return
        if document_kind == "implementation":
            pou.implementation = new_text
            return
        raise LookupError("Unsupported document kind: %s" % document_kind)

    def append_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        text_to_append: str,
    ) -> None:
        pou = self._require_object(project_path, container_path, object_name)
        if document_kind == "declaration":
            pou.declaration += text_to_append
            return
        if document_kind == "implementation":
            pou.implementation += text_to_append
            return
        raise LookupError("Unsupported document kind: %s" % document_kind)

    def insert_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        text_to_insert: str,
        insertion_offset: int,
    ) -> None:
        pou = self._require_object(project_path, container_path, object_name)
        if document_kind == "declaration":
            target = pou.declaration
            pou.declaration = target[:insertion_offset] + text_to_insert + target[insertion_offset:]
            return
        if document_kind == "implementation":
            target = pou.implementation
            pou.implementation = target[:insertion_offset] + text_to_insert + target[insertion_offset:]
            return
        raise LookupError("Unsupported document kind: %s" % document_kind)

    def replace_text_line(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        line_number: int,
        new_text: str,
    ) -> None:
        pou = self._require_object(project_path, container_path, object_name)
        if document_kind == "declaration":
            pou.declaration = self._replace_line(pou.declaration, line_number, new_text)
            return
        if document_kind == "implementation":
            pou.implementation = self._replace_line(pou.implementation, line_number, new_text)
            return
        raise LookupError("Unsupported document kind: %s" % document_kind)

    def generate_pou_transaction(
        self,
        project_path: str,
        container_path: str,
        pou_name: str,
        pou_kind: str,
        declaration_text: str,
        implementation_text: str,
        language: str | None = None,
        return_type: str | None = None,
        base_type: str | None = None,
        interfaces: list[str] | None = None,
        write_strategy: str | None = None,
        verify_mode: str | None = None,
    ) -> dict[str, object]:
        if pou_kind == "program":
            self.create_program(
                project_path=project_path,
                container_path=container_path,
                name=pou_name,
                language=language or "ST",
            )
        elif pou_kind == "function_block":
            self.create_function_block(
                project_path=project_path,
                container_path=container_path,
                name=pou_name,
                language=language or "ST",
                base_type=base_type,
                interfaces=interfaces,
            )
        elif pou_kind == "function":
            if not return_type:
                raise ValueError("return_type is required for function POUs.")
            self.create_function(
                project_path=project_path,
                container_path=container_path,
                name=pou_name,
                return_type=return_type,
                language=language or "ST",
            )
        else:
            raise LookupError("Unsupported pou_kind: %s" % pou_kind)

        self.replace_text_document(
            project_path=project_path,
            container_path=container_path,
            object_name=pou_name,
            document_kind="declaration",
            new_text=declaration_text,
        )
        self.replace_text_document(
            project_path=project_path,
            container_path=container_path,
            object_name=pou_name,
            document_kind="implementation",
            new_text=implementation_text,
        )

        actual_declaration = self.read_text_document(
            project_path=project_path,
            container_path=container_path,
            object_name=pou_name,
            document_kind="declaration",
        )["text"]
        actual_implementation = self.read_text_document(
            project_path=project_path,
            container_path=container_path,
            object_name=pou_name,
            document_kind="implementation",
        )["text"]

        verification = _verify_roundtrip_pair(
            expected_declaration=declaration_text,
            actual_declaration=actual_declaration,
            expected_implementation=implementation_text,
            actual_implementation=actual_implementation,
            verify_mode=verify_mode or "normalize_newlines",
        )
        return {
            "project_path": project_path,
            "requested_container_path": container_path,
            "resolved_container_path": container_path,
            "pou_name": pou_name,
            "pou_kind": pou_kind,
            "language": language or "ST",
            "created": True,
            "written": {"declaration": True, "implementation": True},
            "verification": verification,
            "saved": verification.get("ok", False),
            "closed": True,
            "location": {"container_path": container_path, "object_name": pou_name},
        }

    def edit_pou_transaction(
        self,
        project_path: str,
        container_path: str,
        pou_name: str,
        operations: list[dict[str, Any]],
        verify_mode: str | None = None,
    ) -> dict[str, object]:
        before_declaration = self.read_text_document(
            project_path=project_path,
            container_path=container_path,
            object_name=pou_name,
            document_kind="declaration",
        )["text"]
        before_implementation = self.read_text_document(
            project_path=project_path,
            container_path=container_path,
            object_name=pou_name,
            document_kind="implementation",
        )["text"]

        declaration_ops = [op for op in operations if op.get("document_kind") == "declaration"]
        implementation_ops = [op for op in operations if op.get("document_kind") == "implementation"]

        expected_declaration = _apply_text_operations(before_declaration, declaration_ops)
        expected_implementation = _apply_text_operations(before_implementation, implementation_ops)

        for operation in declaration_ops:
            _apply_backend_operation(
                backend=self,
                project_path=project_path,
                container_path=container_path,
                pou_name=pou_name,
                document_kind="declaration",
                operation=operation,
            )
        for operation in implementation_ops:
            _apply_backend_operation(
                backend=self,
                project_path=project_path,
                container_path=container_path,
                pou_name=pou_name,
                document_kind="implementation",
                operation=operation,
            )

        after_declaration = self.read_text_document(
            project_path=project_path,
            container_path=container_path,
            object_name=pou_name,
            document_kind="declaration",
        )["text"]
        after_implementation = self.read_text_document(
            project_path=project_path,
            container_path=container_path,
            object_name=pou_name,
            document_kind="implementation",
        )["text"]

        verification = _verify_roundtrip_pair(
            expected_declaration=expected_declaration,
            actual_declaration=after_declaration,
            expected_implementation=expected_implementation,
            actual_implementation=after_implementation,
            verify_mode=verify_mode or "normalize_newlines",
        )
        return {
            "project_path": project_path,
            "requested_container_path": container_path,
            "resolved_container_path": container_path,
            "pou_name": pou_name,
            "operations_applied": operations,
            "verification": verification,
            "saved": verification.get("ok", False),
            "closed": True,
            "before": {
                "declaration_length": len(before_declaration),
                "implementation_length": len(before_implementation),
            },
            "after": {
                "declaration_length": len(after_declaration),
                "implementation_length": len(after_implementation),
            },
            "location": {"container_path": container_path, "object_name": pou_name},
        }

    def list_objects(
        self,
        project_path: str,
        container_path: str = "/",
    ) -> dict[str, object]:
        project = self._require_project(project_path)
        normalized = container_path.strip("/")

        if not normalized:
            return {
                "project_path": project_path,
                "container_path": "/",
                "children": [
                    {
                        "name": name,
                        "is_folder": True,
                        "can_browse": True,
                        "child_count": len(project.root_objects[name]),
                        "is_device": False,
                        "device_identification": None,
                    }
                    for name in project.root_objects.keys()
                ],
            }

        if normalized in project.root_objects:
            return {
                "project_path": project_path,
                "container_path": normalized,
                "children": [
                    {
                        "name": name,
                        "is_folder": False,
                        "can_browse": False,
                        "child_count": 0,
                        "is_device": False,
                        "device_identification": None,
                    }
                    for name in project.root_objects[normalized].keys()
                ],
            }

        raise LookupError("Container '%s' was not found." % container_path)

    def find_objects(
        self,
        project_path: str,
        object_name: str,
        container_path: str = "/",
        recursive: bool = True,
    ) -> dict[str, object]:
        listing = self.list_objects(project_path=project_path, container_path=container_path)
        normalized_root = container_path.strip("/")
        matches = []

        for child in listing["children"]:
            if child["name"] == object_name:
                path = child.get("path") or (
                    child["name"] if not normalized_root else "%s/%s" % (normalized_root, child["name"])
                )
                matches.append(
                    {
                        "name": child["name"],
                        "path": path,
                        "is_folder": child.get("is_folder", False),
                        "can_browse": child.get("can_browse", False),
                        "child_count": child.get("child_count", 0),
                        "is_device": child.get("is_device", False),
                        "device_identification": child.get("device_identification"),
                    }
                )

        if recursive:
            project = self._require_project(project_path)
            for root_name, root_objects in project.root_objects.items():
                if normalized_root not in ("", root_name):
                    continue
                for pou_name, pou in root_objects.items():
                    if pou_name != object_name:
                        continue
                    matches.append(
                        {
                            "name": pou_name,
                            "path": "%s/%s" % (root_name, pou_name),
                            "is_folder": False,
                            "can_browse": False,
                            "child_count": 0,
                            "is_device": False,
                            "device_identification": None,
                            "object_type": pou.object_type,
                        }
                    )

        return {
            "project_path": project_path,
            "container_path": container_path,
            "matches": matches,
        }

    def scan_network_devices(
        self,
        gateway_name: str | None = None,
        use_cached_result: bool = False,
    ) -> dict[str, object]:
        return {
            "gateway_name": gateway_name or "InMemory Gateway",
            "gateway_guid": "00000000-0000-0000-0000-000000000001",
            "use_cached_result": use_cached_result,
            "targets": [
                {
                    "device_name": "Simulated PLC",
                    "type_name": "Virtual Controller",
                    "vendor_name": "OpenAI Test Vendor",
                    "device_id": "SIM-PLC-001",
                    "address": "1.1.1",
                    "parent_address": None,
                    "block_driver": "Gateway",
                    "block_driver_address": "127.0.0.1",
                }
            ],
        }

    def _require_project(self, path: str) -> InMemoryProject:
        try:
            return self._projects[path]
        except KeyError as exc:
            raise FileNotFoundError(path) from exc

    def _require_container(
        self,
        project_path: str,
        container_path: str,
    ) -> dict[str, InMemoryPou]:
        project = self._require_project(project_path)
        normalized = container_path.strip("/")
        if not normalized:
            raise LookupError("Root container is not writable for POU objects.")
        try:
            return project.root_objects[normalized]
        except KeyError as exc:
            raise LookupError("Container '%s' was not found." % container_path) from exc

    def _require_object(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
    ) -> InMemoryPou:
        container = self._require_container(project_path, container_path)
        try:
            return container[object_name]
        except KeyError as exc:
            raise LookupError("Object '%s' was not found." % object_name) from exc

    @staticmethod
    def _ensure_missing(container: dict[str, InMemoryPou], name: str) -> None:
        if name in container:
            raise LookupError("Object '%s' already exists." % name)

    @staticmethod
    def _replace_line(current_text: str, line_number: int, new_text: str) -> str:
        lines = current_text.splitlines(True)
        if line_number < 1 or line_number > len(lines):
            raise LookupError("Line %s is outside the document range." % line_number)

        target_index = line_number - 1
        original_line = lines[target_index]
        line_ending = ""
        if original_line.endswith("\r\n"):
            line_ending = "\r\n"
        elif original_line.endswith("\n") or original_line.endswith("\r"):
            line_ending = original_line[-1]

        lines[target_index] = new_text + line_ending
        return "".join(lines)


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _first_mismatch_index(expected_text: str, actual_text: str) -> int:
    shared_length = min(len(expected_text), len(actual_text))
    for index in range(shared_length):
        if expected_text[index] != actual_text[index]:
            return index
    return shared_length


def _verify_roundtrip(expected_text: str, actual_text: str, verify_mode: str) -> dict[str, object]:
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
    return {"ok": False, "mismatch_index": _first_mismatch_index(expected_text, actual_text)}


def _verify_roundtrip_pair(
    *,
    expected_declaration: str,
    actual_declaration: str,
    expected_implementation: str,
    actual_implementation: str,
    verify_mode: str,
) -> dict[str, object]:
    declaration = _verify_roundtrip(expected_declaration, actual_declaration, verify_mode)
    implementation = _verify_roundtrip(expected_implementation, actual_implementation, verify_mode)
    ok = bool(declaration["ok"]) and bool(implementation["ok"])
    return {
        "mode": verify_mode,
        "ok": ok,
        "declaration_roundtrip_verified": bool(declaration["ok"]),
        "implementation_roundtrip_verified": bool(implementation["ok"]),
        "declaration_mismatch_index": declaration["mismatch_index"],
        "implementation_mismatch_index": implementation["mismatch_index"],
        "consistency_ok": True,
        "missing_identifiers": [],
    }


def _apply_text_operations(current_text: str, operations: list[dict[str, Any]]) -> str:
    expected = current_text
    for operation in operations:
        op = operation.get("op")
        if op == "replace":
            expected = str(operation.get("new_text", ""))
            continue
        if op == "append":
            expected = expected + str(operation.get("text", ""))
            continue
        if op == "insert":
            text = str(operation.get("text", ""))
            offset = int(operation.get("offset", 0))
            expected = expected[:offset] + text + expected[offset:]
            continue
        if op == "replace_line":
            line_number = int(operation.get("line_number", 0))
            new_text = str(operation.get("new_text", ""))
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


def _apply_backend_operation(
    *,
    backend: InMemoryCodesysBackend,
    project_path: str,
    container_path: str,
    pou_name: str,
    document_kind: str,
    operation: dict[str, Any],
) -> None:
    op = operation.get("op")
    if op == "replace":
        backend.replace_text_document(
            project_path=project_path,
            container_path=container_path,
            object_name=pou_name,
            document_kind=document_kind,
            new_text=str(operation.get("new_text", "")),
        )
        return
    if op == "append":
        backend.append_text_document(
            project_path=project_path,
            container_path=container_path,
            object_name=pou_name,
            document_kind=document_kind,
            text_to_append=str(operation.get("text", "")),
        )
        return
    if op == "insert":
        backend.insert_text_document(
            project_path=project_path,
            container_path=container_path,
            object_name=pou_name,
            document_kind=document_kind,
            text_to_insert=str(operation.get("text", "")),
            insertion_offset=int(operation.get("offset", 0)),
        )
        return
    if op == "replace_line":
        backend.replace_text_line(
            project_path=project_path,
            container_path=container_path,
            object_name=pou_name,
            document_kind=document_kind,
            line_number=int(operation.get("line_number", 0)),
            new_text=str(operation.get("new_text", "")),
        )
        return
    raise LookupError("Unsupported operation: %s" % op)
