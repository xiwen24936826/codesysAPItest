from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.services.pous.edit_pou_transaction import edit_pou_transaction
from codesys_mcp_server.services.pous.generate_pou_transaction import generate_pou_transaction
from codesys_mcp_server.server.in_memory_backend import InMemoryCodesysBackend


class CorruptingInMemoryBackend(InMemoryCodesysBackend):
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
            super().replace_text_document(
                project_path=project_path,
                container_path=container_path,
                object_name=object_name,
                document_kind=document_kind,
                new_text=new_text + " ",
            )


class PouTransactionServiceTests(unittest.TestCase):
    def test_generate_pou_transaction_creates_and_writes_in_one_call(self) -> None:
        backend = InMemoryCodesysBackend()
        backend.create("D:/Projects/demo.project", primary=True)

        response = generate_pou_transaction(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "pou_name": "Diameter_Cal",
                "pou_kind": "function_block",
                "declaration_text": "FUNCTION_BLOCK Diameter_Cal\nVAR\nEND_VAR\n",
                "implementation_text": "(* impl *)\n",
                "write_strategy": "replace",
                "verify_mode": "normalize_newlines",
            },
            pou_transaction_generator=backend,
            request_id="req-tx-001",
        )

        self.assertTrue(response["ok"])
        self.assertTrue(response["data"]["saved"])
        self.assertTrue(response["data"]["verification"]["ok"])

    def test_generate_pou_transaction_reports_verification_failure(self) -> None:
        backend = CorruptingInMemoryBackend()
        backend.create("D:/Projects/demo.project", primary=True)

        response = generate_pou_transaction(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "pou_name": "Diameter_Cal",
                "pou_kind": "function_block",
                "declaration_text": "FUNCTION_BLOCK Diameter_Cal\nVAR\nEND_VAR\n",
                "implementation_text": "Counter := Counter + 1;\n",
                "write_strategy": "replace",
                "verify_mode": "normalize_newlines",
            },
            pou_transaction_generator=backend,
            request_id="req-tx-002",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "POU_TRANSACTION_VERIFICATION_FAILED")

    def test_edit_pou_transaction_applies_operations(self) -> None:
        backend = InMemoryCodesysBackend()
        backend.create("D:/Projects/demo.project", primary=True)
        backend.create_function_block(
            project_path="D:/Projects/demo.project",
            container_path="Application",
            name="Diameter_Cal",
            language="ST",
        )
        backend.replace_text_document(
            project_path="D:/Projects/demo.project",
            container_path="Application",
            object_name="Diameter_Cal",
            document_kind="declaration",
            new_text="FUNCTION_BLOCK Diameter_Cal\nVAR\nx : INT;\nEND_VAR\n",
        )
        backend.replace_text_document(
            project_path="D:/Projects/demo.project",
            container_path="Application",
            object_name="Diameter_Cal",
            document_kind="implementation",
            new_text="x := 1;\n",
        )

        response = edit_pou_transaction(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "pou_name": "Diameter_Cal",
                "operations": [
                    {
                        "document_kind": "implementation",
                        "op": "replace_line",
                        "line_number": 1,
                        "new_text": "x := x + 1;",
                    }
                ],
                "verify_mode": "normalize_newlines",
            },
            pou_transaction_editor=backend,
            request_id="req-tx-003",
        )

        self.assertTrue(response["ok"])
        self.assertTrue(response["data"]["verification"]["ok"])

    def test_edit_pou_transaction_reports_verification_failure(self) -> None:
        backend = CorruptingInMemoryBackend()
        backend.create("D:/Projects/demo.project", primary=True)
        backend.create_function_block(
            project_path="D:/Projects/demo.project",
            container_path="Application",
            name="Diameter_Cal",
            language="ST",
        )
        backend.replace_text_document(
            project_path="D:/Projects/demo.project",
            container_path="Application",
            object_name="Diameter_Cal",
            document_kind="declaration",
            new_text="FUNCTION_BLOCK Diameter_Cal\nVAR\nx : INT;\nEND_VAR\n",
        )

        response = edit_pou_transaction(
            request={
                "project_path": "D:/Projects/demo.project",
                "container_path": "Application",
                "pou_name": "Diameter_Cal",
                "operations": [
                    {
                        "document_kind": "implementation",
                        "op": "replace",
                        "new_text": "x := x + 1;\n",
                    }
                ],
                "verify_mode": "normalize_newlines",
            },
            pou_transaction_editor=backend,
            request_id="req-tx-004",
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "POU_TRANSACTION_VERIFICATION_FAILED")


if __name__ == "__main__":
    unittest.main()
