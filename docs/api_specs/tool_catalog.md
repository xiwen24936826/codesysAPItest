# Tool Catalog

本文件由 `scripts/sync_tool_docs.py` 从 `src/codesys_mcp_server/tools/catalog.py` 生成。

这是当前 MCP 工具的唯一权威索引文档视图。

## `create_project`

- 描述：Create a new CODESYS project.
- 域：`projects`
- 风险等级：`dangerous`
- 工作流：`new_project_flow`
- 备注：Only for explicit new-project creation requests. Must not be used as a fallback during existing-project editing.

输入字段：

```json
{
  "type": "object",
  "required": [
    "project_path",
    "project_mode"
  ],
  "properties": {
    "project_path": {
      "type": "string"
    },
    "project_mode": {
      "type": "string",
      "enum": [
        "empty",
        "template"
      ]
    },
    "set_as_primary": {
      "type": "boolean"
    },
    "template_project_path": {
      "type": "string"
    }
  },
  "additionalProperties": false
}
```

## `open_project`

- 描述：Open an existing CODESYS project.
- 域：`projects`
- 风险等级：`safe`
- 工作流：`existing_project_edit_flow`, `new_project_flow`, `online_operations_flow`

输入字段：

```json
{
  "type": "object",
  "required": [
    "project_path"
  ],
  "properties": {
    "project_path": {
      "type": "string"
    }
  },
  "additionalProperties": false
}
```

## `list_project_objects`

- 描述：List child objects below a logical container in the project tree.
- 域：`projects`
- 风险等级：`safe`
- 工作流：`existing_project_edit_flow`, `new_project_flow`
- 推荐前置工具：`open_project`
- 备注：Prefer can_browse over is_folder when recursing the returned tree.

输入字段：

```json
{
  "type": "object",
  "required": [
    "project_path"
  ],
  "properties": {
    "project_path": {
      "type": "string"
    },
    "container_path": {
      "type": "string"
    }
  },
  "additionalProperties": false
}
```

## `find_project_objects`

- 描述：Find matching objects by name below a logical container in the project tree.
- 域：`projects`
- 风险等级：`safe`
- 工作流：`existing_project_edit_flow`, `new_project_flow`
- 推荐前置工具：`open_project`

输入字段：

```json
{
  "type": "object",
  "required": [
    "project_path",
    "object_name"
  ],
  "properties": {
    "project_path": {
      "type": "string"
    },
    "object_name": {
      "type": "string"
    },
    "container_path": {
      "type": "string"
    },
    "recursive": {
      "type": "boolean"
    }
  },
  "additionalProperties": false
}
```

## `scan_network_devices`

- 描述：Scan online targets through a configured CODESYS gateway.
- 域：`online`
- 风险等级：`safe`
- 工作流：`network_scan_flow`

输入字段：

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "gateway_name": {
      "type": "string"
    },
    "use_cached_result": {
      "type": "boolean"
    }
  },
  "additionalProperties": false
}
```

## `save_project`

- 描述：Save or save-as an existing CODESYS project.
- 域：`projects`
- 风险等级：`caution`
- 工作流：`existing_project_edit_flow`, `new_project_flow`

输入字段：

```json
{
  "type": "object",
  "required": [
    "project_path",
    "save_mode"
  ],
  "properties": {
    "project_path": {
      "type": "string"
    },
    "save_mode": {
      "type": "string",
      "enum": [
        "save",
        "save_as"
      ]
    },
    "target_project_path": {
      "type": "string"
    }
  },
  "additionalProperties": false
}
```

## `add_controller_device`

- 描述：Add a top-level controller device to a project.
- 域：`projects`
- 风险等级：`dangerous`
- 工作流：`new_project_flow`
- 推荐前置工具：`create_project`, `open_project`
- 备注：Not part of the preferred existing-project POU editing flow.

输入字段：

```json
{
  "type": "object",
  "required": [
    "project_path",
    "device_name",
    "device_type",
    "device_id",
    "device_version"
  ],
  "properties": {
    "project_path": {
      "type": "string"
    },
    "device_name": {
      "type": "string"
    },
    "device_type": {
      "type": [
        "string",
        "integer"
      ]
    },
    "device_id": {
      "type": "string"
    },
    "device_version": {
      "type": "string"
    },
    "module": {
      "type": "string"
    }
  },
  "additionalProperties": false
}
```

## `create_program`

- 描述：Create a PRG in the selected container.
- 域：`pous`
- 风险等级：`caution`
- 工作流：`existing_project_edit_flow`, `new_project_flow`
- 推荐前置工具：`open_project`, `list_project_objects`

输入字段：

```json
{
  "type": "object",
  "required": [
    "project_path",
    "container_path",
    "name"
  ],
  "properties": {
    "project_path": {
      "type": "string"
    },
    "container_path": {
      "type": "string"
    },
    "name": {
      "type": "string"
    },
    "language": {
      "type": "string"
    }
  },
  "additionalProperties": false
}
```

## `create_function_block`

- 描述：Create a function block in the selected container.
- 域：`pous`
- 风险等级：`caution`
- 工作流：`existing_project_edit_flow`, `new_project_flow`
- 推荐前置工具：`open_project`, `list_project_objects`

输入字段：

```json
{
  "type": "object",
  "required": [
    "project_path",
    "container_path",
    "name"
  ],
  "properties": {
    "project_path": {
      "type": "string"
    },
    "container_path": {
      "type": "string"
    },
    "name": {
      "type": "string"
    },
    "language": {
      "type": "string"
    },
    "base_type": {
      "type": "string"
    },
    "interfaces": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "additionalProperties": false
}
```

## `create_function`

- 描述：Create a function in the selected container.
- 域：`pous`
- 风险等级：`caution`
- 工作流：`existing_project_edit_flow`, `new_project_flow`
- 推荐前置工具：`open_project`, `list_project_objects`

输入字段：

```json
{
  "type": "object",
  "required": [
    "project_path",
    "container_path",
    "name",
    "return_type"
  ],
  "properties": {
    "project_path": {
      "type": "string"
    },
    "container_path": {
      "type": "string"
    },
    "name": {
      "type": "string"
    },
    "return_type": {
      "type": "string"
    },
    "language": {
      "type": "string"
    }
  },
  "additionalProperties": false
}
```

## `read_textual_declaration`

- 描述：Read the textual declaration part of an object.
- 域：`pous`
- 风险等级：`safe`
- 工作流：`existing_project_edit_flow`
- 推荐前置工具：`open_project`

输入字段：

```json
{
  "type": "object",
  "required": [
    "project_path",
    "container_path",
    "object_name"
  ],
  "properties": {
    "project_path": {
      "type": "string"
    },
    "container_path": {
      "type": "string"
    },
    "object_name": {
      "type": "string"
    }
  },
  "additionalProperties": false
}
```

## `read_textual_implementation`

- 描述：Read the textual implementation part of an object.
- 域：`pous`
- 风险等级：`safe`
- 工作流：`existing_project_edit_flow`
- 推荐前置工具：`open_project`

输入字段：

```json
{
  "type": "object",
  "required": [
    "project_path",
    "container_path",
    "object_name"
  ],
  "properties": {
    "project_path": {
      "type": "string"
    },
    "container_path": {
      "type": "string"
    },
    "object_name": {
      "type": "string"
    }
  },
  "additionalProperties": false
}
```

## `replace_text_document`

- 描述：Replace a declaration or implementation document.
- 域：`pous`
- 风险等级：`caution`
- 工作流：`existing_project_edit_flow`
- 推荐前置工具：`open_project`

输入字段：

```json
{
  "type": "object",
  "required": [
    "project_path",
    "container_path",
    "object_name",
    "document_kind",
    "new_text"
  ],
  "properties": {
    "project_path": {
      "type": "string"
    },
    "container_path": {
      "type": "string"
    },
    "object_name": {
      "type": "string"
    },
    "document_kind": {
      "type": "string",
      "enum": [
        "declaration",
        "implementation"
      ]
    },
    "new_text": {
      "type": "string"
    }
  },
  "additionalProperties": false
}
```

## `append_text_document`

- 描述：Append text to the end of a declaration or implementation document.
- 域：`pous`
- 风险等级：`caution`
- 工作流：`existing_project_edit_flow`
- 推荐前置工具：`open_project`

输入字段：

```json
{
  "type": "object",
  "required": [
    "project_path",
    "container_path",
    "object_name",
    "document_kind",
    "text_to_append"
  ],
  "properties": {
    "project_path": {
      "type": "string"
    },
    "container_path": {
      "type": "string"
    },
    "object_name": {
      "type": "string"
    },
    "document_kind": {
      "type": "string",
      "enum": [
        "declaration",
        "implementation"
      ]
    },
    "text_to_append": {
      "type": "string"
    }
  },
  "additionalProperties": false
}
```

## `insert_text_document`

- 描述：Insert text into a declaration or implementation document at a fixed offset.
- 域：`pous`
- 风险等级：`caution`
- 工作流：`existing_project_edit_flow`
- 推荐前置工具：`open_project`

输入字段：

```json
{
  "type": "object",
  "required": [
    "project_path",
    "container_path",
    "object_name",
    "document_kind",
    "text_to_insert",
    "insertion_offset"
  ],
  "properties": {
    "project_path": {
      "type": "string"
    },
    "container_path": {
      "type": "string"
    },
    "object_name": {
      "type": "string"
    },
    "document_kind": {
      "type": "string",
      "enum": [
        "declaration",
        "implementation"
      ]
    },
    "text_to_insert": {
      "type": "string"
    },
    "insertion_offset": {
      "type": "integer"
    }
  },
  "additionalProperties": false
}
```
