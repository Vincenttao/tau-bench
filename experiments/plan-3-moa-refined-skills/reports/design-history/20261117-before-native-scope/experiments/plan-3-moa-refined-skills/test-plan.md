# MOA 银行完整流程测试方案

2026-11-17刷新：本文件现作为英文主比较的执行顺序说明。详细验收以 test-design.md、plans/scenarios.json 和共同 acceptance-matrix.json 为准。config/experiment.json、plans/banking-cohort.json 的中文配置仅保留作历史专项，不作为本文件默认输入。

## 目标、边界与冻结

验证五项要求：仅慢意图识别、七个独立业务 Agent、MOA Todo、任务 A 让出执行并保持状态、B 完成后恢复 A。不能以单纯重发请求、创建新业务任务、重新执行已成功写入或打印模拟轨迹作为恢复通过。

当前已有八Runtime pilot及两次真实单题诊断；完整远端恢复与正式流水线尚未完成。真实诊断的执行完成不等于业务得分通过，见 reports/moa-pilot-review-20261117/review.md。此次刷新仅修订测试规格并离线核查历史证据。

正式运行前冻结：Solution/Core/Runtime commit与实际JAR、源码/工作区差异、领域Agent Card、权限、Skill与展开prompt hash、实际官方benchmark源码/KB/DB/评分器、模型请求名与实际返回版本。语言en、BM25、seed=300及22题取共同study/cohort；以plan.json和study.json联合校验为准，不继承旧中文task hash或模型配置。

## 分层执行与放行门禁

| 阶段 | 范围 | 放行证据 |
|---|---|---|
| source-contract-check | 28个细化用例、schema、目录、权限与资产 | 用例字段完整；主/子ID映射完整；全部待实现项明确 |
| scripted-moa-contract | 真实MOA/Runtime、脚本模型、协议L2 | 路由、阶段授权、单一调度、等待/恢复与隔离断言；纯函数测试不代替本阶段 |
| bank-bridge-contract | 真实官方环境、脚本业务Agent | 同题共享状态、主体与工具日志、严格重放、独立业务完成判断 |
| restart-and-fault-contract | 真实持久化与双端故障注入 | P3-09五类窗口及P3-03c/07/08全部阻塞断言，必须早于正式轮 |
| live-dependency-smoke | 真实模型、MOA、业务Agent | 独立合成A→B→A与A→B→C→B→A结构/业务证据；模型质量单列 |
| model-behavior-diagnostic | 跨轮咨询、边界数值、证据汇总 | P3-03e保留真实成功/失败，不改正式题或强制用户选择 |
| selected-banking-round | 英文22题各一次 | 全部阻塞契约放行后执行；原官方reward、架构与业务结果分开 |


阶段是放行条件，不能因单元测试通过跳过真实 MOA 的协议层。已有 MOA 测试类 `StageFlowIT`、`HierarchicalIntentSwitchIT`、`TaskPauseRuntimeContractTest` 可作为入口；当前仅确认源码存在，未运行。构建命令需在独立实验 checkout 中按父 POM 实际依赖生成，不给不存在的启动脚本或虚构 CLI。

## 场景矩阵与关键断言

完整场景见 `plans/scenarios.json`，至少覆盖：
- 单业务、多业务、显式 intent、TARGET handoff 全部进入慢路径；新请求的 fast 路由计数必须为 0。
- 每个 Todo 有业务目标、Agent、依赖、授权边界及验收条件；无候选不丢弃目标后继续假成功。
- 已执行部分步骤的 A 挂起后 B 真正改变官方状态；恢复 A 保留 businessTaskId、todoId 和 checkpoint 关联。
- A→B→C→B→A的执行顺序（依赖图为A依赖B、B依赖C）、多项等待、用户变更目标、等待用户输入、无法满足前置条件、依赖环。
- 重复恢复/重复回调无重复扣款、销卡、申请；超时后的未知提交先核验，不自动重试。
- 错 session/Agent 的 checkpoint、已消费检查点及伪造完成必须拒绝；计划已修订但未取消的旧委派合法回执接收一次；业务输出中的指令不改变权限。
- B 成功但 A 仍不满足条件时不得强行批准；转人工只能标记移交。
- 暂停回执 ACCEPTED 与真实停止必须分别观察；暂停后不启动后继 Todo，按契约处理在途远端工作。
- L1/L2 重启后恢复，已完成 B 不重做；没启用持久化的部署不能声称通过重启恢复。

## 官方 benchmark 接入

正式适配器的验收要求（现有MoaPilotAgent仅部分接线）：把官方用户消息送到 MOA A2A 会话；把用户确认、业务澄清原样交给官方用户模拟器，不自动替用户同意规划或业务写入。MOA/L2 调用银行 MCP 时经 episode 独占桥进入原官方工具环境，所有子 Agent 的工具记录汇入同一官方轨迹，并额外保留 actor/delegation/checkpoint 元数据。内部 Todo、路由和恢复消息不能伪造成用户消息或银行工具调用。

银行工具调用的 requestor 仍遵守官方 assistant/user 契约；独立 Agent 身份用于可追溯和权限约束。客户专属工具交给原模拟用户执行。桥不能把 get/approve 等子 Agent 操作藏在官方轨迹之外，否则 DB replay 与官方评分失真。每题重建初始状态，各题之间完全隔离。

只在题目要求或可观测事实确实需要时产生依赖和暂停；不强迫 22 题全部经过 A→B→A。恢复专项用明确标注的 synthetic fixtures。不得按 task ID、预期动作或评分结果驱动路由、Todo 或业务决策。

## 评分与停止条件

官方业务通过：官方 reward==1；官方失败：已评分 reward<1；基础设施异常、取消、用户暂停、中途故障保留 null 和原因，不能冒充 0 或 1。DB、ACTION 等 reward_basis 从每题官方结果读取。例：销户 reason 字符串不同可能导致官方 DB 0，即使开户销户均已完成；报告可以解释但不能改分。

MOA 流程验收单独记录：slow_path_only、agent_isolation、todo_valid、checkpoint_saved、dependency_completed、resumed_same_business_task、no_duplicate_write、business_evidence_verified、termination_bounded，取 pass/fail/unknown/not_applicable。A2A COMPLETED、操作通知、Todo 完成均不能单独证明银行成功。

统计：planned/started/scored/pass/fail/unscored/cancelled、passed/scored、官方每题对照、恢复成功数/适用恢复数、正确路由/可人工核验路由、依赖处理时间、各层模型次数与 Token、每题时长。单次单组不证明稳定性或因果改善；多 Agent 和新增模型调用改变条件，不伪称只改一个变量。

默认题间串行、每题一次、无自动 episode 重试；在途写入不重试。仅记录 Token，不设未经用户指定的累计 Token 停止阈值。部署拟设单题40分钟、全study总有效运行64小时（四方案共同预算）、每次远端调用120秒、最大业务步骤200、最多任务32、单任务恢复8次、动态依赖扩展4层；这些是待实施配置，正式运行前固定并验证，超限保留明确终态。循环依赖、越权、冻结漂移或无法确认旧进程状态时停止新题。

## 产物、工作台与交付

每个 run 使用英文语义名和时间戳，写 `manifest.json`、`progress.json`、逐题 `attempt/status/result.json`、官方对话和独立 `moa-events.jsonl`。关联字段至少含 episode/session/planRevision/todoId/agentId/businessTaskId/transportTaskId/delegationId/checkpointRevision/operationId/eventId。

工作台展示：慢意图候选及理由 → 规划与风险确认 → Agent 分派 → 每项 Todo 状态 → 挂起原因和检查点 → 依赖操作 → 恢复关联 → 官方结果。只显示受控摘要，密钥及完整可复用恢复令牌不进日志。若现有工作台不能理解 MOA 事件，标为待实现，不用现有 DeepAgent 页面截图充当验证。

最终交付包括逐题结果、失败因果链、实际/参考状态差异、未评分说明、源码/配置哈希与恢复验证记录；原始轨迹不提交 Git。本次方案刷新不触发新的模型诊断或正式轮；执行时保留独立批次与冻结证据。
