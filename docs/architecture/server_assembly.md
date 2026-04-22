# Server Assembly

当前离线可开发阶段，MCP server 主体采用三层装配：

1. `services/`
   - 负责具体业务能力
   - 统一做参数校验、错误映射和结构化响应

2. `tools/`
   - 负责把 service 组装成可暴露的 tool registry
   - 定义 tool name、description 和最小 input schema

3. `server/`
   - 提供本地 in-process 的 `ServerApplication`
   - 负责 `list_tools` 和 `call_tool` 分发

当前实现不依赖外部 MCP 库，目的是先稳定：

- tool 注册
- 调用分发
- client SDK 调用链
- 本地离线 backend
- 本地 CLI 验证入口
- 标准化 runtime 启动入口
- 配置加载与日志初始化

后续如果接入正式 transport，例如 stdio 或 HTTP，可以继续复用这一层。

## Runtime

当前标准化入口位于 `server/runtime.py`：

- `ServerRuntime`
  - 基于 `ServerSettings` 构建本地运行时
  - 统一初始化日志
  - 统一构建 backend 对应的 `ServerApplication`
- `create_runtime()`
  - 支持直接使用环境变量创建默认运行时

当前 runtime 提供三类能力：

- `list_tools()`
- `call_tool()`
- `serve_stdio()`
- `serve_jsonl()`

其中：

- `serve_stdio()` 是当前首选的 stdio 入口
- 协议形态采用 JSON-RPC 风格消息包
- 传输层暂时仍使用“每行一个 JSON 消息”的简化形式
- `serve_jsonl()` 仅作为兼容别名保留

当前支持的核心消息包括：

- `initialize`
- `ping`
- `tools/list`
- `tools/call`
- `shutdown`
- `notifications/initialized`

## Config And Logging

当前配置层位于 `config/settings.py`，日志层位于 `logging/setup.py`。

配置模型：

- `ServerSettings`
  - `backend_mode`
  - `log_level`
  - `log_json`

环境变量约定：

- `CODESYS_MCP_BACKEND`
- `CODESYS_MCP_LOG_LEVEL`
- `CODESYS_MCP_LOG_JSON`

日志初始化约定：

- 默认输出到控制台
- 支持普通文本日志
- 支持最小 JSON 日志
- 由 runtime 在启动时统一配置，避免各模块各自初始化根日志器
