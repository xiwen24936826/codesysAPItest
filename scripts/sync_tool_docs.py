"""Generate UTF-8 tool-catalog and workflow docs from the canonical tool catalog."""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from codesys_mcp_server.tools.catalog import get_tool_catalog, tool_code_for  # noqa: E402


WORKFLOW_TITLES = {
    "existing_project_edit_flow": "现有工程编辑流",
    "new_project_flow": "新建工程流",
    "network_scan_flow": "网络扫描流",
    "online_operations_flow": "PLC 在线操作流",
}

DOMAIN_LABELS = {
    "projects": "projects / 项目",
    "pous": "pous / 程序组织单元",
    "devices": "devices / 设备与扫描",
    "online": "online / 在线操作",
    "ethercat": "ethercat / EtherCAT 预留",
}

RISK_LABELS = {
    "safe": "safe / 低风险",
    "caution": "caution / 需谨慎",
    "dangerous": "dangerous / 高风险",
}


def main() -> int:
    catalog = get_tool_catalog()
    _write_tool_catalog_doc(catalog)
    _write_client_workflows_doc(catalog)
    return 0


def _write_tool_catalog_doc(catalog) -> None:
    output_path = REPO_ROOT / "docs" / "api_specs" / "tool_catalog.md"
    lines = [
        "# Tool Catalog",
        "",
        "本文档由 `scripts/sync_tool_docs.py` 从 `src/codesys_mcp_server/tools/catalog.py` 自动生成。",
        "",
        "这是当前 MCP 工具的单一权威索引视图，用于查看工具分类、功能说明、风险等级和输入契约。",
        "",
    ]

    for entry in catalog:
        lines.extend(
            [
                "## `%s`" % entry.name,
                "",
                "- 代码：`%s`" % tool_code_for(entry.name),
                "- 类别：`%s`" % DOMAIN_LABELS.get(entry.domain, entry.domain),
                "- 功能：%s" % entry.description,
                "- 风险等级：`%s`" % RISK_LABELS.get(entry.risk_level, entry.risk_level),
                "- 工作流：%s"
                % ", ".join(
                    "`%s`" % WORKFLOW_TITLES.get(workflow, workflow)
                    for workflow in entry.workflow_ids
                ),
            ]
        )
        if entry.preferred_predecessors:
            lines.append(
                "- 推荐前置工具：%s"
                % ", ".join("`%s`" % tool_name for tool_name in entry.preferred_predecessors)
            )
        if entry.notes:
            lines.append("- 备注：%s" % " ".join(entry.notes))
        lines.extend(
            [
                "",
                "输入字段：",
                "",
                "```json",
                json.dumps(entry.input_schema, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_client_workflows_doc(catalog) -> None:
    output_path = REPO_ROOT / "docs" / "client_workflows.md"
    grouped: dict[str, list] = defaultdict(list)
    for entry in catalog:
        for workflow_id in entry.workflow_ids:
            grouped[workflow_id].append(entry)

    lines = [
        "# Client Workflows",
        "",
        "本文档由 `scripts/sync_tool_docs.py` 从 `src/codesys_mcp_server/tools/catalog.py` 自动生成。",
        "",
        "用于指导客户端在不同场景下优先选择 MCP 工具，并按风险和前置条件理解工作流。",
        "",
    ]

    for workflow_id, title in WORKFLOW_TITLES.items():
        lines.extend(["## %s" % title, ""])
        tools = grouped.get(workflow_id, [])
        if not tools:
            lines.extend(
                [
                    "- 当前 catalog 中尚无直接归属到该工作流的已实现工具。",
                    "",
                ]
            )
            continue

        ordered = sorted(
            tools,
            key=lambda item: (
                item.risk_level == "dangerous",
                item.domain,
                item.name,
            ),
        )
        for entry in ordered:
            lines.append(
                "- `%s`：%s（风险：`%s`）"
                % (
                    entry.name,
                    entry.description,
                    RISK_LABELS.get(entry.risk_level, entry.risk_level),
                )
            )
            if entry.preferred_predecessors:
                lines.append(
                    "  前置建议：%s"
                    % ", ".join("`%s`" % tool_name for tool_name in entry.preferred_predecessors)
                )
            if entry.notes:
                lines.append("  备注：%s" % " ".join(entry.notes))
        lines.append("")

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
