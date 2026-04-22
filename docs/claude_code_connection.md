# Claude Code Connection

更新时间：2026-04-22

本文档固定 Claude Code 作为客户端时的连接方式。

## 1. 当前推荐方案

使用：

- Claude Code 项目级 MCP 配置
- `stdio` 传输
- PowerShell 启动脚本

仓库根目录已经提供可直接使用的配置文件：

- [.mcp.json](D:\工作资料\codesysAPItest\.mcp.json)

该配置会启动：

- [start_mcp_server.ps1](D:\工作资料\codesysAPItest\scripts\start_mcp_server.ps1)

## 2. 配置内容

当前项目使用的 Claude Code 项目级 MCP 配置如下：

```json
{
  "mcpServers": {
    "codesys-sp20": {
      "type": "stdio",
      "command": "powershell",
      "args": [
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "D:\\工作资料\\codesysAPItest\\scripts\\start_mcp_server.ps1"
      ]
    }
  }
}
```

## 3. 使用方式

方式一：直接使用项目里的 `.mcp.json`

1. 用 Claude Code 打开仓库目录：
   - `D:\工作资料\codesysAPItest`
2. Claude Code 读取项目级 MCP 配置
3. 允许它启动 `codesys-sp20`

方式二：使用 Claude Code CLI 手动添加项目级 server

可执行：

```powershell
claude mcp add-json --scope project codesys-sp20 "{\"type\":\"stdio\",\"command\":\"powershell\",\"args\":[\"-ExecutionPolicy\",\"Bypass\",\"-File\",\"D:\\工作资料\\codesysAPItest\\scripts\\start_mcp_server.ps1\"]}"
```

如果你已经保留了仓库里的 `.mcp.json`，通常优先方式一就够了。

## 4. 连接后应该看到什么

连接成功后，Claude Code 应该能发现当前阶段的 MCP tools，例如：

- `open_project`
- `create_program`
- `create_function_block`
- `create_function`
- `read_textual_declaration`
- `read_textual_implementation`
- `replace_text_document`
- `append_text_document`
- `insert_text_document`

## 5. 当前推荐使用边界

当前最稳妥的真实使用方式仍然是：

- 用户先手工准备 SP20 真实项目
- 在自然语言里明确给出绝对路径 `project_path`
- Claude Code 通过 MCP tools 操作 POU

当前第一阶段不建议默认依赖：

- 自动创建工程
- 自动插入控制器
- EtherCAT 扫描

## 6. 推荐的第一条验证指令

连接成功后，可以先让 Claude Code 执行类似请求：

```text
在项目 D:\工作资料\test\test_pou_create.project 中创建一个 ST 程序，名称为 DemoMain，并在实现区写入初始化代码。
```

如果这条链路成功，说明：

- Claude Code 已经连接到 MCP server
- MCP server 已经能调用真实 SP20 适配层
- 第一阶段的 POU 主线可用
