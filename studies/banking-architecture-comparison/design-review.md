# 四方案测试设计检查与修订记录

日期：2026-11-16。本次为文档、配置及本地源码核对；没有进行独立第三方评审、框架构建或真实模型测试。

## 逐项检查结论

| 方案 | 修改前 | 本次补充 | 当前边界 |
| --- | --- | --- | --- |
| 1 原始Skill DeepAgent | README和plan.json，缺独立详细设计 | 调用链、原始资产隔离、7项检查、22题规则、提示词等价及失败判据 | 旧英文执行器已归档，新准备入口可用；正式执行适配和共同调度器待实现 |
| 2 优化Skill DeepAgent | README和plan.json，历史材料分散 | 七业务指南边界、政策到Todo、8项检查、方案1对照和成本指标 | 共享组件已提取，正式执行适配待接入；模型行为效果仍待本轮测试 |
| 3 完整MOA | 已有场景、架构、技术设计和中文专项计划 | 英文主对比、状态所有权、A→B→A步骤、11组结构检查、来源与缺口 | 慢意图旁路封堵、远端恢复及英文适配待实现 |
| 4 Agent Hub | 已有23项契约和148次B0/B1专项 | enforce单轮主对比、效果边界、12组检查映射全部23项契约、成本及误拒分析 | 真实Go控制链、接线及故障验证待实现 |

四方案现在均有详细设计。设计完成不等于运行能力或验收通过；四份plan.json继续comparison_ready=false、execution_enabled=false，study.json为不可执行规格。

## 本轮发现和处理的问题

| 编号 | 问题 | 处理与依据 |
| --- | --- | --- |
| R01 | 原始Skill要求英文，中文runner只允许banking-evidence-guides/3.1/3.2/3.3 | 主对比统一英文官方commit；保持原始文本不改；中文专项保留 |
| R02 | 方案1/2可能同时改变系统提示词 | 两者固定evidence-todo-v1及同一代码；正式冻结需核验实际展开输入 |
| R03 | 中文task hash不能代表英文输入 | 只复用22个canonical ID，从英文任务文件重新计算raw-byte SHA-256 |
| R04 | Hub148次多seed专项与每题一次冲突 | 主比较仅enforce，每方案22次，总88；旧专项不叠加、不自动执行 |
| R05 | MOA现有config仍为中文 | 保留独立专项，新增共同study引用与显式优先级；执行适配仍是阻塞项 |
| R06 | 方案名或Go进程存活不能证明真实架构 | MOA独立Agent/远端恢复证据；Hub停Go与接线变异检查作为门禁 |
| R07 | 把模型行为检查全设为前置门禁会筛掉弱基线 | 区分接线门禁与业务测量；普通行为失败仍计入，严重效果问题停止 |
| R08 | 重跑、未评分或分母选择可制造提升 | 88唯一位置、无自动重跑、原null保留，同时报告计划与已评分分母 |
| R09 | 多Agent额外调用成本容易遗漏 | MOA意图/规划、Hub纠错及模拟器用量全部纳入，并按层拆分 |
| R10 | 单次已暴露22题不足以证明泛化或稳定性 | 明确诊断回归性质；仅逐题差异及描述性结果，不承诺提分 |

## 设计完整性检查

四份详细设计均覆盖：目标/范围、当前状态、调用链、状态归属、资产与输入、共同条件、正反例、执行步骤、结果/失败判据、证据、成本或专项指标、责任角色和实施缺口。共同设计补充调度顺序、分母守恒、暂停/停止条件、数据隔离和交付位置。

具体责任人尚未登记，模型实际版本也不能仅凭请求别名锁定；执行前需要记录人员、机器资源、制品、实际模型和所有提示词hash。当前文档没有虚构可直接启动MOA/Hub的命令。

## 核查依据

- [原始Skill](../../shared/skills/releases/1.0.0/banking-mcp/SKILL.md)：原始英文答复和Skill/MCP说明。
- [中文执行器](../../archive/deepagent-source/v0.4/run_zh_e2e.py)：版本白名单、中文基准和默认条件。
- [Java装配](../../shared/java/src/main/java/eval/DeepAgentAssembly.java)：实际提示词版本装配点。
- [MOA专项计划](../../experiments/plan-3-moa-refined-skills/test-plan.md)及[配置](../../experiments/plan-3-moa-refined-skills/config/experiment.json)：中文条件和未实施状态。
- [Hub专项规格](../../experiments/plan-4-agent-hub-refined-skills/design/plans/test-spec.json)：23项契约、B0/B1和148次规模。
- [共同规格](study.json)、[英文题集](cohort.json)、[静态验证结果](design-validation.json)：本次新增资产及一致性检查。
