# Claude Code Connection

更新时间：2026-04-24

本文档固定 Claude Code 作为客户端时的连接方式。  
客户端工具选择、扫描顺序和误调用规避规则以
[codex_client_handbook.md](D:\工作资料\codesysAPItest\docs\codex_client_handbook.md)
为主。本文件只保留连接方式、最小启动流程和排查入口。

## 1. 当前推荐方案

使用：

- Claude Code 项目级 MCP 配置
- `stdio` 传输
- PowerShell 启动脚本

仓库根目录已经提供：

- [.mcp.json](D:\工作资料\codesysAPItest\.mcp.json)
- [start_mcp_server.ps1](D:\工作资料\codesysAPItest\scripts\start_mcp_server.ps1)

当前仓库还应配合使用：

- `.claude/settings.json`

它用于：

- 预先允许 `mcp__codesys-sp20`
- 允许 Claude Code 访问真实项目目录，例如 `D:\test`

## 2. 最小启动步骤

1. 把真实项目放到英文或 ASCII 路径，例如：
   - `D:\test\test_pou_create.project`
2. 用 Claude Code 打开仓库目录：
   - `D:\工作资料\codesysAPItest`
3. 确认 MCP server `codesys-sp20` 状态为 `Connected`
4. 直接发送自然语言请求

## 3. 当前重要边界

- 真实项目**路径**继续优先使用 ASCII-only 路径
- 真实项目中的**源码文本**现在允许 UTF-8 中文注释
- 因此：
  - 可以要求 Claude 写中文注释
  - 但不要把工程放回中文目录路径

## 4. 推荐自然语言示例

```text
在项目 D:\test\test_pou_create.project 中创建一个 ST 语言的 Function Block，名称为 PID_Controller_FB。创建前先扫描或查找真实 Application 容器；声明区补齐变量；实现区写入完整 PID 逻辑；写入后保存项目。
```

## 5. PowerShell UTF-8 显示建议

如果你在终端里想看中文表格或 Markdown 输出，先执行：

```powershell
chcp 65001
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
```

再查看工具目录：

```powershell
cd "D:\工作资料\codesysAPItest"
$env:PYTHONPATH="$PWD\src"
python -m codesys_mcp_server.server.cli --backend real_ide list-tools
```

## 6. 相关文档

- [codex_client_handbook.md](D:\工作资料\codesysAPItest\docs\codex_client_handbook.md)
- [tool_catalog.md](D:\工作资料\codesysAPItest\docs\api_specs\tool_catalog.md)
- [client_workflows.md](D:\工作资料\codesysAPItest\docs\client_workflows.md)
- [claude_code_troubleshooting.md](D:\工作资料\codesysAPItest\docs\claude_code_troubleshooting.md)
