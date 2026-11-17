# MOA Banking V2 真实端到端测试复盘

## 结论

本次 `task_003` 使用真实模型、真实 MAIN Runtime、7 个领域 Runtime 和官方 banking simulator 执行。运行结果是 **未评分的执行失败**，不是业务结果被评分器判定为失败。

- `status`: `execution_error`
- `business_pass`: `null`
- `formal_comparison`: `false`
- 没有 `result.json`，没有官方 reward
- 未发生业务写入、信用卡申请或数据库变更

## 执行链路

1. MAIN 生成高风险执行计划，获得模拟用户确认。
2. MAIN 将信用卡比较路由到 `card-application-agent`。
3. 领域 Agent 执行 24 次 `KB_search`，找到 Silver、Gold、Platinum 等产品证据。
4. 领域 Agent 创建 Todo 后发生双 `in_progress` 冲突，远程任务失败。
5. MAIN 没有伪造比较结果，向用户报告失败并建议重试或人工处理。
6. 模拟用户要求再试一次。新 A2A 任务中，MAIN 模型在首段响应前等待 120 秒超时。
7. Java bridge 返回 `TASK_STATE_FAILED`，Python supervisor 终止 simulation，因此没有进入官方评分。

## 根因分析

### 一、首次失败：Todo 状态冲突

这是直接的程序失败原因。

- 模型向 `todo_create` 传入的首项 `gather_evidence` 状态是 `completed`。
- Todo 工具返回时仍将该首项标记为当前任务：`[→]`，内部状态等价于 `in_progress`。
- 下一次 `todo_modify` 又将 `rank_candidates` 设为 `in_progress`。
- 底层校验发现两个进行中任务，抛出：`More than one task is marked as 'in_progress' (only one allowed)`。

这是 **DeepAgent/Todo 工具语义与模型输出组合触发的问题**，不是 MOA 基数、MAIN 路由或 A2A 协议本身的失败。现有 prompt 要求“证据变化后更新 Todo”，但没有明确规定“不得在 `todo_create` 中把首项直接设为 `completed`”及单活动项的安全迁移顺序。

### 二、第二次失败：MAIN 模型首段超时

这是独立的外部模型调用失败。

- 错误：`model call timeout at BEFORE_FIRST_SEGMENT`
- 超时：`header_wait timeout after 120.0s`
- 当前配置未自动重试，A2A 任务直接进入 `TASK_STATE_FAILED`。

这一失败与第一次 Todo 冲突无直接因果关系。

## 与 MOA、prompt、Skill 的关系

| 层次 | 本次观察 | 判断 |
|---|---|---|
| MOA 路由 | MAIN 正确选择信用卡领域 Agent | 通过本用例的路由观察 |
| MOA 失败收敛 | 领域失败后 MAIN 没有伪造业务成功 | 符合设计 |
| MAIN prompt | 计划确认、路由和失败说明正常 | 未发现导致首次失败的证据 |
| 领域 prompt | 证据 Todo 要求存在，但缺少安全状态迁移约束 | 需要小范围修订 |
| Skill | 成功约束 Agent 读取指南和通过 `KB_search` 取证 | 未观察到 Skill 路由失败 |
| DeepAgent Todo | 创建时重解释首项状态，随后校验失败 | 直接故障点 |

## 建议的最小修订

1. 在领域 prompt 中增加 Todo 安全迁移规则：创建时只设一个 `in_progress`；切换前先完成当前项；不在创建时把首项声明为 `completed`。
2. 对 DeepAgent Todo 工具增加回归用例：创建首项为 `completed` 时的实际状态，以及从一个活动项切换到下一项的原子操作。
3. 在不改变 MOA 能力边界的前提下，为首段超时增加有限次数的幂等重试，或将其明确分类为可重试的模型依赖失败。
4. 修正 `trajectory_preserved` 字段的语义。本次原始轨迹已保存 54 行，但该字段为 `false`，它实际表示“没有可供评分的完整 Simulation 对象”。
5. 修正 MAIN 模型观测事件：异常后已有 `model_exception`，但又记录一条 `call_id=unmatched` 的空 `model_response`，应避免误导调用对账。

## 证据与哈希

- `episodes/task_003/status.json`: `8afeed68c4961c6cb797514e81904750d0babcc4728b52197227be34f84838b8`
- `episodes/task_003/exception.txt`: `e1a12cce8a6e72acf1f2273b9a116c07f912fec5a7d93f7c98854bb4040b9b55`
- `episodes/task_003/official-trajectory.jsonl`: `a9b0cd5a7d1df49cb4887583d2b445901c9ef9a4ea9f89ef3481f8553c676531`
- Todo 冲突：`episodes/task_003/moa/card-application-agent.stderr.log:1828`
- MAIN 超时：`episodes/task_003/moa/banking-moa.stderr.log:1249`
- 最终 bridge 异常：`episodes/task_003/exception.txt:28`

凭据未记入本报告、manifest 或异常文件。运行结束后未发现残留的 MOA/Runtime 进程。
