# Claude Code 常见失败排查表

更新时间：2026-04-23

本文档用于快速排查 Claude Code 作为客户端连接本项目时的常见失败情况。

## 1. MCP Server 显示 failed 或无法连接

典型现象：

- `Manage MCP servers` 里看到：
  - `codesys-sp20 · × failed`
- `claude mcp list` 显示：
  - `Failed to connect`

优先检查：

1. 仓库根目录是否存在：
   - [.mcp.json](D:\工作资料\codesysAPItest\.mcp.json)
2. 启动脚本是否存在：
   - [start_mcp_server.ps1](D:\工作资料\codesysAPItest\scripts\start_mcp_server.ps1)
3. Claude Code 是否在项目目录中打开：
   - `D:\工作资料\codesysAPItest`

建议命令：

```powershell
cd "D:\工作资料\codesysAPItest"
claude mcp list
claude mcp get codesys-sp20
```

当前已知正常状态：

- `codesys-sp20: ... ✓ Connected`

## 2. MCP 工具未授权

典型现象：

- `mcp__codesys-sp20__open_project` 未授权
- `mcp__codesys-sp20__append_text_document` 未授权
- Claude 输出：
  - `Claude requested permissions to use ...`

原因：

- 这是 Claude Code 自身的工具权限策略
- 不是 MCP server 坏了
- 也不是缺少 `skills.md`

解决办法：

1. 在项目中配置：
   - [settings.json](D:\工作资料\codesysAPItest\.claude\settings.json)
2. 预先允许：
   - `mcp__codesys-sp20`

当前推荐配置：

```json
{
  "permissions": {
    "allow": [
      "mcp__codesys-sp20"
    ],
    "defaultMode": "default"
  },
  "additionalDirectories": [
    "D:\\test"
  ]
}
```

说明：

- `mcp__codesys-sp20` 会放行该 MCP server 下的整组工具
- `additionalDirectories` 允许 Claude 的内置工具访问真实项目目录

## 3. 中文路径项目打开失败

典型现象：

- 在自然语言里指定：
  - `D:\工作资料\test\test_pou_create.project`
- `open_project` 返回：
  - `Unexpected error while opening project.`
- 服务端真实异常里出现：
  - `D:/????/test/test_pou_create.project`

原因：

- 真实 SP20 / CODESYS 后端当前对非 ASCII 路径不稳定
- 中文目录会在自动化链路里被破坏成 `????`

已验证结论：

- 中文路径项目会失败
- 同一个项目复制到英文路径后，`open_project` 成功

推荐做法：

1. 把 `.project` 放到纯英文路径
2. 优先使用：
   - `D:\test\test_pou_create.project`

不推荐当前阶段继续使用：

- `D:\工作资料\...`

## 4. `container_path` 错误

典型现象：

- `Field 'container_path' is required.`
- Claude 传了空字符串：
  - `""`
- 或者传了项目里并不存在的逻辑路径

原因：

- 当前服务层要求 `container_path` 必填
- 某些真实项目根节点没有 `Application`
- 你的真实项目已经验证过顶层对象是：
  - `MyController`
  - `Project Information`
  - `Project Settings`
  - `__VisualizationStyle`

当前已验证可用规则：

- 对这个项目，创建 POU 时可用：
  - `container_path="/" `

推荐做法：

1. 如果知道项目里有 `Application`
   - 用 `Application`
2. 如果项目顶层没有 `Application`
   - 用 `/`

当前第一阶段对真实项目最稳的默认值是：

```text
container_path = /
```

## 5. Claude 理解了自然语言，但中途停住

典型现象：

- 已经调用了 `open_project`
- 已经创建了 `create_program`
- 然后在 `append_text_document` 或别的工具处停住

常见原因：

1. 又遇到新的 MCP 工具权限请求
2. 路径是中文路径
3. 生成的 `container_path` 不正确

排查顺序：

1. 先看是否弹了新的工具授权
2. 再看项目路径是否为纯英文
3. 再看 Claude 调用时的 `container_path` 是否是 `/` 或 `Application`

## 6. Claude 想自己猜项目结构，结果越走越偏

典型现象：

- 先试图 `Glob` 项目文件
- 再试图 `Bash` 到项目目录
- 然后因为目录权限受限而偏离主线

原因：

- Claude 会尝试用内置工具先探路
- 如果目标目录不在 `additionalDirectories` 里，就会被限制

解决办法：

1. 在自然语言里直接给出绝对路径
2. 在 `.claude/settings.json` 里加入：
   - `D:\test`
3. 在提示里明确要求：
   - 直接使用 MCP tools，不要先用 Bash/Glob 试探

推荐提示词：

```text
在项目 D:\test\test_pou_create.project 中创建一个 ST 程序，名称为 DemoMain。请直接使用可用的 MCP tools 完成，不要先用 Bash 或 Glob 探测项目。
```

## 7. 当前最稳的最小联调方式

推荐条件：

1. 项目路径为英文路径：
   - `D:\test\test_pou_create.project`
2. Claude Code 已连接：
   - `codesys-sp20`
3. `.claude/settings.json` 已允许：
   - `mcp__codesys-sp20`
4. 真实项目目录已加入：
   - `D:\test`

推荐首条自然语言：

```text
在项目 D:\test\test_pou_create.project 中创建一个 ST 程序，名称为 DemoMain，并在实现区写入一行注释和一行赋值。请直接使用可用的 MCP tools 完成，不要先用 Bash 或 Glob 探测项目。
```

## 8. 一句话总结

当前 Claude Code 联调最常见的 3 个根因是：

1. MCP 工具未授权
2. 项目路径含中文
3. `container_path` 不正确

只要先解决这 3 个点，第一阶段的 POU 自然语言链路就是可用的。
