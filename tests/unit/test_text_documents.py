"""Unit tests for textual document services."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.services.pous.append_text_document import append_text_document
from codesys_mcp_server.services.pous.insert_text_document import insert_text_document
from codesys_mcp_server.services.pous.read_textual_declaration import read_textual_declaration
from codesys_mcp_server.services.pous.read_textual_implementation import (
    read_textual_implementation,
)
from codesys_mcp_server.services.pous.replace_text_document import replace_text_document


NESTED_APPLICATION_PATH = "MyController/PLCLogic/Application"


class FakeTextDocumentReader:
    """Simple text reader test double."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def read_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
    ) -> dict[str, str]:
        self.calls.append(
            {
                "project_path": project_path,
                "container_path": container_path,
                "object_name": object_name,
                "document_kind": document_kind,
            }
        )
        return {"text": "PROGRAM MainProgram"}

    def list_objects(
        self,
        project_path: str,
        container_path: str = "/",
    ) -> dict[str, object]:
        if container_path == "/":
            return {"children": [{"name": "MyController", "is_folder": True, "can_browse": True}]}
        if container_path == "MyController":
            return {"children": [{"name": "PLCLogic", "is_folder": True, "can_browse": True}]}
        if container_path == "MyController/PLCLogic":
            return {"children": [{"name": "Application", "is_folder": True, "can_browse": True}]}
        return {"children": []}


class MissingTextReader:
    """Reader test double that simulates missing text documents."""

    def read_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
    ) -> str:
        raise LookupError("Text document missing")


class FakeTextDocumentWriter:
    """Stateful test double for text update services."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.declaration = "PROGRAM MainProgram\nVAR\n    Counter: INT;\nEND_VAR"
        self.implementation = "Counter := Counter + 1;"

    def list_objects(
        self,
        project_path: str,
        container_path: str = "/",
    ) -> dict[str, object]:
        if container_path == "/":
            return {"children": [{"name": "MyController", "is_folder": True, "can_browse": True}]}
        if container_path == "MyController":
            return {"children": [{"name": "PLCLogic", "is_folder": True, "can_browse": True}]}
        if container_path == "MyController/PLCLogic":
            return {"children": [{"name": "Application", "is_folder": True, "can_browse": True}]}
        return {"children": []}

    def read_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
    ) -> dict[str, str]:
        self.calls.append(
            {
                "kind": "read",
                "project_path": project_path,
                "container_path": container_path,
                "object_name": object_name,
                "document_kind": document_kind,
            }
        )
        if document_kind == "declaration":
            return {"text": self.declaration}
        if document_kind == "implementation":
            return {"text": self.implementation}
        raise LookupError("Unsupported document kind")

    def replace_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        new_text: str,
    ) -> None:
        self.calls.append(
            {
                "kind": "replace",
                "project_path": project_path,
                "container_path": container_path,
                "object_name": object_name,
                "document_kind": document_kind,
                "new_text": new_text,
            }
        )
        if document_kind == "declaration":
            self.declaration = new_text
        else:
            self.implementation = new_text

    def append_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        text_to_append: str,
    ) -> None:
        self.calls.append(
            {
                "kind": "append",
                "project_path": project_path,
                "container_path": container_path,
                "object_name": object_name,
                "document_kind": document_kind,
                "text_to_append": text_to_append,
            }
        )
        if document_kind == "declaration":
            self.declaration += text_to_append
        else:
            self.implementation += text_to_append

    def insert_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        text_to_insert: str,
        insertion_offset: int,
    ) -> None:
        self.calls.append(
            {
                "kind": "insert",
                "project_path": project_path,
                "container_path": container_path,
                "object_name": object_name,
                "document_kind": document_kind,
                "text_to_insert": text_to_insert,
                "insertion_offset": insertion_offset,
            }
        )
        if document_kind == "declaration":
            self.declaration = (
                self.declaration[:insertion_offset]
                + text_to_insert
                + self.declaration[insertion_offset:]
            )
        else:
            self.implementation = (
                self.implementation[:insertion_offset]
                + text_to_insert
                + self.implementation[insertion_offset:]
            )


class CorruptingTextDocumentWriter(FakeTextDocumentWriter):
    """Writer that simulates a broken write/read round-trip."""

    def replace_text_document(
        self,
        project_path: str,
        container_path: str,
        object_name: str,
        document_kind: str,
        new_text: str,
    ) -> None:
        super().replace_text_document(
            project_path=project_path,
            container_path=container_path,
            object_name=object_name,
            document_kind=document_kind,
            new_text=new_text,
        )
        if document_kind == "implementation":
            self.implementation = self.implementation + " "


class TextDocumentServiceTests(unittest.TestCase):
    """Behavioral tests for textual document MCP services."""

    def test_read_textual_declaration_returns_text(self) -> None:
        reader = FakeTextDocumentReader()

        response = read_textual_declaration(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "object_name": "MainProgram",
            },
            text_document_reader=reader,
            request_id="req-text-001",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["data"]["document_kind"], "declaration")
        self.assertEqual(response["data"]["text"], "PROGRAM MainProgram")
        declaration_read = next(call for call in reader.calls if call["document_kind"] == "declaration")
        self.assertEqual(declaration_read["document_kind"], "declaration")
        self.assertEqual(declaration_read["container_path"], NESTED_APPLICATION_PATH)

    def test_read_textual_implementation_reports_missing_text(self) -> None:
        response = read_textual_implementation(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "object_name": "MainProgram",
            },
            text_document_reader=MissingTextReader(),
            request_id="req-text-002",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "TEXT_DOCUMENT_NOT_FOUND")

    def test_replace_text_document_allows_empty_string(self) -> None:
        writer = FakeTextDocumentWriter()

        response = replace_text_document(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "object_name": "MainProgram",
                "document_kind": "implementation",
                "new_text": "",
            },
            text_document_replacer=writer,
            request_id="req-text-003",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["data"]["text_length"], 0)
        replace_call = next(call for call in writer.calls if call["kind"] == "replace")
        self.assertEqual(replace_call["new_text"], "")
        self.assertTrue(response["data"]["roundtrip_verified"])

    def test_append_text_document_appends_to_tail(self) -> None:
        writer = FakeTextDocumentWriter()

        response = append_text_document(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "object_name": "MainProgram",
                "document_kind": "implementation",
                "text_to_append": "\nCounter := Counter + 1;",
            },
            text_document_appender=writer,
            request_id="req-text-004",
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["data"]["appended_length"], 23)
        append_call = next(call for call in writer.calls if call["kind"] == "append")
        self.assertEqual(append_call["kind"], "append")
        self.assertEqual(append_call["container_path"], NESTED_APPLICATION_PATH)
        self.assertTrue(response["data"]["roundtrip_verified"])

    def test_insert_text_document_requires_non_negative_offset(self) -> None:
        writer = FakeTextDocumentWriter()

        response = insert_text_document(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "object_name": "MainProgram",
                "document_kind": "implementation",
                "text_to_insert": "Start := TRUE;\n",
                "insertion_offset": -1,
            },
            text_document_inserter=writer,
            request_id="req-text-005",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "insertion_offset")
        self.assertEqual(writer.calls, [])

    def test_insert_text_document_rejects_offsets_beyond_document_length(self) -> None:
        writer = FakeTextDocumentWriter()

        response = insert_text_document(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "object_name": "MainProgram",
                "document_kind": "implementation",
                "text_to_insert": "Start := TRUE;\n",
                "insertion_offset": 999,
            },
            text_document_inserter=writer,
            request_id="req-text-005b",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response["error"]["details"]["field"], "insertion_offset")

    def test_replace_text_document_rejects_non_ascii_text(self) -> None:
        writer = FakeTextDocumentWriter()

        response = replace_text_document(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "object_name": "MainProgram",
                "document_kind": "implementation",
                "new_text": "// init\nx := 1;\u4e2d",
            },
            text_document_replacer=writer,
            request_id="req-text-006",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "NON_ASCII_TEXT_UNSUPPORTED")
        self.assertEqual(writer.calls, [])

    def test_append_text_document_rejects_non_ascii_text(self) -> None:
        writer = FakeTextDocumentWriter()

        response = append_text_document(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "object_name": "MainProgram",
                "document_kind": "implementation",
                "text_to_append": "// init\u4e2d",
            },
            text_document_appender=writer,
            request_id="req-text-007",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "NON_ASCII_TEXT_UNSUPPORTED")
        self.assertEqual(writer.calls, [])

    def test_replace_text_document_verifies_roundtrip_after_write(self) -> None:
        writer = CorruptingTextDocumentWriter()

        response = replace_text_document(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "object_name": "MainProgram",
                "document_kind": "implementation",
                "new_text": "Counter := Counter + 2;",
            },
            text_document_replacer=writer,
            request_id="req-text-008",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "TEXT_ROUNDTRIP_VERIFICATION_FAILED")

    def test_replace_text_document_rejects_undeclared_identifiers(self) -> None:
        writer = FakeTextDocumentWriter()

        response = replace_text_document(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "object_name": "MainProgram",
                "document_kind": "implementation",
                "new_text": "Counter := MissingVar + 1;",
            },
            text_document_replacer=writer,
            request_id="req-text-009",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "POU_SOURCE_VALIDATION_FAILED")
        self.assertEqual(response["error"]["details"]["missing_identifiers"], ["MissingVar"])

    def test_replace_declaration_rejects_breaking_current_implementation(self) -> None:
        writer = FakeTextDocumentWriter()

        response = replace_text_document(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "object_name": "MainProgram",
                "document_kind": "declaration",
                "new_text": "PROGRAM MainProgram\nVAR\nEND_VAR",
            },
            text_document_replacer=writer,
            request_id="req-text-010",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "POU_SOURCE_VALIDATION_FAILED")
        self.assertEqual(response["error"]["details"]["missing_identifiers"], ["Counter"])


if __name__ == "__main__":
    unittest.main()
