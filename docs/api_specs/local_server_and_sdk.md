# Local Server And SDK

当前仓库提供一个离线可测试的本地装配方案：

- server: `codesys_mcp_server.server.ServerApplication`
- runtime: `codesys_mcp_server.server.ServerRuntime`
- client: `codesys_client_sdk.LocalCodesysMcpClient`
- demo backend: `codesys_mcp_server.server.InMemoryCodesysBackend`
- CLI: `codesys-mcp-local`

## Server

创建本地 server：

```python
from codesys_mcp_server.server import create_server_application

app = create_server_application(backend)
tools = app.list_tools()
result = app.call_tool("create_program", {...}, request_id="req-001")
```

`backend` 需要实现当前 phase-1 工具会用到的方法，例如：

- `create`
- `open`
- `save`
- `save_as`
- `add_controller`
- `create_program`
- `create_function_block`
- `create_function`
- `read_text_document`
- `replace_text_document`
- `append_text_document`
- `insert_text_document`

## Runtime

创建标准化本地 runtime：

```python
from codesys_mcp_server.server import create_runtime

runtime = create_runtime()
tools = runtime.list_tools()
result = runtime.call_tool(
    name="create_program",
    arguments={
        "project_path": "D:/Projects/demo.project",
        "container_path": "Application",
        "name": "MainProgram",
    },
)
```

当前 runtime 负责：

- 读取 `ServerSettings`
- 初始化日志
- 创建默认 backend 对应的 `ServerApplication`
- 提供 `list_tools`、`call_tool`、`serve_stdio`、`serve_jsonl`

当前 stdio 入口采用：

- JSON-RPC 风格消息结构
- 每行一个 JSON 消息的简化传输形式
- `serve-jsonl` 仅作为兼容别名保留

## Client SDK

创建本地 client：

```python
from codesys_client_sdk import LocalCodesysMcpClient

client = LocalCodesysMcpClient(app)
result = client.create_program(
    project_path="D:/Projects/demo.project",
    container_path="Application",
    name="MainProgram",
)
```

当前 client SDK 提供：

- `list_tools`
- `call_tool`
- `create_project`
- `open_project`
- `save_project`
- `add_controller_device`
- `create_program`
- `create_function_block`
- `create_function`
- `read_textual_declaration`
- `read_textual_implementation`
- `replace_text_document`
- `append_text_document`
- `insert_text_document`

## CLI

列出工具：

```bash
codesys-mcp-local list-tools
```

调用工具：

```bash
codesys-mcp-local call-tool create_project --arguments "{\"project_path\":\"D:/Projects/demo.project\",\"project_mode\":\"empty\"}"
```

启动首选 stdio 协议入口：

```bash
codesys-mcp-local serve-stdio
```

兼容旧入口：

```bash
codesys-mcp-local serve-jsonl
```

示例消息：

```json
{"jsonrpc":"2.0","id":"init-1","method":"initialize","params":{}}
{"jsonrpc":"2.0","id":"tools-1","method":"tools/list"}
{"jsonrpc":"2.0","id":"call-1","method":"tools/call","params":{"name":"create_project","arguments":{"project_path":"D:/Projects/demo.project","project_mode":"empty","set_as_primary":true}}}
```

配置运行参数：

```bash
codesys-mcp-local --log-level DEBUG --log-json list-tools
```

也可以通过环境变量控制默认配置：

```bash
set CODESYS_MCP_BACKEND=in_memory
set CODESYS_MCP_LOG_LEVEL=DEBUG
set CODESYS_MCP_LOG_JSON=true
```
