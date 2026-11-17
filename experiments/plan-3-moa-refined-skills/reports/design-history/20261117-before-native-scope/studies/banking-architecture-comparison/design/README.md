# 四实验实施设计入口

日期：2026-11-17。下面的材料细化“如何实施与如何验收”，不是运行结果。正式规模、共同条件和历史证据保持不变；各方案仍未放行。

1. [公共执行框架](execution-framework.md)：公共模块与ArmDriver边界、拟新增接口、状态隔离、超时传播及防止方案混入。
2. [能力装配与配置来源](capability-assembly.md)：四方案能力矩阵、声明/观察/验证区别、配置和报告生成设计、MOA部署拓扑。
3. [交付与失败定位](delivery-and-diagnosis.md)：W1–W7交付顺序、保护上限检查、两张结果表、五段偏差定位和失败报告模板。

| 方案实施细化 | 当前主要交付目标 |
| --- | --- |
| [方案1](../../../experiments/plan-1-deepagent-original-skills/implementation-plan.md) | 原始Skill新接线、与方案2条件等价 |
| [方案2](../../../experiments/plan-2-deepagent-refined-skills/implementation-plan.md) | 优化指南接线、证据到行为关联 |
| [方案3](../../../experiments/plan-3-moa-refined-skills/implementation-plan.md) | 真实慢意图、委派、同任务恢复、七领域权限 |
| [方案4](../../../experiments/plan-4-agent-hub-refined-skills/implementation-plan.md) | 真实Go效果链、拒绝/绕过检测、未知结果治理 |

当前权威数值仍来自[study.json](../study.json)；本文不创建第二套运行参数。当前准备度见[横向准备报告](../readiness-report.md)。
