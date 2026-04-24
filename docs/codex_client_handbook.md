# Codex Client Handbook

本手册现在是仓库的主客户端使用规则文档。

- 阶段范围和稳定边界以 [current_phase_plan.md](D:\工作资料\codesysAPItest\docs\current_phase_plan.md) 为准
- 本文档只保留客户端应如何选工具、如何递归扫描、以及如何避免误调用
- Claude Code 的连接细节放在 [claude_code_connection.md](D:\工作资料\codesysAPItest\docs\claude_code_connection.md)
- 工具的单一权威索引见 [tool_catalog.md](D:\工作资料\codesysAPItest\docs\api_specs\tool_catalog.md)
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

- 项目文件路径必须是绝对路径。
- 项目路径优先使用纯英文或 ASCII 路径。
- `container_path` 是项目内逻辑路径，例如 `Application`。
- 在第一阶段，允许用户手工在 SP20 中准备真实项目。
- 当真实项目由用户手工准备时，Codex 不应强行先调用 `create_project`。

## 3. 推荐任务拆解顺序

当用户说“在某个项目中创建或修改 POU”时，推荐顺序是：

1. 确认或提取 `project_path`
2. 使用 `open_project`
3. 先使用 `list_project_objects` 或 `find_project_objects`
4. 只根据返回结果选择真实容器
5. 根据目标类型选择：
   - `create_program`
   - `create_function_block`
   - `create_function`
6. 读取已有文本：
   - `read_textual_declaration`
   - `read_textual_implementation`
7. 根据修改意图选择：
   - 整体替换用 `replace_text_document`
   - 末尾追加用 `append_text_document`
   - 指定位置插入用 `insert_text_document`

补充约束：

- 客户端递归扫描时，优先看 `can_browse`。
- `is_folder` 只保留兼容意义，不能再作为主要递归条件。
- `child_count` 只是提示信息，不是是否继续扫描的判断依据。
- `is_device` 与 `device_identification` 是设备树增强信息，可辅助识别控制器、总线和模块。
- 如果调用方传入 `/` 或 `Application`，服务端仍会尝试自动解析到真实项目里的嵌套 `Application` 容器，但这只是 fallback，不是主流程。
- 在真实 SP20 自动化链路中，源码文本暂时应保持 ASCII-only，避免中文注释写入后乱码。
- 写实现区之前，应先确保声明区包含实现逻辑会使用到的变量。
- 当任务目标是“在现有工程中编辑或生成 POU”时，客户端不应自行切换到 `create_project` 或 `add_controller_device`。

## 4. 文本工具语义

- `replace_text_document`: 用新全文覆盖原文
- `append_text_document`: 只在末尾追加
- `insert_text_document`: 在指定字符偏移位置插入
- 当前真实后端建议源码和注释使用 ASCII-only

不要把 `append_text_document` 当成“任意位置插入”工具使用。

## 5. 当前不可靠或暂缓能力

- `scan_ethercat_devices` 暂缓
- `create_project/open_project/save_project/add_controller_device` 的真实自动化链路仍可能受到 SP20 环境问题影响
- 若用户已手工准备项目，优先走“现有项目 + POU 操作”的路径
- `create_project` 现在属于高风险工具：
  - 仅用于明确的新工程创建场景
  - 不能作为“找不到 Application 时的兜底方案”

## 6. 自然语言到工具的大致映射

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
