# 面向 MCP Server 的 CODESYS 能力清单与 API 映射表

更新时间：2026-04-20

本文基于 CODESYS 官方 Scripting 文档，对目标能力进行拆解，并映射到可用于 MCP Server 封装的核心 Script API。目标运行环境为 Schneider EcoStruxure Motion Expert SP20（基于 CODESYS IDE），但由于设备库、模板工程、控制器 DeviceId/type/version 可能带有供应商定制项，落地时仍需在目标 IDE 中二次确认。

## 1. 目标范围

本轮需要覆盖的业务目标如下：

1. 自动创建 Project，可选择 project type、Controller 类型、项目名称和保存路径。
2. 在新建或现有 Project 中创建 POU，支持 FB、PRG、Function，并支持程序读写与修改。
3. 扫描 EtherCAT_Master_SE 设备。
4. 在 IDE 中扫描网络并连接 PLC 设备。
5. 登录 PLC，支持用户名和密码。
6. 启动程序运行。

## 2. 结论摘要

- 第 1、2、4、5、6 步都能在官方 Scripting API 中找到较明确的对象和方法支撑。
- 第 3 步“扫描 EtherCAT_Master_SE 设备”在官方帮助中明确存在，但在本次核对到的 ScriptingEngine 对象文档里，没有看到一个直接公开的专用脚本方法，例如 `scan_ethercat_devices()` 这类 API。
- 因此第 3 步当前应标记为“功能存在，但脚本入口待验证”，后续需要在 SP20 实际 IDE 环境中确认是否通过命令执行机制、供应商扩展对象或其他自动化接口暴露。
- 当前项目决策：暂时搁置 `EtherCAT_Master_SE` 扫描能力的验证与开发，优先完成其余已明确可落地的模块和 MCP 工具；后续待核心链路稳定后，再单独恢复该能力的专项验证与实现。

## 3. MCP 能力清单与 API 映射表

| 步骤 | 用户目标 | 建议 MCP 能力名 | 关键 Script API / 对象 | 可行性判断 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 1 | 创建 Project，指定名称、路径、控制器 | `create_project` | `ScriptProjects.create(path, primary=True)` | 明确可行 | 项目路径可直接控制；项目名称通常由路径或后续保存路径决定 |
| 1 | 保存/另存项目 | `save_project` | `ScriptProject.save()`、`ScriptProject.save_as()` | 明确可行 | 可用于项目重命名与路径迁移 |
| 1 | 打开已有项目 | `open_project` | `ScriptProjects.open(path, ...)` | 明确可行 | 适合“已有项目继续编辑”场景 |
| 1 | 选择 Controller 类型并插入到项目 | `add_controller_device` | `ScriptProjectDeviceExtension.add(name, type, id, version, module=None)` | 明确可行 | 关键前提是拿到目标控制器的 `type/id/version` |
| 1 | 在设备树中继续添加子设备 | `add_child_device` | `ScriptDeviceObject.add(name, type, id, version, module=None)` | 明确可行 | 可用于继续挂载总线主站、模块等 |
| 1 | 选择 project type | `create_project_from_template` 或 `create_empty_project` | `ScriptProjects.create(...)` / `ScriptProjects.open(...)` / 模板工程另存 | 部分可行 | 官方文档明确支持“创建项目”，但未看到“新建向导模板类型”脚本参数 |
| 2 | 创建 FB | `create_function_block` | `ScriptIecLanguageObjectContainer.create_function_block(...)` | 明确可行 | 支持名称、语言、基类、接口 |
| 2 | 创建 PRG | `create_program` | `ScriptIecLanguageObjectContainer.create_program(...)` | 明确可行 | 默认 Structured Text，可传语言 GUID |
| 2 | 创建 Function | `create_function` | `ScriptIecLanguageObjectContainer.create_function(name, return_type, language=None)` | 明确可行 | 必须提供返回类型 |
| 2 | 读取声明区源码 | `read_textual_declaration` | `ScriptObjectWithTextualDeclaration.textual_declaration` + `ScriptTextDocument.get_text()` | 明确可行 | 适合读变量声明、接口定义 |
| 2 | 读取实现区源码 | `read_textual_implementation` | `ScriptObjectWithTextualImplementation.textual_implementation` + `ScriptTextDocument.get_text()` | 明确可行 | 适合读取 ST 实现代码 |
| 2 | 覆盖/替换源码 | `write_text_document` / `replace_text_document` | `ScriptTextDocument.replace(...)` | 明确可行 | 可整体替换，也可局部替换 |
| 2 | 插入/追加/删除源码 | `insert_text` / `append_text` / `remove_text` | `ScriptTextDocument.insert()` / `append()` / `remove()` / `replace_line()` | 明确可行 | 适合基于自然语言做局部修改 |
| 2 | 在线读取变量值 | `read_online_value` | `ScriptOnlineApplication.read_value(expression)` / `read_values(expressions)` | 明确可行 | 监视需已启用 |
| 2 | 在线写入变量值 | `write_online_value` | `ScriptOnlineApplication.set_prepared_value()` + `write_prepared_values()` | 明确可行 | 更偏在线调试/运行期写值 |
| 3 | 扫描 EtherCAT_Master_SE 下挂设备 | `scan_ethercat_devices` | 官方帮助中存在 “Scan for Devices” | 存在能力但脚本入口待验证 | 适用于 EtherCAT Master，但未在本次核对到的 ScriptingEngine 对象页中发现直接方法 |
| 3 | 将 EtherCAT Master 加到控制器下 | `add_ethercat_master` | `ScriptDeviceObject.add(...)` | 明确可行 | 需要 EtherCAT Master 的设备标识 |
| 4 | 扫描网络上的 PLC 设备 | `scan_network_devices` | `ScriptGateway.perform_network_scan()` | 明确可行 | 可返回网络中发现的目标设备 |
| 4 | 获取缓存扫描结果 | `get_network_scan_result` | `ScriptGateway.get_cached_network_scan_result()` | 明确可行 | 适合二次查询和客户端展示 |
| 4 | 通过 IP 定位目标地址 | `find_plc_address_by_ip` | `ScriptGateway.find_address_by_ip(address, port=11740)` | 明确可行 | 适合用户已知 PLC IP 的场景 |
| 4 | 将设备树里的控制器绑定到网关/地址 | `bind_plc_comm_settings` | `ScriptDeviceObject.set_gateway_and_address()` / `set_gateway_and_device_name()` / `set_gateway_and_ip_address()` | 明确可行 | 这是“连接 PLC”前的关键配置步骤 |
| 4 | 创建在线设备句柄并连接 | `connect_online_device` | `ScriptOnline.create_online_device(device=None)` + `ScriptOnlineDevice.connect()` | 明确可行 | 建议用 `with` 管理生命周期 |
| 5 | 设置默认凭据 | `set_default_credentials` | `ScriptOnline.set_default_credentials(username, password=None)` | 明确可行 | 适合单目标或默认登录流程 |
| 5 | 按目标设置专用凭据 | `set_specific_credentials` | `ScriptOnline.set_specific_credentials(target, username, password=None)` | 明确可行 | 多 PLC 或多连接目标时更稳妥 |
| 5 | 登录应用 | `login_application` | `ScriptOnlineApplication.login(change_option, delete_foreign_apps)` | 明确可行 | 登录前通常需完成在线连接和目标绑定 |
| 5 | 查询当前登录用户 | `get_logged_on_user` | `ScriptOnlineDevice.current_logged_on_username()` | 明确可行 | 可用于状态回传 |
| 6 | 启动程序 | `start_application` | `ScriptOnlineApplication.start()` | 明确可行 | 登录成功后即可触发运行 |
| 6 | 停止程序 | `stop_application` | `ScriptOnlineApplication.stop()` | 明确可行 | 便于补全运行控制能力 |
| 6 | 查询运行状态 | `get_application_state` | `ScriptOnlineApplication.application_state` / `operation_state` | 明确可行 | 适合客户端状态轮询或结果确认 |

## 4. 分步骤设计说明

### 4.1 创建 Project

可直接使用 `ScriptProjects.create(path, primary=True)` 创建新项目，并通过 `ScriptProject.save()` 或 `ScriptProject.save_as()` 完成保存与另存。

对“project name”和“保存路径”来说，脚本层是可控的：

- 保存路径：由 `create(path)` 或 `save_as(path)` 指定。
- 项目名称：通常由项目对象名与最终保存文件路径共同体现。

对“project type”来说，当前需要谨慎处理：

- 官方文档明确支持“创建新项目”。
- 但本次核对未发现一个直接暴露“标准工程 / 模板工程 / 供应商工程类型”的脚本参数。
- 因此建议在 MCP 设计中预留两种模式：
  - 空项目模式：直接 `create(path)`。
  - 模板模式：先打开模板工程，再 `save_as()` 为目标工程。

对“Controller 类型”来说，推荐通过项目根或设备树对象的 `add(name, type, id, version, module=None)` 来实现。落地时需要先从目标 IDE 设备库中确定具体的 `type`、`id`、`version`。

### 4.2 创建 POU 与编辑程序

POU 创建这部分在官方 Scripting API 中支持较完整：

- FB：`create_function_block(...)`
- PRG：`create_program(...)`
- Function：`create_function(...)`

程序源码层面的“读写和修改”可以拆成两个维度：

- 离线源码编辑：
  - `textual_declaration`
  - `textual_implementation`
  - `get_text()`
  - `replace()`
  - `replace_line()`
  - `insert()`
  - `append()`
  - `remove()`
- 在线变量值读写：
  - `read_value()`
  - `read_values()`
  - `set_prepared_value()`
  - `write_prepared_values()`

如果 MCP Server 的目标是让客户端通过自然语言“新建一个 FB 并写入一段 ST 逻辑”，那么最直接的封装方式是：

1. 创建 POU。
2. 获取声明区/实现区文档对象。
3. 用 `replace(new_text=...)` 或 `append(...)` 写入代码。

### 4.3 扫描 EtherCAT_Master_SE 设备

这一步目前是唯一需要标记为“待实机确认脚本入口”的部分。

可以确认的事实：

- EtherCAT 官方帮助文档明确提供 `Scan for Devices` 功能，并明确写明适用于 `EtherCAT Master`。
- EtherCAT 调试流程要求：
  - 先在项目中插入 EtherCAT Master。
  - 正确选择网络适配器。
  - 某些场景下需先下载到控制器，以确保 EtherCAT stack 可用。

当前未确认的部分：

- 在 `ScriptingEngine` 对象文档中，我没有找到一个清晰暴露的 EtherCAT 扫描脚本方法。
- 因此暂时不能把它定义成“已确认存在的标准对象方法”。

设计建议：

- 在 MCP Server 中将其抽象为独立能力 `scan_ethercat_devices`。
- 先把前置步骤全部脚本化：
  - 插入 Controller
  - 插入 EtherCAT Master
  - 配置通信
  - 需要时登录/下载
- 等在 SP20 环境中确认实际脚本入口后，再补上最终扫描动作。

### 4.4 扫描网络与连接 PLC

网络扫描是脚本层支持最明确的一段能力链：

- `ScriptGateway.perform_network_scan()`
- `ScriptGateway.get_cached_network_scan_result()`
- `ScriptScanTargetDescription` 用于读取扫描结果中的设备名、供应商名、设备类型、地址等。

连接 PLC 推荐拆成两个动作：

1. 配置离线设备树对象的通信参数：
   - `set_gateway_and_address()`
   - `set_gateway_and_device_name()`
   - `set_gateway_and_ip_address()`
2. 建立在线连接：
   - `create_online_device(...)`
   - `connect()`

这很适合 MCP 的工具化设计，因为客户端可以先自然语言触发“扫描网络”，再从返回设备列表中选择目标 PLC，最后执行“连接到该 PLC”。

### 4.5 登录 PLC

登录 PLC 需要两个层面的 API 配合：

- 凭据设置：
  - `set_default_credentials(username, password=None)`
  - `set_specific_credentials(target, username, password=None)`
- 在线登录：
  - `ScriptOnlineApplication.login(change_option, delete_foreign_apps)`

因此你描述的“输入用户名和密码登录 PLC”是能实现的。后续在 MCP Server 中应将用户名、密码、change option 封装为结构化 JSON 输入，避免散落在不同调用层中。

### 4.6 启动程序运行

官方对象上有直接方法：

- `ScriptOnlineApplication.start()`
- `ScriptOnlineApplication.stop()`
- `application_state`
- `operation_state`

因此“点击运行启动程序”在脚本层是明确支持的。MCP 封装时建议在 `start_application` 的返回结果里带上运行前后状态，便于客户端确认动作是否生效。

## 5. 面向 MCP Server 的建议工具拆分

结合上面的 API 映射，建议第一版 MCP tools 采用细颗粒度设计：

1. `create_project`
2. `open_project`
3. `save_project`
4. `add_controller_device`
5. `add_child_device`
6. `create_program`
7. `create_function_block`
8. `create_function`
9. `read_textual_declaration`
10. `read_textual_implementation`
11. `replace_text_document`
12. `append_text_document`
13. `scan_network_devices`
14. `bind_plc_comm_settings`
15. `connect_online_device`
16. `set_login_credentials`
17. `login_application`
18. `read_online_value`
19. `write_online_value`
20. `start_application`
21. `stop_application`
22. `get_application_state`
23. `scan_ethercat_devices`（占位能力，待确认脚本入口）

这套拆分方式比较适合你当前的开发原则：

- 每次实现一个函数或模块。
- 每个能力单一职责。
- 每个能力都能独立单元测试。
- 后续可由客户端自然语言编排成复杂流程。

## 6. 当前已识别的风险与待确认项

### 6.1 供应商定制设备标识

SP20 虽然基于 CODESYS IDE，但控制器、EtherCAT_Master_SE、通信驱动的 `type/id/version/module` 很可能是 Schneider 定制项。正式开发前需要补齐：

- 目标 Controller 的设备标识
- EtherCAT_Master_SE 的设备标识
- 相关设备描述是否已安装在设备库中

### 6.2 “project type” 不一定等于一个直接 API 参数

如果你想实现的是 IDE 新建工程向导里的模板类型选择，这在本次核对中尚未发现明确的单参数脚本入口。更稳妥的技术路线是：

- 空项目直建
- 模板工程复制
- 或维护一组标准模板工程

### 6.3 EtherCAT 扫描脚本入口待验证

功能存在，但当前不能把它定义成“已确认的标准对象方法”。后续应在目标 IDE 中验证以下路径：

- 是否存在可脚本执行的命令调用接口
- 是否存在供应商扩展脚本对象
- 是否需先登录或下载以加载总线栈

当前处理策略：

- 本项暂不纳入第一阶段开发范围。
- 第一阶段优先实现 Project、POU、网络扫描、PLC 连接、登录、启动运行等已确认能力。
- `scan_ethercat_devices` 保留为占位能力，不阻塞其他 MCP Server 模块和工具的设计与开发。

## 7. 推荐的下一步

建议后续先按以下顺序落地：

1. `create_project`
2. `add_controller_device`
3. `create_function_block` / `create_program` / `create_function`
4. `read/write textual implementation`
5. `scan_network_devices`
6. `bind_plc_comm_settings`
7. `set_login_credentials`
8. `login_application`
9. `start_application`
10. 在第一阶段主链路稳定后，再恢复 `scan_ethercat_devices` 的专项验证与实现

## 8. 参考文档

- CODESYS Scripting 总索引  
  <https://content.helpme-codesys.com/en/ScriptingEngine/idx-codesys_scripting.html>
- ScriptProjects  
  <https://content.helpme-codesys.com/en/ScriptingEngine/ScriptProjects.html>
- ScriptIecLanguageObjectContainer  
  <https://content.helpme-codesys.com/en/ScriptingEngine/ScriptIecLanguageObjectContainer.html>
- ScriptTextualObject  
  <https://content.helpme-codesys.com/en/ScriptingEngine/ScriptTextualObject.html>
- ScriptDeviceObject  
  <https://content.helpme-codesys.com/en/ScriptingEngine/ScriptDeviceObject.html>
- ScriptOnline  
  <https://content.helpme-codesys.com/en/ScriptingEngine/ScriptOnline.html>
- EtherCAT: Command - Scan for Devices  
  <https://content.helpme-codesys.com/en/CODESYS%20EtherCAT/_ecat_cmd_scan_devices.html>
- EtherCAT: Getting Started with Commissioning an EtherCAT Network  
  <https://content.helpme-codesys.com/en/CODESYS%20EtherCAT/_ecat_tutorial.html>
