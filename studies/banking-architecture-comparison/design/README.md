# 四实验实施设计入口

日期：2026-11-17。下面的材料细化“如何实施与如何验收”，不是运行结果。正式规模、共同条件和历史证据保持不变；各方案仍未放行。

1. [公共执行框架](execution-framework.md)：公共模块与ArmDriver边界、拟新增接口、状态隔离、超时传播及防止方案混入。
2. [能力装配与配置来源](capability-assembly.md)：四方案能力矩阵、声明/观察/验证区别、配置和报告生成设计、MOA部署拓扑。
3. [交付与失败定位](delivery-and-diagnosis.md)：W1–W7交付顺序、保护上限检查、两张结果表、五段偏差定位和失败报告模板。

关于银行测试暴露的跨 Agent 规划、授权和部分成功问题，见[基于 Core Java 与 Runtime Java 的框架增强建议](java-business-task-execution.md)。

| 方案实施细化 | 当前主要交付目标 |
| --- | --- |
| [方案1](../../../experiments/plan-1-deepagent-original-skills/implementation-plan.md) | 原始Skill新接线、与方案2条件等价 |
| [方案2](../../../experiments/plan-2-deepagent-refined-skills/implementation-plan.md) | 优化指南接线、证据到行为关联 |
| [方案3](../../../experiments/plan-3-moa-refined-skills/implementation-plan.md) | 既有慢规划裁剪、原生委派/输入续接、七领域权限 |
| [方案4](../../../experiments/plan-4-agent-hub-refined-skills/implementation-plan.md) | 真实Go效果链、拒绝/绕过检测、未知结果治理 |

当前权威数值仍来自[study.json](../study.json)；本文不创建第二套运行参数。当前准备度见[横向准备报告](../readiness-report.md)。
