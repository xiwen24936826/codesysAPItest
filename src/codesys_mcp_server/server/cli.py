"""Local CLI entrypoint for offline server validation."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from codesys_mcp_server.config import ServerSettings

from .runtime import create_runtime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codesys-mcp-local",
        description="Offline local MCP server utility for CODESYS phase-1 tools.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-tools", help="List registered tools.")
    list_parser.add_argument(
        "--view",
        default="summary",
        choices=["summary", "json"],
        help="summary prints a concise catalog table; json prints the machine-readable catalog.",
    )

    call_parser = subparsers.add_parser("call-tool", help="Call one tool with JSON arguments.")
    call_parser.add_argument("tool_name", help="Registered tool name.")
    call_parser.add_argument(
        "--arguments",
        default="{}",
        help="JSON object passed as tool arguments.",
    )
    call_parser.add_argument("--request-id", default=None, help="Optional request id.")

    subparsers.add_parser(
        "serve-stdio",
        help="Serve a JSON-RPC-style newline-delimited stdio protocol.",
    )
    subparsers.add_parser(
        "serve-jsonl",
        help="Backward-compatible alias for the stdio protocol.",
    )

    parser.add_argument(
        "--backend",
        default="in_memory",
        choices=["in_memory", "real_ide"],
        help="Backend mode used by the local runtime.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Console log level.",
    )
    parser.add_argument(
        "--bridge-script-path",
        default=None,
        help="Optional override path for the embedded CODESYS bridge script.",
    )
    parser.add_argument(
        "--log-json",
        action="store_true",
        help="Emit JSON logs.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    runtime = create_runtime(
        ServerSettings(
            backend_mode=args.backend,
            bridge_script_path=args.bridge_script_path,
            log_level=args.log_level,
            log_json=args.log_json,
        )
    )

    if args.command == "list-tools":
        payload = runtime.export_tool_catalog()
        if args.view == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(_render_tool_catalog_summary(payload))
        return 0

    if args.command == "serve-stdio":
        return runtime.serve_stdio()

    if args.command == "serve-jsonl":
        return runtime.serve_jsonl()

    arguments = json.loads(args.arguments)
    result = runtime.call_tool(
        name=args.tool_name,
        arguments=arguments,
        request_id=args.request_id,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


def _render_tool_catalog_summary(catalog: list[dict[str, object]]) -> str:
    """Render a concise terminal-friendly summary for the tool catalog."""
    ordered = sorted(
        catalog,
        key=lambda item: (
            str(item.get("category", "")),
            str(item.get("code", "")),
            str(item.get("name", "")),
        ),
    )
    lines = [
        "| Category | Name | Function | Code |",
        "| --- | --- | --- | --- |",
    ]
    for item in ordered:
        lines.append(
            "| {category} | {name} | {description} | {code} |".format(
                category=item.get("category", ""),
                name=item.get("name", ""),
                description=item.get("description", ""),
                code=item.get("code", ""),
            )
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
