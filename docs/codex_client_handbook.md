# Codex Client Handbook

本手册是当前仓库的主客户端使用规则文档。

- 阶段范围和稳定边界以 [current_phase_plan.md](D:\工作资料\codesysAPItest\docs\current_phase_plan.md) 为准
- Claude Code 的连接细节见 [claude_code_connection.md](D:\工作资料\codesysAPItest\docs\claude_code_connection.md)
- 工具单一权威索引见 [tool_catalog.md](D:\工作资料\codesysAPItest\docs\api_specs\tool_catalog.md)
- 工作流分组视图见 [client_workflows.md](D:\工作资料\codesysAPItest\docs\client_workflows.md)

## 1. 当前可靠能力

优先使用以下工具：

- `open_project`
- `list_project_objects`
- `find_project_objects`
- `scan_network_devices`
- `create_program`
- `create_function_block`
- `create_function`
- `read_textual_declaration`
- `read_textual_implementation`
- `replace_text_document`
- `append_text_document`
- `insert_text_document`

## 2. 当前前置条件

- `project_path` 必须是绝对路径。
- 真实项目路径当前仍优先使用纯英文或 ASCII 路径，例如 `D:\test\test_pou_create.project`。
- `container_path` 是项目内逻辑路径，例如 `Application`。
- 第一阶段允许用户先手工准备 SP20 真实项目。
- 当目标是“编辑已有工程中的 POU”时，客户端不应把 `create_project` 当作兜底方案。

## 3. 推荐任务拆解顺序

当用户说“在某个项目中创建或修改 POU”时，推荐顺序是：

1. 确认 `project_path`
2. 调用 `open_project`
3. 先调用 `list_project_objects` 或 `find_project_objects`
4. 根据返回结果定位真实 `Application` 容器
5. 选择创建工具：
   - `create_program`
   - `create_function_block`
   - `create_function`
6. 读取已有文本：
   - `read_textual_declaration`
   - `read_textual_implementation`
7. 根据修改意图选择：
   - `replace_text_document`
   - `append_text_document`
   - `insert_text_document`
8. 最后 `save_project`

补充约束：

- 客户端递归扫描时优先看 `can_browse`。
- `is_folder` 只保留兼容意义，不能再作为主递归条件。
- `child_count` 只是辅助信息，不是是否继续扫描的判断依据。
- `is_device` 和 `device_identification` 可辅助识别控制器、总线和设备节点。
- 如果调用方传入 `/` 或 `Application`，服务端仍会尝试自动解析到真实项目里的嵌套 `Application`，但这是 fallback，不是主流程。

## 4. 文本工具语义

- `replace_text_document`：用新全文覆盖原文
- `append_text_document`：只在末尾追加
- `insert_text_document`：在指定字符偏移位置插入

不要把 `append_text_document` 当成“任意位置插入”工具使用。

## 5. UTF-8 与路径规则

当前结论已经更新为：

- 真实项目**路径**仍建议使用 ASCII-only 路径
- 真实项目中的**源码文本**现在允许使用 UTF-8 注释和字符串

已完成的真实实验结论：

- 在 ASCII 项目路径下
- 通过真实 SP20 后端创建临时 FB
- 写入中文声明区注释和中文实现区注释
- 再读回 declaration / implementation
- 回读结果与写入内容一致，没有出现 `?` 或乱码

因此：

- “项目路径 ASCII-only” 继续保留
- “源码和注释必须 ASCII-only” 已不再作为当前规则

## 6. 当前不可靠或暂缓能力

- `scan_ethercat_devices` 暂缓
- `create_project / add_controller_device` 属于高风险工具
- 自动建工程链路仍可能受 SP20 环境波动影响

对“在已有工程里生成 POU”这类任务：

- 优先走现有工程编辑流
- 不要误用 `create_project`
- 不要把 `add_controller_device` 当作修复容器定位失败的手段

## 7. 自然语言到工具的大致映射

- “帮我创建一个 PRG”
  - `open_project`
  - `list_project_objects`
  - `create_program`
- “创建一个 FB，名字叫 MotorControl”
  - `open_project`
  - `list_project_objects`
  - `create_function_block`
- “读取这个 POU 的声明区”
  - `open_project`
  - `read_textual_declaration`
- “把实现区改成下面这段代码”
  - `open_project`
  - `read_textual_declaration`
  - `replace_text_document`
- “在实现区最后再加一段”
  - `open_project`
  - `append_text_document`
- “在实现区开头插入一行注释”
  - `open_project`
  - `insert_text_document`

## 8. 终端显示建议

如果你在 PowerShell 中查看 CLI 表格或 Markdown 文档，建议先执行：

```powershell
chcp 65001
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
```

查看中文 Markdown 时建议显式指定：

```powershell
Get-Content -Raw -Encoding UTF8 "D:\工作资料\codesysAPItest\docs\codex_client_handbook.md"
```
