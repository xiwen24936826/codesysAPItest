# 第一阶段 MCP 工具输入输出规范

更新时间：2026-04-22

本文定义第一阶段 MCP 工具的统一输入输出规范，用于服务端实现、客户端接入和测试验证。当前阶段以 POU 优先交付为主，允许基于用户手工准备好的真实 SP20 项目进行联调。

## 1. 当前范围

第一阶段重点交付：

1. `create_program`
2. `create_function_block`
3. `create_function`
4. `read_textual_declaration`
5. `read_textual_implementation`
6. `replace_text_document`
7. `append_text_document`
8. `insert_text_document`

继续保留但不作为本阶段阻塞项：

1. `create_project`
2. `open_project`
3. `save_project`
4. `add_controller_device`

暂不纳入本阶段：

1. `scan_ethercat_devices`

## 2. 路径与对象定位约定

- 文件系统路径一律使用绝对路径。
- `project_path`、`target_project_path` 都必须是绝对路径。
- `container_path` 是项目内逻辑路径，不是文件系统路径。
- `container_path` 使用 `/` 作为分隔符，例如 `Application`、`Application/POUs`。
- `object_name` 表示目标 POU 名称。
- `document_kind` 仅允许：
  - `declaration`
  - `implementation`

## 3. 统一响应格式

所有工具都返回统一结构：

```json
{
  "ok": true,
  "tool": "create_program",
  "data": {},
  "error": null,
  "meta": {
    "timestamp": "2026-04-22T10:30:00+08:00",
    "request_id": "6c296c6b-9c6f-4e56-a760-c98b30c3aaf7",
    "duration_ms": 120
  }
}
```

失败示例：

```json
{
  "ok": false,
  "tool": "insert_text_document",
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Field 'insertion_offset' must be a non-negative integer.",
    "details": {
      "field": "insertion_offset",
      "value": -1
    }
  },
  "meta": {
    "timestamp": "2026-04-22T10:31:12+08:00",
    "request_id": "4fc482bf-4b50-44bf-b527-1477d36a9285",
    "duration_ms": 8
  }
}
```

## 4. 错误码

第一阶段统一使用以下错误码：

- `VALIDATION_ERROR`
- `PROJECT_NOT_FOUND`
- `PROJECT_IN_USE`
- `PROJECT_NOT_OPEN`
- `SAVE_FAILED`
- `DEVICE_TYPE_NOT_FOUND`
- `DEVICE_INSERT_FAILED`
- `POU_CREATE_FAILED`
- `POU_CONTAINER_NOT_FOUND`
- `POU_NOT_FOUND`
- `TEXT_DOCUMENT_NOT_FOUND`
- `INTERNAL_ERROR`

## 5. 项目工具

### 5.1 `create_project`

用途：

- 创建一个新的 `.project`

输入：

```json
{
  "project_path": "D:/Projects/demo.project",
  "project_mode": "empty",
  "set_as_primary": true
}
```

说明：

- 当前第一阶段仅将 `project_mode="empty"` 视为真实实现范围。
- `template` 仍保留字段，但不作为当前联调主线。

### 5.2 `open_project`

用途：

- 打开已有项目

输入：

```json
{
  "project_path": "D:/Projects/demo.project"
}
```

### 5.3 `save_project`

用途：

- 保存当前项目或另存为

输入：

```json
{
  "project_path": "D:/Projects/demo.project",
  "save_mode": "save"
}
```

说明：

- `save_mode` 允许 `save` 和 `save_as`
- 当 `save_mode="save_as"` 时必须提供 `target_project_path`

### 5.4 `add_controller_device`

用途：

- 向项目根节点插入控制器设备

输入：

```json
{
  "project_path": "D:/Projects/demo.project",
  "device_name": "M310_Controller",
  "device_type": 4102,
  "device_id": "1044 0006",
  "device_version": "3.5.20.55",
  "module": null
}
```

说明：

- `device_type/device_id/device_version` 必须来自目标 IDE 设备库的真实元数据。

## 6. POU 创建工具

### 6.1 `create_program`

用途：

- 在指定容器中创建 PRG

输入：

```json
{
  "project_path": "D:/Projects/demo.project",
  "container_path": "Application",
  "name": "MainProgram",
  "language": "ST"
}
```

成功输出：

```json
{
  "project_path": "D:/Projects/demo.project",
  "container_path": "Application",
  "name": "MainProgram",
  "object_type": "program",
  "language": "ST"
}
```

### 6.2 `create_function_block`

用途：

- 在指定容器中创建 FB

输入：

```json
{
  "project_path": "D:/Projects/demo.project",
  "container_path": "Application",
  "name": "MotorControl",
  "language": "ST",
  "base_type": null,
  "interfaces": []
}
```

### 6.3 `create_function`

用途：

- 在指定容器中创建 Function

输入：

```json
{
  "project_path": "D:/Projects/demo.project",
  "container_path": "Application",
  "name": "CalculateSpeed",
  "return_type": "REAL",
  "language": "ST"
}
```

## 7. 文本读写工具

### 7.1 `read_textual_declaration`

用途：

- 读取目标对象声明区文本

输入：

```json
{
  "project_path": "D:/Projects/demo.project",
  "container_path": "Application",
  "object_name": "MainProgram"
}
```

### 7.2 `read_textual_implementation`

用途：

- 读取目标对象实现区文本

输入：

```json
{
  "project_path": "D:/Projects/demo.project",
  "container_path": "Application",
  "object_name": "MainProgram"
}
```

### 7.3 `replace_text_document`

用途：

- 用新全文整体替换目标文档内容

输入：

```json
{
  "project_path": "D:/Projects/demo.project",
  "container_path": "Application",
  "object_name": "MainProgram",
  "document_kind": "implementation",
  "new_text": "Counter := 1;"
}
```

说明：

- `document_kind="declaration"` 表示改声明区
- `document_kind="implementation"` 表示改实现区
- 允许将 `new_text` 设为空字符串

### 7.4 `append_text_document`

用途：

- 在目标文档末尾追加文本

输入：

```json
{
  "project_path": "D:/Projects/demo.project",
  "container_path": "Application",
  "object_name": "MainProgram",
  "document_kind": "implementation",
  "text_to_append": "\nCounter := Counter + 1;"
}
```

说明：

- 本工具只负责末尾追加
- 不负责任意位置插入

### 7.5 `insert_text_document`

用途：

- 在目标文档指定位置插入文本

输入：

```json
{
  "project_path": "D:/Projects/demo.project",
  "container_path": "Application",
  "object_name": "MainProgram",
  "document_kind": "implementation",
  "text_to_insert": "// inserted by Codex\n",
  "insertion_offset": 0
}
```

说明：

- 第一阶段只支持单一定位方式：字符偏移量 `insertion_offset`
- 偏移量从 0 开始
- 不同时支持行号、锚点文本等多种定位策略

## 8. 真实联调策略

当前真实联调按两阶段推进：

### 阶段 A

- 允许基于用户手工准备好的真实 SP20 项目恢复联调
- 用户提供真实项目的绝对路径
- 集成测试优先复制该项目到临时副本后再执行，避免与手工打开的源项目发生占用冲突
- 优先验证：
  - `open_project`
  - `create_program`
  - `create_function_block`
  - `create_function`
  - `read_textual_declaration`
  - `read_textual_implementation`
  - `replace_text_document`
  - `append_text_document`
  - `insert_text_document`

### 阶段 B

- 待 `create/open/save/add_controller_device` 自动化链路稳定后
- 再恢复“自动建项目 + 插入控制器 + 创建 POU”的完整真实链路
