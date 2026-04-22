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
    """Generic test double for text update services."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

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
        self.assertEqual(reader.calls[0]["document_kind"], "declaration")

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
        self.assertEqual(writer.calls[0]["new_text"], "")

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
        self.assertEqual(writer.calls[0]["kind"], "append")

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


if __name__ == "__main__":
    unittest.main()
