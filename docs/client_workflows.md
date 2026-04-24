# Client Workflows

本文档由 `scripts/sync_tool_docs.py` 从 `src/codesys_mcp_server/tools/catalog.py` 自动生成。

用于指导客户端在不同场景下优先选择 MCP 工具，并按风险和前置条件理解工作流。

## 现有工程编辑流

- `append_text_document`：Append text to the end of a declaration or implementation document.（风险：`caution / 需谨慎`）
  前置建议：`open_project`
- `create_function`：Create a function in the selected container.（风险：`caution / 需谨慎`）
  前置建议：`open_project`, `list_project_objects`
- `create_function_block`：Create a function block in the selected container.（风险：`caution / 需谨慎`）
  前置建议：`open_project`, `list_project_objects`
- `create_program`：Create a PRG in the selected container.（风险：`caution / 需谨慎`）
  前置建议：`open_project`, `list_project_objects`
- `insert_text_document`：Insert text into a declaration or implementation document at a fixed offset.（风险：`caution / 需谨慎`）
  前置建议：`open_project`
- `read_textual_declaration`：Read the textual declaration part of an object.（风险：`safe / 低风险`）
  前置建议：`open_project`
- `read_textual_implementation`：Read the textual implementation part of an object.（风险：`safe / 低风险`）
  前置建议：`open_project`
- `replace_text_document`：Replace a declaration or implementation document.（风险：`caution / 需谨慎`）
  前置建议：`open_project`
- `find_project_objects`：Find matching objects by name below a logical container in the project tree.（风险：`safe / 低风险`）
  前置建议：`open_project`
- `list_project_objects`：List child objects below a logical container in the project tree.（风险：`safe / 低风险`）
  前置建议：`open_project`
  备注：Prefer can_browse over is_folder when recursing the returned tree.
- `open_project`：Open an existing CODESYS project.（风险：`safe / 低风险`）
- `save_project`：Save or save-as an existing CODESYS project.（风险：`caution / 需谨慎`）

## 新建工程流

- `create_function`：Create a function in the selected container.（风险：`caution / 需谨慎`）
  前置建议：`open_project`, `list_project_objects`
- `create_function_block`：Create a function block in the selected container.（风险：`caution / 需谨慎`）
  前置建议：`open_project`, `list_project_objects`
- `create_program`：Create a PRG in the selected container.（风险：`caution / 需谨慎`）
  前置建议：`open_project`, `list_project_objects`
- `find_project_objects`：Find matching objects by name below a logical container in the project tree.（风险：`safe / 低风险`）
  前置建议：`open_project`
- `list_project_objects`：List child objects below a logical container in the project tree.（风险：`safe / 低风险`）
  前置建议：`open_project`
  备注：Prefer can_browse over is_folder when recursing the returned tree.
- `open_project`：Open an existing CODESYS project.（风险：`safe / 低风险`）
- `save_project`：Save or save-as an existing CODESYS project.（风险：`caution / 需谨慎`）
- `add_controller_device`：Add a top-level controller device to a project.（风险：`dangerous / 高风险`）
  前置建议：`create_project`, `open_project`
  备注：Not part of the preferred existing-project POU editing flow.
- `create_project`：Create a new CODESYS project.（风险：`dangerous / 高风险`）
  备注：Only for explicit new-project creation requests. Must not be used as a fallback during existing-project editing.

## 网络扫描流

- `scan_network_devices`：Scan online targets through a configured CODESYS gateway.（风险：`safe / 低风险`）

## PLC 在线操作流

- `open_project`：Open an existing CODESYS project.（风险：`safe / 低风险`）
