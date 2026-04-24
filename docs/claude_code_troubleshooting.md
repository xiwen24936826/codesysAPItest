# Claude Code 常见失败排查表

更新时间：2026-04-24

## 1. MCP Server 显示 `failed` 或无法连接

先检查：

1. 仓库根目录是否存在 [.mcp.json](D:\工作资料\codesysAPItest\.mcp.json)
2. 启动脚本是否存在 [start_mcp_server.ps1](D:\工作资料\codesysAPItest\scripts\start_mcp_server.ps1)
3. Claude Code 是否在项目目录 `D:\工作资料\codesysAPItest` 中打开

建议命令：

```powershell
cd "D:\工作资料\codesysAPItest"
claude mcp list
claude mcp get codesys-sp20
```

## 2. MCP 工具未授权

典型现象：

- `mcp__codesys-sp20__open_project` 未授权
- Claude 弹出工具权限请求

解决办法：

1. 配置 `.claude/settings.json`
2. 预先允许：
   - `mcp__codesys-sp20`
3. 把真实项目目录加入：
   - `D:\test`

## 3. 中文项目路径导致 `open_project` 失败

典型现象：

- 项目明明存在
- 但真实后端返回路径被破坏成 `????`

当前结论：

- 真实 SP20 自动化链路对**中文工程路径**仍然不稳定
- 所以项目路径继续建议使用 ASCII-only 路径

推荐做法：

- 使用 `D:\test\test_pou_create.project`
- 不要把主工程放在中文目录下做自动化调用

## 4. `container_path` 错误

推荐顺序：

1. `open_project`
2. `list_project_objects` 或 `find_project_objects`
3. 根据真实返回结果定位 `Application`
4. 再创建 POU

补充规则：

- 递归扫描优先看 `can_browse`
- `is_folder` 只保留兼容意义

## 5. 中文注释是否会乱码

最新结论已经更新：

- 在 **ASCII 项目路径** 下
- 真实 SP20 后端对 **UTF-8 中文注释** 已完成一次受控实验
- 声明区和实现区中文注释写入后再读回，结果一致，没有出现 `?`

所以当前规则是：

- 工程路径：继续 ASCII-only
- 源码文本：允许 UTF-8 中文注释

## 6. 变量声明遗漏导致预编译报错

当前工具链已经做的保护：

- 写实现区前会校验声明区
- 如果实现区引用了未声明标识符，会直接拒绝写入

推荐客户端顺序：

1. 先生成/补齐声明区
2. 再写实现区
3. 必要时先 `read_textual_declaration`

## 7. 终端中文显示乱码

这通常不是 Markdown 文件坏了，而是 PowerShell 显示编码问题。

建议先执行：

```powershell
chcp 65001
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
```

查看文档时显式指定：

```powershell
Get-Content -Raw -Encoding UTF8 "D:\工作资料\codesysAPItest\docs\codex_client_handbook.md"
```

查看工具目录：

```powershell
cd "D:\工作资料\codesysAPItest"
$env:PYTHONPATH="$PWD\src"
python -m codesys_mcp_server.server.cli --backend real_ide list-tools
```
