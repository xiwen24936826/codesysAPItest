"""Runtime helpers for standardized server startup."""

from __future__ import annotations

import json
import sys
from typing import Any

from codesys_mcp_server.config import ServerSettings
from codesys_mcp_server.logging import configure_logging

from .factory import (
    create_in_memory_server_application,
    create_real_ide_server_application,
)


class ServerRuntime:
    """Thin runtime wrapper around the local server application."""

    def __init__(self, settings: ServerSettings) -> None:
        self._settings = settings
        configure_logging(level=settings.log_level, json_output=settings.log_json)
        self._app = self._build_application()

    def _build_application(self):
        if self._settings.backend_mode == "in_memory":
            return create_in_memory_server_application()
        if self._settings.backend_mode == "real_ide":
            return create_real_ide_server_application(
                bridge_script_path=self._settings.bridge_script_path
            )
        raise ValueError("Unsupported backend mode: %s" % self._settings.backend_mode)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._app.list_tools()
        ]

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        request_id: str | None = None,
    ) -> dict[str, Any]:
        return self._app.call_tool(name=name, arguments=arguments, request_id=request_id).payload

    def handle_protocol_message(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Handle one JSON-RPC-style stdio request."""
        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params", {})

        if not isinstance(method, str):
            return self._protocol_error(
                request_id=request_id,
                code=-32600,
                message="Invalid request: method must be a string.",
            )

        if method == "notifications/initialized":
            return None

        if method == "initialize":
            return self._protocol_result(
                request_id=request_id,
                result={
                    "protocolVersion": "2026-04-22-draft",
                    "serverInfo": {
                        "name": "codesys-mcp-local",
                        "version": "0.1.0",
                    },
                    "capabilities": {
                        "tools": {
                            "listChanged": False,
                        }
                    },
                },
            )

        if method == "ping":
            return self._protocol_result(request_id=request_id, result={"pong": True})

        if method == "tools/list":
            return self._protocol_result(
                request_id=request_id,
                result={"tools": self.list_tools()},
            )

        if method == "tools/call":
            if not isinstance(params, dict):
                return self._protocol_error(
                    request_id=request_id,
                    code=-32602,
                    message="Invalid params for tools/call.",
                )
            if not isinstance(params.get("name"), str) or not params["name"].strip():
                return self._protocol_error(
                    request_id=request_id,
                    code=-32602,
                    message="Invalid params for tools/call: name is required.",
                )
            return self._protocol_result(
                request_id=request_id,
                result=self.call_tool(
                    name=params["name"],
                    arguments=params.get("arguments", {}),
                    request_id=params.get("request_id"),
                ),
            )

        if method == "shutdown":
            return self._protocol_result(
                request_id=request_id,
                result={"acknowledged": True},
            )

        return self._protocol_error(
            request_id=request_id,
            code=-32601,
            message="Method not found: %s" % method,
        )

    def serve_stdio(self, stdin: Any = None, stdout: Any = None) -> int:
        """Serve a JSON-RPC-style newline-delimited stdio protocol."""
        input_stream = stdin or sys.stdin
        output_stream = stdout or sys.stdout

        for raw_line in input_stream:
            line = raw_line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError as exc:
                response = self._protocol_error(
                    request_id=None,
                    code=-32700,
                    message="Parse error: %s" % str(exc),
                )
            else:
                if not isinstance(request, dict):
                    response = self._protocol_error(
                        request_id=None,
                        code=-32600,
                        message="Invalid request: top-level JSON object required.",
                    )
                else:
                    response = self.handle_protocol_message(request)

            if response is None:
                continue

            output_stream.write(json.dumps(response, ensure_ascii=False) + "\n")
            output_stream.flush()
        return 0

    def serve_jsonl(self, stdin: Any = None, stdout: Any = None) -> int:
        """Backward-compatible alias for the stdio message loop."""
        return self.serve_stdio(stdin=stdin, stdout=stdout)

    @staticmethod
    def _protocol_result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result,
        }

    @staticmethod
    def _protocol_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message,
            },
        }


def create_runtime(settings: ServerSettings | None = None) -> ServerRuntime:
    """Create the standardized local runtime."""
    return ServerRuntime(settings or ServerSettings.from_env())
