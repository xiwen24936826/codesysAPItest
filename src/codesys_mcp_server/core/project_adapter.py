"""Real CODESYS IDE-backed project adapter."""

from __future__ import annotations

from dataclasses import dataclass
import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any
import winreg


PRODUCT_NAME = "EcoStruxure Motion Expert SP20"
DEFAULT_EXECUTABLE_RELATIVE_PATH = Path(
    "EcoStruxure Motion Expert",
    "Common",
    "CODESYS.exe",
)
BRIDGE_REQUEST_ENV = "CODESYS_BRIDGE_REQUEST"
BRIDGE_RESPONSE_ENV = "CODESYS_BRIDGE_RESPONSE"


@dataclass(frozen=True)
class CodesysIdeConfig:
    """Runtime configuration for the installed CODESYS-based IDE."""

    executable_path: str
    profile_name: str
    bridge_script_path: str
    no_ui: bool = True

    @classmethod
    def discover(
        cls,
        bridge_script_path: str,
        display_name: str = PRODUCT_NAME,
    ) -> "CodesysIdeConfig":
        """Resolve the installed SP20 executable from the Windows registry."""
        install_location = _find_install_location(display_name)
        executable_path = Path(install_location) / DEFAULT_EXECUTABLE_RELATIVE_PATH

        if not executable_path.exists():
            raise FileNotFoundError(
                "CODESYS executable was not found at '%s'." % executable_path
            )

        return cls(
            executable_path=str(executable_path),
            profile_name=display_name,
            bridge_script_path=bridge_script_path,
        )


class CodesysScriptExecutionError(RuntimeError):
    """Raised when the embedded script execution fails."""


class CodesysProjectInUseError(CodesysScriptExecutionError):
    """Raised when the target project is already opened elsewhere."""


class CodesysIdeRunner:
    """Runs bridge operations inside the real installed IDE."""

    def __init__(self, config: CodesysIdeConfig) -> None:
        self._config = config

    def run_operation(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute one bridge request inside the installed IDE."""
        normalized_payload = _normalize_codesys_payload_paths(payload)
        request_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            encoding="utf-8",
            delete=False,
        )
        response_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            encoding="utf-8",
            delete=False,
        )

        try:
            json.dump(normalized_payload, request_file)
            request_file.close()
            response_file.close()

            env = os.environ.copy()
            env[BRIDGE_REQUEST_ENV] = request_file.name
            env[BRIDGE_RESPONSE_ENV] = response_file.name

            argument_list = [
                '--profile="%s"' % self._config.profile_name,
                '--runscript="%s"' % self._config.bridge_script_path,
            ]
            if self._config.no_ui:
                argument_list.append("--noUI")

            powershell_command = (
                "$proc = Start-Process -FilePath '%s' -ArgumentList %s -Wait -PassThru; "
                "Write-Output $proc.ExitCode"
            ) % (
                self._config.executable_path.replace("'", "''"),
                ", ".join("'%s'" % arg.replace("'", "''") for arg in argument_list),
            )

            completed = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    powershell_command,
                ],
                env=env,
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )

            response_path = Path(response_file.name)
            if not response_path.exists():
                raise CodesysScriptExecutionError(
                    "CODESYS bridge did not create a response file. "
                    "stdout=%r stderr=%r returncode=%s"
                    % (completed.stdout, completed.stderr, completed.returncode)
                )

            response_text = response_path.read_text(encoding="utf-8").strip()
            if not response_text:
                raise CodesysScriptExecutionError(
                    "CODESYS bridge produced an empty response file. "
                    "stdout=%r stderr=%r returncode=%s"
                    % (completed.stdout, completed.stderr, completed.returncode)
                )

            response_payload = json.loads(response_text)

            if not response_payload.get("ok"):
                error = response_payload.get("error", {})
                error_message = error.get("message", "unknown error")
                error_message = _normalize_codesys_error_message(
                    error_message=error_message,
                    original_payload=payload,
                )
                exception_text = "CODESYS bridge operation failed: %s" % error_message
                if (
                    "ProjectConcurrentlyInUseException" in error_message
                    or "当前正由" in error_message
                    or "currently in use" in error_message.lower()
                ):
                    raise CodesysProjectInUseError(exception_text)
                raise CodesysScriptExecutionError(exception_text)

            if completed.returncode not in (0, None):
                raise CodesysScriptExecutionError(
                    "PowerShell launcher exited with %s. stdout=%r stderr=%r"
                    % (completed.returncode, completed.stdout, completed.stderr)
                )

            return response_payload["data"]
        finally:
            for path in (request_file.name, response_file.name):
                try:
                    Path(path).unlink(missing_ok=True)
                except OSError:
                    pass


class CodesysProjectAdapter:
    """Adapter that satisfies the project and POU service protocols."""

    def __init__(self, runner: CodesysIdeRunner) -> None:
        self._runner = runner

    @classmethod
    def from_discovery(cls, bridge_script_path: str) -> "CodesysProjectAdapter":
        """Create an adapter from the locally installed SP20 IDE."""
        config = CodesysIdeConfig.discover(bridge_script_path=bridge_script_path)
        return cls(runner=CodesysIdeRunner(config))

    def create(self, path: str, primary: bool = True) -> dict[str, Any]:
        """Create a project through the real IDE."""
        return self._runner.run_operation(
            {
                "operation": "create",
                "project_path": path,
                "primary": primary,
            }
        )

    def open(self, path: str) -> dict[str, Any]:
        """Open a project through the real IDE."""
        return self._runner.run_operation(
            {
                "operation": "open",
                "project_path": path,
                "primary": True,
            }
        )

    def save(self, path: str) -> dict[str, Any]:
        """Save a project through the real IDE."""
        return self._runner.run_operation(
            {
                "operation": "save",
                "project_path": path,
            }
        )

    def save_as(self, path: str, target_path: str) -> dict[str, Any]:
        """Save a project under a new path through the real IDE."""
        return self._runner.run_operation(
            {
                "operation": "save_as",
                "project_path": path,
                "target_project_path": target_path,
            }
        )

    def add_controller(
        self,
        project_path: str,
        device_name: str,
        device_type: int | str,
        device_id: str,
        device_version: str,
        module: str | None = None,
    ) -> dict[str, Any]:
        """Add a top-level controller device through the real IDE bridge."""
        return self._runner.run_operation(
            {
                "operation": "add_controller_device",
                "project_path": project_path,
                "device_name": device_name,
                "device_type": device_type,
                "device_id": device_id,
                "device_version": device_version,
                "module": module,
            }
        )

    def create_program(
        self,
        project_path: str,
        container_path: str,
        name: str,
        language: str = "ST",
    ) -> dict[str, Any]:
        """Create a program through the real IDE bridge."""
        return self._runner.run_operation(
            {
                "operation": "create_program",
                "project_path": project_path,
                "container_path": container_path,
                "name": name,
                "language": language,
            }
        )

    def create_function_block(
        self,
        project_path: str,
        container_path: str,
        name: str,
        language: str = "ST",
        base_type: str | None = None,
        interfaces: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a function block through the real IDE bridge."""
        return self._runner.run_operation(
            {
                "operation": "create_function_block",
                "project_path": project_path,
                "container_path": container_path,
                "name": name,
                "language": language,
                "base_type": base_type,
                "interfaces": interfaces or [],
            }
        )

    def create_function(
        self,
        project_path: str,
        container_path: str,
        name: str,
        return_type: str,
        language: str = "ST",
    ) -> dict[str, Any]:
        """Create a function through the real IDE bridge."""
        return self._runner.run_operation(
            {
                "operation": "create_function",
                "project_path": project_path,
                "container_path": container_path,
                "name": name,
                "return_type": return_type,
                "language": language,
            }
        )

    def read_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
    ) -> dict[str, Any]:
        """Read a textual declaration or implementation document."""
        return self._runner.run_operation(
            {
                "operation": "read_text_document",
                "project_path": project_path,
                "container_path": container_path,
                "object_name": object_name,
                "document_kind": document_kind,
            }
        )

    def replace_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        new_text: str,
    ) -> dict[str, Any]:
        """Replace a textual declaration or implementation document."""
        return self._runner.run_operation(
            {
                "operation": "replace_text_document",
                "project_path": project_path,
                "container_path": container_path,
                "object_name": object_name,
                "document_kind": document_kind,
                "new_text": new_text,
            }
        )

    def append_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        text_to_append: str,
    ) -> dict[str, Any]:
        """Append to a textual declaration or implementation document."""
        return self._runner.run_operation(
            {
                "operation": "append_text_document",
                "project_path": project_path,
                "container_path": container_path,
                "object_name": object_name,
                "document_kind": document_kind,
                "text_to_append": text_to_append,
            }
        )

    def insert_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        text_to_insert: str,
        insertion_offset: int,
    ) -> dict[str, Any]:
        """Insert text at a fixed offset in a textual document."""
        return self._runner.run_operation(
            {
                "operation": "insert_text_document",
                "project_path": project_path,
                "container_path": container_path,
                "object_name": object_name,
                "document_kind": document_kind,
                "text_to_insert": text_to_insert,
                "insertion_offset": insertion_offset,
            }
        )

    def replace_text_line(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        line_number: int,
        new_text: str,
    ) -> dict[str, Any]:
        """Replace one line in a textual declaration or implementation document."""
        return self._runner.run_operation(
            {
                "operation": "replace_text_line",
                "project_path": project_path,
                "container_path": container_path,
                "object_name": object_name,
                "document_kind": document_kind,
                "line_number": line_number,
                "new_text": new_text,
            }
        )

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
    ) -> dict[str, Any]:
        return self._runner.run_operation(
            {
                "operation": "generate_pou_transaction",
                "project_path": project_path,
                "container_path": container_path,
                "pou_name": pou_name,
                "pou_kind": pou_kind,
                "language": language,
                "return_type": return_type,
                "base_type": base_type,
                "interfaces": interfaces or [],
                "declaration_text": declaration_text,
                "implementation_text": implementation_text,
                "write_strategy": write_strategy,
                "verify_mode": verify_mode,
            }
        )

    def edit_pou_transaction(
        self,
        project_path: str,
        container_path: str,
        pou_name: str,
        operations: list[dict[str, Any]],
        verify_mode: str | None = None,
    ) -> dict[str, Any]:
        return self._runner.run_operation(
            {
                "operation": "edit_pou_transaction",
                "project_path": project_path,
                "container_path": container_path,
                "pou_name": pou_name,
                "operations": operations,
                "verify_mode": verify_mode,
            }
        )

    def list_objects(
        self,
        project_path: str,
        container_path: str = "/",
    ) -> dict[str, Any]:
        """List child objects below the given logical container."""
        return self._runner.run_operation(
            {
                "operation": "list_objects",
                "project_path": project_path,
                "container_path": container_path,
            }
        )

    def find_objects(
        self,
        project_path: str,
        object_name: str,
        container_path: str = "/",
        recursive: bool = True,
    ) -> dict[str, Any]:
        """Find matching objects below the given logical container."""
        return self._runner.run_operation(
            {
                "operation": "find_objects",
                "project_path": project_path,
                "object_name": object_name,
                "container_path": container_path,
                "recursive": recursive,
            }
        )

    def scan_network_devices(
        self,
        gateway_name: str | None = None,
        use_cached_result: bool = False,
    ) -> dict[str, Any]:
        """Scan online targets through a configured gateway."""
        return self._runner.run_operation(
            {
                "operation": "scan_network_devices",
                "gateway_name": gateway_name,
                "use_cached_result": use_cached_result,
            }
        )

    def copy_project_for_testing(
        self,
        source_project_path: str,
        target_project_path: str,
    ) -> str:
        """Create a filesystem copy of a project for manual integration testing."""
        shutil.copy2(source_project_path, target_project_path)
        return target_project_path


def _find_install_location(display_name: str) -> str:
    for hive_path in (
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, hive_path) as hive:
                subkey_count = winreg.QueryInfoKey(hive)[0]
                for index in range(subkey_count):
                    subkey_name = winreg.EnumKey(hive, index)
                    with winreg.OpenKey(hive, subkey_name) as subkey:
                        try:
                            current_display_name = winreg.QueryValueEx(
                                subkey,
                                "DisplayName",
                            )[0]
                        except FileNotFoundError:
                            continue

                        if current_display_name != display_name:
                            continue

                        install_location = winreg.QueryValueEx(
                            subkey,
                            "InstallLocation",
                        )[0]
                        if not install_location:
                            raise FileNotFoundError(
                                "InstallLocation is empty for '%s'." % display_name
                            )
                        return install_location
        except FileNotFoundError:
            continue

    raise FileNotFoundError(
        "Could not find installed product '%s' in registry." % display_name
    )


def _normalize_codesys_payload_paths(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    for key in ("project_path", "target_project_path"):
        value = normalized.get(key)
        if isinstance(value, str) and value.strip():
            normalized[key] = _normalize_codesys_path(value)
    return normalized


def _normalize_codesys_path(path: str) -> str:
    if _is_ascii(path):
        return path

    exact_short = _get_short_path(path)
    if exact_short is not None:
        return exact_short

    source_path = Path(path)
    parent_short = _get_short_path(str(source_path.parent))
    if parent_short is not None:
        candidate = str(Path(parent_short) / source_path.name)
        if _is_ascii(candidate):
            return candidate

    return path


def _get_short_path(path: str) -> str | None:
    if os.name != "nt":
        return None

    buffer_size = 4096
    output_buffer = ctypes.create_unicode_buffer(buffer_size)
    result = ctypes.windll.kernel32.GetShortPathNameW(
        path,
        output_buffer,
        buffer_size,
    )
    if result == 0:
        return None
    return output_buffer.value


def _normalize_codesys_error_message(
    error_message: str,
    original_payload: dict[str, Any],
) -> str:
    project_path = original_payload.get("project_path")
    if (
        isinstance(project_path, str)
        and not _is_ascii(project_path)
        and ("????" in error_message or "\\u003f\\u003f\\u003f\\u003f" in error_message)
    ):
        return (
            "The real IDE backend could not resolve the non-ASCII project path. "
            "Move or copy the project to an ASCII-only path, or use an ASCII-only "
            "parent directory for the project file."
        )
    return error_message


def _is_ascii(value: str) -> bool:
    try:
        value.encode("ascii")
    except UnicodeEncodeError:
        return False
    return True
