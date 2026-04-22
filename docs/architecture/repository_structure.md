# 仓库结构说明

本仓库采用“文档先行、模块分层、逐步实现”的组织方式。

## 顶层目录

- `docs/`: 设计与规范文档
- `src/`: Python 源码
- `tests/`: 测试代码
- `scripts/`: 开发脚本
- `examples/`: 示例代码

## Server 代码分层

- `server/`: Web 或 MCP 服务入口
- `core/`: 与 CODESYS IDE 交互的核心基础设施
- `config/`: 配置加载
- `logging/`: 日志封装
- `models/`: 请求、响应、错误模型
- `services/`: 按业务域拆分的能力模块
- `tools/`: 面向 MCP 暴露的工具层
- `utils/`: 通用工具函数

## 业务域划分

- `services/projects/`: Project 创建、打开、保存、控制器插入
- `services/pous/`: POU 创建、读取与源码修改
- `services/online/`: 在线连接、登录、运行控制、在线变量读写
- `services/devices/`: 网络扫描、设备通信绑定
- `services/ethercat/`: EtherCAT 能力预留，当前暂缓实现

