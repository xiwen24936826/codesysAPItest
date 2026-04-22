# SP20 自动化调用阻塞记录

更新时间：2026-04-22

## 1. 背景

当前项目已经完成 `create_project`、`open_project`、`save_project` 的服务层实现，并已搭建真实 CODESYS / SP20 适配层，目标是通过脚本驱动 Schneider EcoStruxure Motion Expert SP20 实际创建和操作工程。

在继续推进 `add_controller_device` 与更复杂的真实联调前，发现当前目标机器上的 SP20 脚本调用链存在稳定性问题，会影响后续所有真实环境测试。

## 2. 当前已确认的真实环境信息

- SP20 IDE 主程序路径：
  - `E:\EcoStruxure Motion Expert SP20\EcoStruxure Motion Expert\Common\EcoStruxure Motion Expert SP20.exe`
- 可用脚本执行入口：
  - `E:\EcoStruxure Motion Expert SP20\EcoStruxure Motion Expert\Common\CODESYS.exe`
- scriptengine stub 路径：
  - `E:\EcoStruxure Motion Expert SP20\EcoStruxure Motion Expert\ScriptLib\Stubs\scriptengine`

已确认结论：

- `EcoStruxure Motion Expert SP20.exe` 用于正常 IDE 启动。
- 在自动化场景中，更稳定的脚本执行入口是 `CODESYS.exe`，并配合：
  - `--profile="EcoStruxure Motion Expert SP20"`
  - `--runscript="<path>"`
  - `--noUI`

## 3. 已确认可行的部分

以下动作已经在当前机器上完成过真实验证：

- 使用 `CODESYS.exe` 成功执行最小 smoke test 脚本。
- 使用桥接脚本成功跑通真实的：
  - `create_project`
  - `open_project`
  - `save_as`
- 真实集成测试 `tests/integration/test_real_codesys_project_adapter.py` 曾成功通过。

这说明：

- SP20 / CODESYS 脚本引擎本身并非完全不可用。
- 当前阻塞更像是“某些脚本调用路径或当前环境状态会触发额外组件异常”，而不是服务层实现完全错误。

## 4. 阻塞现象

在继续执行真实脚本调用时，用户机器反复弹出如下错误：

- 进程：`APInstaller.CLI.exe`
- 弹窗标题：`APInstaller.CLI.exe - 应用程序错误`
- 提示内容：
  - 应用程序发生异常，未知的软件异常 `(0xe0434352)`

用户反馈：

- 每次调用一次真实自动化指令，电脑都会出现该错误弹窗。

## 5. 当前判断

当前应将该问题视为“真实环境阻塞项”，而不是普通代码缺陷。

原因：

1. 服务层单元测试是稳定通过的。
2. 真实适配层曾经成功跑通过最小项目链路。
3. 当前错误弹窗来自 `APInstaller.CLI.exe`，不是 MCP Server 自身进程。
4. 继续强行调用真实 SP20 脚本只会不断干扰用户工作环境。

因此在阻塞项解除前，不应继续频繁触发真实 IDE 自动化调用。

## 6. 当前项目处理策略

从现在开始，采取以下策略：

1. 暂停主动执行新的真实 SP20 自动化命令。
2. 保留已经完成的服务层与适配层代码。
3. 后续优先继续：
   - 文档补齐
   - 接口规范完善
   - 可离线开发的模块
4. 等环境稳定后，再恢复真实 IDE 联调。

## 7. 最小排查清单

后续建议按以下顺序排查：

1. 确认是否每次 `CODESYS.exe --runscript` 都会触发 `APInstaller.CLI.exe`。
2. 检查 SP20 / CODESYS 安装器、包管理器、更新器是否处于异常状态。
3. 检查是否存在首次启动或组件修复弹窗被 `--noUI` 触发。
4. 检查 SP20 当前 profile 是否有缺失包、损坏包或待修复状态。
5. 手动启动 SP20 IDE，观察是否有安装器、包管理器、修复器相关提示。
6. 如有必要，检查 Windows 事件查看器中 `APInstaller.CLI.exe` 的应用程序错误日志。

## 8. 恢复真实联调的条件

只有在满足以下条件后，才建议恢复真实自动化测试：

1. 手动启动 SP20 不再触发安装器异常。
2. 最小 smoke test 脚本执行不再弹出错误框。
3. `create -> open -> save_as` 真实链路重新稳定通过。

## 9. 当前结论

当前项目不缺少“真实后端适配层”，阻塞点在于：

- 目标机器上的 SP20 / CODESYS 运行环境存在额外安装器异常
- 该异常会影响继续自动化调用

所以现阶段最合理的决策是：

- 暂停真实自动化调用
- 先记录阻塞
- 先排查环境
- 环境稳定后再恢复真实联调
