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
                    {"name": name, "is_folder": True}
                    for name in project.root_objects.keys()
                ],
            }

        if normalized in project.root_objects:
            return {
                "project_path": project_path,
                "container_path": normalized,
                "children": [
                    {"name": name, "is_folder": False}
                    for name in project.root_objects[normalized].keys()
                ],
            }

        raise LookupError("Container '%s' was not found." % container_path)

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
