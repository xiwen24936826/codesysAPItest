# MCP Client Connection

更新时间：2026-04-22

本文档用于固定当前项目的客户端连接方式。

## 1. 推荐连接方案

当前统一推荐使用：

- `stdio` 传输
- PowerShell 启动脚本
- `real_ide` backend

唯一推荐启动入口：

- [start_mcp_server.ps1](D:\工作资料\codesysAPItest\scripts\start_mcp_server.ps1)

这意味着：

- 不管客户端是谁，只要支持通过 `stdio` 启动一个本地进程并收发 JSON-RPC/MCP 风格消息
- 都应优先连接这个脚本

## 2. 为什么固定成这一种方式

当前仓库已经验证通过的链路是：

- `ServerRuntime`
- `tools/list`
- `tools/call`
- 真实 SP20 适配层
- 手工准备的真实项目路径

`stdio` 是当前最稳妥、最通用的本地连接方式，因为它：

- 不依赖额外 HTTP 服务
- 不依赖固定端口
- 更适合本机 IDE 自动化场景
- 更容易被不同 MCP 客户端复用

## 3. 启动方式

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\start_mcp_server.ps1"
```

默认行为：

- 使用 `python`
- 使用 `real_ide` backend
- 自动设置：
  - `PYTHONPATH=<repo>\src`
  - `CODESYS_MCP_BACKEND=real_ide`
  - `CODESYS_MCP_BRIDGE_SCRIPT_PATH=<repo>\src\codesys_mcp_server\core\codesys_bridge.py`
- 启动：
  - `python -m codesys_mcp_server.server.cli --backend real_ide --bridge-script-path <...> serve-stdio`

## 4. 可选参数

如果需要指定 Python 解释器：

```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\start_mcp_server.ps1" -PythonExe "D:\python.3.13.7\python.exe"
```

如果只想做离线演示，不接真实 SP20：

```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\start_mcp_server.ps1" -Backend in_memory
```

如果需要 JSON 日志：

```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\start_mcp_server.ps1" -JsonLogs
```

## 5. 客户端侧应该如何配置

客户端侧只需要知道 3 件事：

1. 这是一个本地 `stdio` MCP server
2. 启动命令是 PowerShell
3. PowerShell 要执行 `scripts/start_mcp_server.ps1`

抽象成通用配置含义就是：

- `command`: `powershell`
- `args`:
  - `-ExecutionPolicy`
  - `Bypass`
  - `-File`
  - `D:\工作资料\codesysAPItest\scripts\start_mcp_server.ps1`

如果某个客户端支持“工作目录”配置，建议设置为：

- `D:\工作资料\codesysAPItest`

## 6. 当前适用边界

当前这条固定连接方式主要面向第一阶段已验证能力：

- `open_project`
- `create_program`
- `create_function_block`
- `create_function`
- `read_textual_declaration`
- `read_textual_implementation`
- `replace_text_document`
- `append_text_document`
- `insert_text_document`

当前最稳妥的真实使用方式仍然是：

- 用户手工准备好真实项目
- 客户端通过 MCP server 调用 POU 工具
- 项目路径使用绝对路径

## 7. 不同客户端的处理原则

当前先不把连接方式绑定到某一个特定客户端格式。

原因是：

- Codex、Claude Code、VSCode Copilot 等工具的具体 MCP 配置文件格式可能不同
- 但它们最终都需要：
  - 一个本地命令
  - 一组启动参数
  - 一个 stdio 通道

所以当前项目层面固定的是：

- 连接协议：`stdio`
- 启动入口：`scripts/start_mcp_server.ps1`
- backend：`real_ide`

如果你后面确定要优先接某一个具体客户端，再单独补该客户端的配置样例即可。
