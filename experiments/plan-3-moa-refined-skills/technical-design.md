# MOA 银行接入设计：复用现有机制

更新：2026-11-17。上游基线 `0298dcd28a1f3613b47f2af9def52512bab7dbd6`；以 common/agents/moa-agent/docs/task-orchestration.md、suspended-tasks.md、operation-completion.md 及相应源码为依据。

## 允许的调整

1. 配置候选目录、adapter到A2A endpoint映射、领域职责、现有工具allowlist和会话范围。
2. 在既有Main/领域prompt中要求保留用户条件、明确业务归属、依据下游结果汇总；用现有会话/交互历史，不建第二套客户事实数据库。
3. 改善现有确认模板、规划内容和最终答复的语言一致性；实际部署补丁需独立冻结，不能声称是未修改上游。
4. 补实际模型输入输出、委派与回执的只读采集；采集器不改变业务决策或执行状态。
5. 评估程序离线比较最终答复、工具回执和官方DB；不在MOA内部新增BusinessEvidenceVerifier调度闸门。

当前pilot的slow-only是私有classpath补丁，跳过默认识别/任务数服务后进入原生阶段规划；保留其已批准实验身份，但不增加独立BankingSlowIntentRecognition要求。上游默认识别、基数分析、仲裁的行为可另做上游回归，不冒充本pilot已测。

## 执行与依赖

原生StagePlanningRail是唯一计划推进者。先登记完整目标，逐项绑定，HIGH时整计划确认，冻结后串行执行。depends_on只引用合法前序任务；when使用原生ConditionEvaluator。条件未知/失败按原生BLOCKED/SKIPPED语义处理，不另建ReadyTaskSelector跳过当前任务插入新依赖。

如果从一开始已知必须先还款再继续其他业务，可以在原生能力允许且客户授权的范围内规划顺序。执行途中发现新业务需求时，按当前交互/意图切换机制处理；不得承诺自动插入新任务后回到远端执行断点。

## 输入续接、意图切换和暂停

普通INPUT_REQUIRED：Runtime将关联用户答复交给原等待任务；不得把后台通知伪装成客户授权。只在真实下游支持此交互时才能验收通过。

意图切换：下游返回原生not-in-scope或in-scope-intent-change信号；MOA校验当前委派关联，挂起旧计划未完成项，使用最新用户原文重新路由。挂起列表是MOA观察记录，不是远端工作流实时快照。后续命中旧工作流由下游判断。

当前入口未显式导入MoaPauseIngressConfiguration，也未部署本地Skill时，不测试其本地恢复成功作为本方案放行条件。上游可选暂停/本地恢复单独记录适用条件；远端未完成现场恢复必须保留“不支持”的行为，不能用重发旧请求代替。

## 持久化与错误边界

使用现有Session/checkpointer和Runtime TaskStore配置；只有实际部署并验证的范围才能声明跨重启能力。当前不新增业务任务表、inbox/outbox、lease/fencing、checkpoint CAS协议。服务崩溃或银行写入结果未知时停止本题、保存证据并核查，不自动重跑episode或未知写入。无法恢复必须明确报告，不能为通过测试新增底座能力。

## 数据与评估

记录episode/session、plan revision、todo、toolCallId、实际A2A task/context及官方call ID。不可获得的关联字段标明缺失，不生成拟议businessTaskId/checkpointRevision来伪装能力。OperationCompletion只表示一次操作调用结束；官方业务验收和MOA阶段完成分开报告。

原 contracts/task-continuation.schema.json 与 continuation-examples.json 已标记退出本轮范围，不是当前A2A API，也不是启动依赖。详细用例见 [场景清单](plans/scenarios.json)。

## 当前实施记录

2026-11-17已通过BankingPrompts与现有能力目录修订银行提示，修复英文确认模板丢失依赖/条件说明的问题，并通过MoaAgentRailProvider增加MAIN只读模型输入输出采集。部署目录保存main-prompt.md、main-prompt-meta.json和main-model-events.jsonl；领域继续使用deepagent-events.jsonl。采集不写框架状态；失败输出MAIN_MODEL_EVIDENCE_INCOMPLETE，后续审计不得宣称采集完整。

真实Runtime配本机脚本模型的正例已验证阶段→确认→委派→领域提问→客户回答→MAIN汇总，以及记录与实际模型请求一致。完整门禁与真实模型推荐效果仍待验证，见[实现检查](reports/implementation-check-20261117.md)。
