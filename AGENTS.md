# AGENTS.md

本文件用于为进入本仓库工作的 AI 代理提供统一、稳定、可执行的项目规则。

## 1. 项目定位

本仓库用于开发一个基于 Python 的 MCP Server，用来封装 CODESYS IDE / Schneider EcoStruxure Motion Expert SP20 的 Scripting API，并对外提供结构化工具能力。

本仓库同时包含：

- MCP Server 主体代码
- Python Client SDK
- 面向后续渐进开发的文档、测试和示例骨架

## 2. 当前阶段目标

当前项目处于基础能力开发阶段。优先实现以下主链路能力：

1. Project 创建、打开、保存
2. Controller 插入
3. POU 创建
4. POU 程序声明区和实现区的读写与修改
5. 网络扫描
6. PLC 通信绑定与连接
7. PLC 登录
8. 应用启动运行

以下能力当前明确暂缓，不纳入第一阶段开发范围：

- `EtherCAT_Master_SE` 扫描

说明：

- 该能力在官方帮助中存在，但脚本入口尚未在目标环境中完成验证。
- 该能力保留为占位模块，不阻塞其他模块和工具开发。

## 3. 关键参考文档

在开始任何实现前，优先参考以下文件：

- [prompt.md](D:\工作资料\codesysAPItest\prompt.md)
- [prompt_lite.md](D:\工作资料\codesysAPItest\prompt_lite.md)
- [codesys_mcp_capability_mapping.md](D:\工作资料\codesysAPItest\codesys_mcp_capability_mapping.md)
- [docs/architecture/repository_structure.md](D:\工作资料\codesysAPItest\docs\architecture\repository_structure.md)
- [README.md](D:\工作资料\codesysAPItest\README.md)
- [docs/research/sp20_automation_blocker.md](D:\工作资料\codesysAPItest\docs\research\sp20_automation_blocker.md)

原则：

- `prompt.md` 定义项目总目标与开发路线。
- `prompt_lite.md` 定义逐模块生成代码时必须遵循的最小规则。
- `codesys_mcp_capability_mapping.md` 定义当前已确认能力、API 映射和暂缓项。
- `repository_structure.md` 定义当前仓库结构与模块职责。
- `sp20_automation_blocker.md` 定义当前真实 SP20 自动化调用的阻塞情况。

如果以上文档与临时实现想法冲突，优先遵循这些文档，而不是即兴扩展。

## 4. 仓库结构约定

重要目录说明如下：

- `src/codesys_mcp_server/`
  - MCP Server 主体代码
- `src/codesys_client_sdk/`
  - Python Client SDK
- `docs/api_specs/`
  - MCP tools 和内部接口规格
- `docs/research/`
  - 调研、验证记录、供应商差异说明
- `tests/unit/`
  - 单元测试
- `tests/integration/`
  - 集成测试
- `scripts/`
  - 本地辅助脚本
- `examples/`
  - 示例调用与演示脚本

服务层按业务域拆分，当前以以下目录为主：

- `services/projects/`
- `services/pous/`
- `services/devices/`
- `services/online/`
- `services/ethercat/`

约定：

- 新能力应优先放入现有业务域目录。
- 不要在没有明确必要的情况下新增新的顶层目录。
- 不要把多个业务域的实现混放在同一个模块中。

## 5. 开发与实现规则

所有代码实现必须遵循以下规则：

1. 每次只实现一个函数或一个模块。
2. 每个模块只承担单一职责。
3. 所有接口统一采用结构化 JSON 输入输出语义。
4. 所有异常必须被捕获，并返回结构化错误对象。
5. 所有关键操作必须记录日志，至少包含：
   - 时间戳
   - 函数名或能力名
   - 输入参数摘要
   - 成功或失败状态
6. 与 CODESYS IDE 的连接能力应通过统一连接管理实现，避免分散创建连接对象。
7. 所有新增能力都应具备最小可测试性。
8. 每次开发完成后，应同步补齐必要文档，而不是只改代码。

特别要求：

- 不要一次性生成庞大的、多能力耦合的代码。
- 不要越过文档约束自行扩展未确认接口。
- 不要在 `services/ethercat/` 中提前实现未经验证的 EtherCAT 扫描逻辑。
- 在 `sp20_automation_blocker.md` 所述阻塞项解除前，不要主动执行新的真实 SP20 自动化调用，除非用户明确要求继续排查环境问题。

## 6. 文档维护规则

当前仓库中已经存在多份 `README.md` 和设计文档。处理原则如下：

- `AGENTS.md` 是 AI 代理的规则入口，不替代 `README.md`。
- `README.md` 负责介绍仓库和目录。
- `AGENTS.md` 负责约束 AI 如何在本仓库中工作。
- 不要把 README 的内容大段复制到 `AGENTS.md`。
- 当需要详细背景时，应在 `AGENTS.md` 中引用现有文档，而不是重复维护相同内容。

如果后续某个子目录形成了稳定且明显不同的局部规则，再考虑在对应子目录增加局部 `AGENTS.md`。在此之前，默认只维护仓库根目录这一份主 `AGENTS.md`。

## 7. 测试与验证规则

当前项目仍处于骨架阶段，但后续所有功能开发都应遵循以下验证要求：

- 新增模块时，至少补一个最小单元测试入口。
- 涉及多步骤流程时，再逐步补集成测试。
- 如果因环境限制无法运行某项测试，必须在结果说明中明确指出。
- 不要声称某项能力“已验证通过”，除非确实完成了对应验证。

## 8. Git 与变更管理

本项目采用渐进式开发方式，变更管理应保持清晰、可回溯。

规则如下：

- 大改动前先确认变更边界。
- 大改动后应检查变更范围是否与当前目标一致。
- 提交前优先确认：
  - 代码位置是否正确
  - 文档是否同步
  - 测试是否已运行或已说明未运行原因
- 不要顺手改动与当前任务无关的模块。
- 不要覆盖或回退非当前任务引入的现有改动。

说明：

- Git 提交、状态检查和提交信息整理本身不依赖额外 Skill 才能完成。
- 如需安全审视、CLI 设计或 GitHub 评论处理，可按需使用已安装的 Skills。

## 9. 推荐使用的 Skills

本项目当前已安装并可能会用到以下 Skills：

- `security-threat-model`
  - 用于涉及登录、凭据、API Key、权限边界的设计评审
- `cli-creator`
  - 用于后续如需创建开发辅助 CLI 或调试命令入口
- `gh-address-comments`
  - 用于将来接入 GitHub PR 评论处理工作流

说明：

- 只有当任务明显匹配 Skill 用途时再使用。
- 不要为了使用 Skill 而使用 Skill。

## 10. 完成标准

一项工作可以视为“完成”，至少应满足以下条件：

1. 代码放在正确目录和正确业务域下。
2. 实现符合当前阶段范围，没有越界开发。
3. 输入输出、异常处理和日志规则已满足。
4. 已补充最小测试入口，或明确说明暂不能测试的原因。
5. 相关文档已同步更新。
6. 没有引入不必要的结构复杂度。

## 11. 行为准则

在本仓库中工作时，优先遵循以下行为方式：

- 先读文档，再动代码。
- 先做小步实现，再做集成。
- 先保证结构清晰，再追求功能扩张。
- 当发现某项能力仍存在文档或环境不确定性时，先记录并隔离，不要硬写。

如果同一类错误反复出现，应及时更新本文件，而不是只在对话里临时提醒。
