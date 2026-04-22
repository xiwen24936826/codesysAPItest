# CODESYSAPITEST

用于封装 CODESYS IDE Scripting API 的 Python MCP Server 项目骨架。

## 当前目标

- 构建模块化、可维护、可测试的 MCP Server。
- 为外部客户端提供统一的 JSON 输入输出接口。
- 后续逐步实现 Project、POU、网络扫描、PLC 连接、登录、运行控制等能力。
- `EtherCAT_Master_SE` 扫描能力暂缓，待主链路稳定后再恢复专项验证与实现。

## 当前仓库结构

- `docs/`: 架构、研究记录、API 规格文档
- `src/codesys_mcp_server/`: MCP Server 主体代码
- `src/codesys_client_sdk/`: Python Client SDK
- `tests/`: 单元测试、集成测试与测试夹具
- `scripts/`: 本地开发与辅助脚本
- `examples/`: 示例用法与演示脚本

## 现有项目文档

- `prompt.md`: 项目总目标与开发计划
- `prompt_lite.md`: 模块化代码生成约束
- `codesys_mcp_capability_mapping.md`: 能力清单与 API 映射表

## 开发原则

- 每次只实现一个函数或一个模块
- 每个模块只承担单一职责
- 所有接口统一使用结构化 JSON 输入输出
- 所有异常返回结构化错误对象
- 所有关键能力都保留最小单元测试入口

