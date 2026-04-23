# Claude Code Connection

## 2026-04-23 Note

Claude Code should now prefer this tool order when creating or editing POU objects:

1. `open_project`
2. `list_project_objects`
3. select the returned nested `Application` path
4. create the target POU
5. read or write declaration and implementation text

The service layer still accepts `/` or `Application` and tries to auto-resolve the
real nested container, but the explicit scan-first workflow is now the recommended
path for reliable demos and client integrations.

更新时间：2026-04-23

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

当前仓库还应配合使用：

- `.claude/settings.json`

它用于：

- 预先允许 `mcp__codesys-sp20`
- 允许 Claude Code 访问真实项目目录，例如 `D:\test`

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

## 4. 最小操作说明

如果你只想用最少步骤开始联调，按下面做：

1. 把真实项目放到纯英文或 ASCII 路径下  
   推荐：
   - `D:\test\test_pou_create.project`

2. 确认仓库里已经有：
   - [.mcp.json](D:\工作资料\codesysAPItest\.mcp.json)
   - [settings.json](D:\工作资料\codesysAPItest\.claude\settings.json)

3. 用 Claude Code 打开仓库目录：
   - `D:\工作资料\codesysAPItest`

4. 在 Claude Code 里确认 `codesys-sp20` 已连接  
   预期状态：
   - MCP server 状态为 `Connected`

5. 直接发送自然语言请求，例如：

```text
在项目 D:\test\test_pou_create.project 中创建一个 ST 程序，名称为 DemoMain，并在实现区写入一行注释和一行赋值。
```

6. 如果 Claude Code 仍然尝试访问别的目录或弹权限提示：
   - 先检查 `.claude/settings.json` 是否已包含：
     - `mcp__codesys-sp20`
     - `D:\test`

这就是当前阶段最小可用流程。

补充说明：

- 当前服务端会在调用方传入 `/` 或 `Application` 时，尽量自动解析到真实项目里的嵌套 `Application` 容器。
- 当前真实后端建议源码和注释使用 ASCII-only，避免中文注释写入后乱码。
- 如果让 Claude Code 生成实现区代码，最好同时明确要求它先补全声明区变量，再写实现区逻辑。

## 5. 连接后应该看到什么

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

## 6. 当前推荐使用边界

当前最稳妥的真实使用方式仍然是：

- 用户先手工准备 SP20 真实项目
- 在自然语言里明确给出绝对路径 `project_path`
- 真实项目路径优先使用纯英文或 ASCII 路径
- Claude Code 通过 MCP tools 操作 POU

当前第一阶段不建议默认依赖：

- 自动创建工程
- 自动插入控制器
- EtherCAT 扫描

## 7. 推荐的第一条验证指令

连接成功后，可以先让 Claude Code 执行类似请求：

```text
在项目 D:\test\test_pou_create.project 中创建一个 ST 程序，名称为 DemoMain，并在实现区写入初始化代码。
```

更稳妥的写法是：

```text
在项目 D:\test\test_pou_create.project 中创建一个 ST 程序，名称为 DemoMain。请使用 ASCII-only 注释和代码；如果实现区使用到变量，先补全声明区变量；然后再写实现区逻辑。
```

如果这条链路成功，说明：

- Claude Code 已经连接到 MCP server
- MCP server 已经能调用真实 SP20 适配层
- 第一阶段的 POU 主线可用
