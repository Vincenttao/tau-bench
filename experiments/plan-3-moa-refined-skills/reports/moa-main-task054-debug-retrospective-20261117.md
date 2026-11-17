# MOA MAIN 与 task-054 调试复盘

## 1. 结论

本轮调试先后排除了模型连接、单纯超时和任务执行顺序等表层原因，最终定位到两个相互独立的问题：

1. 领域 Agent 的 Todo 状态恢复不完整，导致 assessment 或 continuation 在参数校验阶段失败。
2. MAIN 虽然已经能安排安全的跨领域执行顺序，但没有把一个关联业务目标中的共享业务意图固定并传递给所有领域 Agent。争议 Agent 因此把“换卡由后续 Agent 执行”错误解释为“当前争议应保持卡片有效”，写入了 `card_action=keep_active`。

第二个问题是 task-054 最新一次官方评分仍为零的主要业务参数差异之一。修订后的 v6 prompt 不硬编码 task-054 或官方参考值，而是增加通用规则：MAIN 必须区分用户最终业务意图、写操作责任方和执行顺序；关联任务必须共享业务不变量；执行后必须核对跨任务参数和回执的一致性。

截至本文记录时：代码修订和针对性回归已经完成，Java 路由检查通过；v6 尚未执行新的 task-054 真实 E2E，因此不能声称问题已经在真实模型链路中关闭。

## 2. 调试范围与证据边界

本复盘覆盖以下问题链：

- task-060 为什么按用户叙述顺序执行，而没有先评估跨任务依赖；
- MAIN 120 秒等待超时是否由 Java、MOA、prompt 或模型接口引起；
- 切换 DeepSeek 官方接口后，MAIN 是否仍会超时；
- v5 全局规划 prompt 是否能够修复任务顺序；
- task-054 为什么在三个业务目标均完成后仍被官方判定失败；
- Todo 恢复修订解决了什么，仍遗漏了什么；
- `card_action=keep_active` 是如何产生的；
- v6 prompt 如何修复这一类关联任务语义漂移。

证据分为四类，不能互相替代：

| 证据类型 | 能证明什么 | 不能证明什么 |
| --- | --- | --- |
| 静态代码和 prompt | 当前实现包含哪些规则 | 模型一定遵守规则 |
| 单元及 Java 路由检查 | 本地契约、编译和指定边界成立 | 真实银行任务一定通过 |
| 模型直连探针 | 接口、认证和响应形态可用 | 完整 Java MAIN 链路正确 |
| 真实 task E2E | 指定任务在指定模型和运行环境中的实际结果 | 对全部任务和模型普遍有效 |

## 2.1 更早的版本历史与重建限制

### 证据限制

当前 Git 历史只找到一个直接包含 `BankingPrompts.java` 的提交：

```text
33bed5c 2026-11-17 16:24:03 +0800
Add MOA banking integration fixes and verification reports
```

该提交中的 prompt 版本已经是 `moa-banking-v3`。它的父提交不存在该文件，因此无法仅依靠 Git commit 逐行还原未版本化基线、v2 和 v3 之间的每一次中间修改。下面的 v2→v3 过程由同期报告、当前提交快照和真实运行报告交叉重建。可以确认修改目的和提交时的最终内容，但不能声称每个中间工作区状态都已恢复。

### 版本演进总览

| 阶段 | 主要问题 | 主要修改 | 当时验证 | 后续暴露的缺口 |
| --- | --- | --- | --- | --- |
| 未版本化基线 | MAIN 主要约束最终回复语言，子任务、问答、确认和业务事实使用边界不完整 | 尚未形成独立银行 prompt 版本 | 两次 task-003 历史业务结果均为 0 | 英文链路、领域边界、推荐条件和证据使用不稳定 |
| v2 | MAIN 只要求最终英文；产品比较可能按“额度”关键词错误拆域；确认文本丢失依赖/条件 | 英文覆盖新任务、问答和汇总；产品公开额度归 card-application；已有卡提额归 credit-limit；补回确认中的依赖和 `when` | Java/脚本 Runtime 接线与模型输入采集通过 | 真实 task-003 首轮领域 Todo 双 `in_progress`；随后 MAIN 120 秒超时 |
| v3 | DeepAgent Todo 创建语义被模型误解；上下文和状态迁移规则不足 | 明确首项固定 `in_progress`、其余 `pending`；要求原子完成旧项并激活新项；补产品条件、未知资格和客户申请权限规则 | 真实 Todo 工具复现与 Java 检查通过；context-fix task-003 单题 reward=1 | 仍没有跨领域全局依赖规划规则；异常后的完整恢复仅部分验证 |
| v4 | task-060 中 MAIN 没有保护跨任务资源和资格依赖 | 增加 whole-request goal analysis、资源/资格依赖、证据收集、`depends_on`/`when` 和结果汇总 | Java 检查通过；一次运行阻止了提前销户，但未完成 E2E | DeepSeek 真实 E2E 中模型仍忽略抽象规划要求，直接先销户后开户 |
| v5 | v4 的“整体规划”要求不够操作化，MAIN 未先取得领域 Skill 证据 | 强制 Skill evidence → whole-request planning → execution；assessment-only 和 write plan 分阶段 | task-060 真实 E2E reward=1；task-054 能按 CLI→争议→换卡排序 | Todo continuation/retry 参数错误；关联任务没有共享最终业务意图 |
| v6 | task-054 中争议记录 `keep_active`，后续却执行 replacement | 增加 shared business invariants，区分最终意图、写责任和执行顺序；执行后核对跨任务参数 | 针对性 prompt 测试和 Java 检查通过 | 尚未执行新的真实 task-054 E2E |

### 未版本化基线

同期实现检查报告记载，早期 MAIN “只要求最终英文回复”。这意味着最终答复可以是英文，但 MAIN 生成的子任务 query、候选解释和澄清问题未被统一约束。产品比较中出现信用额度事实时，也可能被错误拆给提额领域，而不是由信用卡产品领域完成一次完整比较。

当前仓库没有可直接恢复的基线 `BankingPrompts.java`，因此这里只记录报告确认的行为差异，不构造不存在的源码版本。

### v2：英文链路、领域职责和确认语义

v2 的目标不是处理跨领域依赖，而是先保证现有 MOA 链路能正确表达银行任务：

- MAIN 新生成的子任务、问答、候选解释和汇总使用英文；
- 保留原生 stage confirmation，不由 MAIN 另行询问确认；
- 产品公开额度范围和产品比较归 `card-application-agent`；
- 已有信用卡的额度资格与调整归 `credit-limit-agent`；
- 英文确认补丁重新展示前置任务、`when` 条件、条件不成立时跳过和不确定时停止；
- 增加 MAIN 模型输入输出的只读采集，便于核对真实请求，不改变控制流。

修订原因来自早期 task-003 和接线检查：当时需要先确认失败来自模型决策、领域执行还是观察器/确认文本，而不能只根据最终回复判断。

v2 真实 task-003 首次执行没有进入官方评分。领域 Agent 完成大量 KB 搜索后，Todo 出现两个 `in_progress`，A2A 任务失败；重试时 MAIN 又在首段响应前等待 120 秒超时。这个结果把下一阶段问题拆成两个方向：Todo 工具契约误解，以及独立的模型调用超时机制。

### v3：Todo 安全迁移与上下文恢复

提交 `33bed5c` 中的 v3 prompt 已包含以下规则：

- `todo_create` 会忽略模型提供的 status，固定首项为 `in_progress`、其余为 `pending`；
- 不得用 `todo_create` 更新既有列表；
- 推进时必须用一次批量 update 同时完成当前项并激活下一项；
- 任意时刻最多一个 `in_progress`；
- 只有证据支持时才能把任务标记完成；
- 产品比较要区分硬条件、排序偏好、公开额度范围和实际批准结果。

这次修改源于真实 Todo 工具复现：模型在创建时把首项写成 `completed`，但工具实际仍把它保存为 `in_progress`；随后模型又启动第二项，稳定触发双活动项异常。修复选择明确工具契约和原子状态迁移，没有放宽底层“单活动项”约束。

同一阶段还修复了几个并非 prompt 版本本身、但影响真实复验的运行问题：

- 新任务携带已有用户/助手可见对话，避免失败后重新请求时丢失客户补充信息；
- 排除 system、工具结果和隐藏题目，避免把内部内容包装进新请求；
- 非流式 A2A 委派结果未知时不自动重发，防止旧任务仍执行时再次撞上会话锁；
- 外层 A2A 等待调整为覆盖领域执行上限，但单次模型首段 timeout 仍保持 120 秒；
- 修复模型异常后产生误导性 unmatched 空响应的观测记录。

`context-fix` 后的 task-003 真实复验得到 `reward=1`，但报告明确保留两个限制：这是单题 pilot；失败后新任务保留补参的路径只有输入构造回归，没有完成新的真实故障复验。

### v4：从局部领域正确转向 whole-request planning

task-060 暴露了 v3 的结构性缺口：每个领域可以局部正确，但 MAIN 没有在写操作前保护另一个目标所需的资源。销户 Agent 只检查销户条件，不会自动知道随后开户所需的 tenure 前提。

v4 `moa-banking-v4-global-planning` 增加：

- 先识别整个请求的全部 outcome；
- 检查跨任务资源和资格依赖；
- 在不确定时先收集证据；
- 用原生 `depends_on` 和 `when` 表达依赖；
- 最终核对所有 outcome，而不是把单个 delegation 完成视为整题完成。

第一次 v4 task-060 尝试在 Runtime 启动时失败，没有业务调用。第二次尝试中，MAIN 先规划了销户和开户 assessment，并加入条件任务；领域证据已经建议先开户后销户。原生条件判断阻止了提前销户，但 MAIN 在用户接受新顺序后的下一次模型调用中发生 120 秒超时，因此没有形成官方评分结果。

切换 DeepSeek 官方接口后，v4 的七次 MAIN 调用全部成功，没有超时。但模型仍在第一份计划中生成两个独立任务：先关闭 Green，再开 savings，没有 assessment、`depends_on` 或 `when`。这次官方 `reward=0` 证明 v4 的抽象指导没有被模型稳定执行，促成 v5 的动作化约束。

### v5：把“整体思考”改为强制三阶段动作

v5 不是简单增加更多“请仔细思考”，而是规定可观察的动作顺序：

```text
domain Skill evidence → whole-request planning → execution
```

如果权威前提、当前事实或安全顺序尚不明确，当前 `stage_plan` 只能包含只读 assessment。MAIN 必须要求每个相关领域使用自己的 Skill 和权威策略，返回 prerequisites、affected resources、unresolved facts 和 feasible sequencing。在 assessment 完成前，不得把受影响写操作放入同一个冻结计划。

这一版本解决了 v4 的“模型看见原则但不执行步骤”问题。task-060 后续真实 E2E 成功，但 task-054 又暴露更细的语义问题：安全顺序已经正确，关联领域对最终 card outcome 的参数解释仍不一致。这成为 v6 的直接原因。

### 同期非 prompt 修订

版本演进期间还有三类重要修订，不应误归因于 MAIN prompt：

1. **资源启动修订**：DeepSeek 第一次官方接口 E2E 因内存和 swap 耗尽，部分领域 Runtime 未完成 MCP 初始化。随后限制每个 JVM heap 为 256 MiB，并只让 MAIN 配置远端领域发现。
2. **模型接口修订**：实验 runner 支持显式、可记录的 API base 和 model override，用于 DeepSeek 官方接口诊断；正式四组比较配置未因此改变。
3. **Todo 边界修订**：task-054 v5 期间继续增加 id、status、单活动项和持久集合校验。这些修订提高 continuation/retry 的可恢复性，但不能代替 MAIN 对共享业务意图的规划。

## 3. 阶段一：task-060 暴露 MAIN 全局规划缺陷

### 3.1 现象

早期 task-060 运行中，MAIN 收到了整体规划提示，但仍按用户叙述顺序规划：先关闭 Green checking，再开 savings。关闭操作移除了满足 savings 开户期限要求的 checking account，导致后续目标无法完成。

这说明“整体思考”“考虑依赖”等抽象要求不足以稳定改变模型行为。MAIN 需要明确的动作顺序和阶段边界。

### 3.2 v5 修订

MAIN prompt 升级为 `moa-banking-v5-skill-evidence-plan`，明确要求：

1. 识别所有目标、领域和可能改变资源的操作。
2. 先由相关领域 Agent 读取 Skill 和权威策略，执行只读 assessment。
3. 在安全顺序依赖 assessment 时，不得把 assessment 和业务写操作放入同一个冻结计划。
4. MAIN 汇总证据后停止，由后续用户请求进入原生规划流程。
5. 只有证据充分后才能形成完整 write plan，并使用 `depends_on` 和 `when` 表达依赖。
6. 依赖结果缺失、失败或含糊时，不得授权后续写操作。

该修改保持现有 MOA 能力边界：MAIN 不直接读取领域 Skill，不增加动态计划重排器，也不引入新的任务事务账本。

### 3.3 task-060 验证结果

在 DeepSeek 官方接口的真实 E2E 中：

- 首轮计划仅执行只读 assessment；
- 领域证据证明 Green 满足 tenure 前提，Blue 不满足；
- MAIN 将顺序改为先开 Silver Plus savings，再关闭 Green checking；
- 官方结果为 `reward=1.0`、`business_pass=true`；
- MAIN 35 次请求全部返回，最大间隔为 `30.949` 秒，没有超时。

这个结果证明 v5 能修复已暴露的 task-060 顺序问题，但它只是单题回归，不代表整体基准提升。

## 4. 阶段二：MAIN 120 秒超时诊断

### 4.1 历史现象

历史运行中，`main-model-11` 等待 120 秒后抛出 `HttpTimeoutException`。失败发生在可用响应产生之前，客户端重试次数为零，因此错误直接传播。该调用使用非流式请求。

当时没有以下证据：

- 没有 HTTP 429 或 5xx；
- 没有上下文超限响应；
- 没有模型标识和 token usage；
- 没有证据证明生成完成后只是客户端没有读取。

### 4.2 探针与脱敏重放

合成上下文请求能够成功完成，但它不是原始输入、token 数、复杂度或 Java 客户端的精确复现，因此不能排除偶发网关排队或上游停顿。

随后使用经授权的脱敏请求进行两次相同 payload 重放：

| 次数 | 结果 |
| --- | --- |
| 第一次 | 180 秒仍未收到响应头，`ReadTimeout` |
| 第二次 | 约 8.27 秒返回 HTTP 200 和 tool call |

同一 payload 一次超时、一次快速成功，说明该 payload 并非必然超限或必然过慢。问题可以在 MOA 和 Java 之外复现，因此不能把根因归结为 Java Runtime 或 Skill 执行。网关路由、排队、上游停顿、缓存和后端选择仍是可能因素，需要服务端 tracing 才能进一步区分。

### 4.3 DeepSeek 官方接口对照

切换到 `https://api.deepseek.com` 和 `deepseek-flash` 后：

- 短请求、两次脱敏 MAIN 非流式请求和一次流式请求均成功；
- 非流式脱敏 MAIN 分别约 8.55 秒和 16.08 秒完成；
- 流式请求约 0.13 秒开始返回事件，约 11.72 秒完成；
- 后续 task-060 和 task-054 真实 Java MAIN 链路均未出现 120 秒超时。

这证明官方接口在本轮实验条件下可用，但不能单独证明模型版本导致差异，因为接口、账号路由和模型别名同时发生了变化。

### 4.4 是否改为流式

流式可以更早暴露响应进度，也可能避免某些网关缓冲整个响应后才返回的等待形态。但本轮没有证明流式能够消除历史故障。提高 timeout 同样只会提高容忍度，不会修复网关或上游停顿。因此本轮优先通过官方接口真实 E2E 验证业务链路，没有把“改为流式”当作已确认根因的修复。

## 5. 阶段三：task-054 第一轮 E2E 暴露 Todo 恢复问题

task-054 包含三个关联目标：

1. 提交并批准信用额度增加；
2. 对 CloudSync 交易提出争议；
3. 更换相关信用卡。

此前失败运行先争议、再换卡、最后申请 CLI，导致 CLI 不再符合条件。该任务适合验证 MAIN 是否能处理三方跨领域依赖。

### 5.1 v5 第一次运行

证据目录：`runs/live-e2e-moa-task054-deepseek-v5-20261117-01`。

MAIN 正确创建了 assessment-only 计划，没有执行争议、换卡或 CLI 写操作。领域 assessment 找到了无现有争议、无待处理换卡、无既往 CLI 请求和连续按时付款等事实。

但后续流程因领域 Todo 参数失败：

- `card-lifecycle-agent`：更新项缺少 `id`；
- `transaction-dispute-agent`：更新不存在的 `provisional_credit`；
- 持久会话重试时重复 append `sequencing`。

最终没有完成三个业务目标，官方 `reward=0` 合理。此时主要阻塞不再是 MAIN 顺序，而是 Todo 状态集合和重试恢复契约。

## 6. 阶段四：Todo 恢复两轮修订

### 6.1 第一轮修订

项目边界在 model-generated `todo_modify` 进入 Core/A2A 前校验：

- `update` 和 `append` 每一项必须有非空、批内唯一的 `id`；
- `update` 的 id 必须已经存在；
- `append` 的 id 必须尚不存在；
- 非法调用改为读取权威 `todo_list`，允许模型在同一 ReAct 循环中重新计算。

领域 prompt 同时要求在 rejection、resume 或 retry 后重新读取 Todo 状态。

### 6.2 第二次 task-054 E2E

证据目录：`runs/live-e2e-moa-task054-deepseek-v5-20261117-02`。

本次运行最终按正确顺序完成三个目标：CLI 先批准，随后提交争议，最后换卡。但仍出现两个未覆盖的 Todo 校验问题：

- 同时存在多个 `in_progress`；
- update 项缺少 `status`。

这些错误造成过 A2A 失败，后续新的用户请求才使业务操作继续完成。

官方仍为零，并暴露了三个业务差异：缺少成功的 `log_verification`、换卡配送方式与参考不同、争议使用 `card_action=keep_active`。

其中配送方式不能为了匹配隐藏参考而覆盖用户明确偏好；`card_action` 则需要按照公开工具契约进一步核查。

### 6.3 第二轮 Todo 修订

边界增加以下校验：

- 每个 update/append 项必须提供受支持的显式状态；
- 根据未修改项和批量修改项计算调用后的完整状态；
- 调用后最多只能存在一个 `in_progress`；
- 开始下一个任务时，必须在同一批 update 中完成当前任务。

Java 回归增加 missing status 和 multiple active state 用例。

### 6.4 第三次 task-054 E2E

证据目录：`runs/live-e2e-moa-task054-deepseek-v5-20261117-03`。

结果如下：

- 三个业务目标按安全顺序完成；
- CLI 从 `$5,000` 增加到 `$7,500`；
- CloudSync 争议成功提交；
- 只下了一个 expedited replacement 订单；
- 之前的 missing status 和 multiple `in_progress` 没有再次出现；
- MAIN 47 次请求全部返回，最大间隔 `24.449` 秒，没有超时；
- 官方仍为 `reward=0.0`、`business_pass=false`。

剩余 Todo 问题包括 append 项缺少 `content`/`activeForm`，以及同一 invocation 内重复 append `unresolved_facts`。后者说明仅从持久文件重新读取状态不够：当前 ReAct invocation 内，内存状态已经变化，而磁盘状态可能仍滞后。

官方 action 差异减少为两项：缺少 `log_verification`，以及争议记录为 `keep_active` 而参考要求 `cancel_and_reissue`。

## 7. `card_action=keep_active` 的根因

### 7.1 已验证事实

争议 Agent 实际检索到了正确的公开知识库规则：

- `keep_active`：用户希望继续使用当前卡，只争议该交易；
- `cancel_and_reissue`：用户希望更换卡，无论换卡已经通过独立工具下单，还是由争议流程触发。

用户的整体目标包含换卡，但要求按安全顺序执行。用户没有明确选择“保持当前卡有效”。

争议 Agent 最终提交了：

```text
card_action=keep_active
```

并在回复中称这是“per your instruction”。随后 card-lifecycle Agent 又关闭旧卡并下单换卡。

### 7.2 推断出的决策过程

从轨迹可还原以下错误链：

```text
用户最终意图：争议交易并更换卡
        │
MAIN 拆为两个有顺序的领域任务
        ├─ 争议 Agent 先提交争议
        └─ card-lifecycle Agent 后执行一次换卡
        │
争议 Agent 为避免重复换卡或越过领域边界
        │
把“本任务不执行换卡”错误映射为“用户选择 keep_active”
```

避免重复写入和保持领域边界本身是正确目标。错误发生在参数语义映射：

| 概念 | 正确解释 | 实际错误解释 |
| --- | --- | --- |
| 用户最终业务意图 | 争议并更换旧卡 | 当前步骤先保持卡有效 |
| 写操作责任方 | card-lifecycle Agent 执行换卡 | 争议记录不能表达换卡意图 |
| 执行顺序 | 先争议，后换卡 | 争议时必须选择 keep_active |

`card_action` 表达的是用户对卡片最终处理方式，不是当前 Agent 是否负责下换卡订单。争议 Agent 可以记录 replacement outcome，同时不执行换卡操作；后续 Agent 再执行唯一一次换卡写入。

### 7.3 为什么最终状态看似正确仍判定失败

后续换卡使旧卡最终关闭，所以物理状态接近用户目标。但争议记录仍表示用户希望保持旧卡有效。这造成两个关联写入之间的语义矛盾：

```text
dispute.card_action = keep_active
replacement.order_created = true
```

后一个成功写入不能自动修复前一个错误业务记录。官方评分核对数据库和 action 参数，因此即使用户表面目标完成，仍会判定失败。

### 7.4 根因归属

根因主要位于 MAIN 的跨任务契约，而不是知识库缺失：

1. MAIN 传递了目标和顺序，但没有显式生成共享业务不变量。
2. MAIN 没有要求各领域对同一最终 outcome 使用一致语义。
3. 争议 Agent 将参数解释成当前任务的执行开关，而不是用户最终业务意图。
4. 执行后 MAIN 只确认各项回执，没有发现 `keep_active` 与后续 replacement 的矛盾。
5. “per your instruction”是错误归因，因为用户没有明确选择该值或其业务含义。

## 8. v6 修订方案

### 8.1 MAIN prompt

版本更新为：

```text
moa-banking-v6-linked-outcome-plan
```

新增的通用要求包括：

- 在形成 write plan 前，为描述同一用户 outcome 的关联任务生成共享业务不变量；
- 将同一个最终 outcome 传递给所有受影响领域；
- 不得把执行顺序、领域写权限或避免重复写入转换成不同的用户选择；
- 明确区分用户最终意图、写操作责任方和执行顺序；
- 允许前一个领域记录由后续任务实际执行的 outcome，但不授权前一个领域执行或重复后续写入；
- 在每个 task query 中携带共享不变量和该任务的写边界；
- 计划参数存在互相矛盾的用户 outcome 时，不得 finalize 或 execute；
- 执行后同时核对业务参数和 receipts；后续成功操作不能修复前一个表达错误用户选择的记录。

这些规则没有出现 `task_054`、`keep_active` 或 `cancel_and_reissue`，可用于争议与换卡、关户与资金转移、冻结与支付等通用关联任务。

### 8.2 领域 prompt

领域通用规则增加：

- 根据用户最终业务意图解释操作参数；
- 不根据当前 Agent 的写操作所有权或任务位置改变参数含义；
- 后续任务执行实际变更时，当前记录仍应保留共享 outcome；
- 当前 Agent 不得因此执行或重复下游写操作；
- 除非用户明确选择了某个值或其文档化含义，不得称该值为用户指令。

### 8.3 为什么这不是针对测试作弊

本次修改满足以下边界：

- 没有读取或注入隐藏参考答案；
- 没有在 prompt 中写入 task id、账户 id、交易 id 或期望枚举值；
- 参数语义来自领域 Agent 实际检索到的公开工具契约；
- 修复的是关联任务中“意图、责任和时序混淆”的一般问题；
- 仍由领域 Skill 决定具体参数值，MAIN 只负责保持跨任务语义一致。

因此这是正常的架构和 prompt 修复，不是为了匹配单题隐藏结果而硬编码答案。

## 9. 本次代码改动

修改文件：

- `experiments/plan-3-moa-refined-skills/java/src/eval/BankingPrompts.java`
- `experiments/plan-3-moa-refined-skills/tests/test_runtime_hosts.py`

新增回归检查：

- prompt 包含 shared business invariants；
- prompt 区分 customer intended business outcome；
- prompt 禁止把 avoidance of duplicate writes 转换为不同选择；
- prompt 在 incompatible customer outcomes 时阻止执行；
- prompt 要求核对 returned business parameters 和 receipts；
- 领域 prompt 禁止错误声称“customer's instruction”；
- prompt 不包含 `cancel_and_reissue`；
- prompt 不包含 `task_054`。

## 10. 验证结果

### 10.1 已通过

针对性 Python prompt 回归：

```text
Ran 2 tests
OK
```

Java `check-routing.sh` 通过：

- real MOA slow routing；
- English confirmation；
- MAIN model evidence read-only behavior；
- Todo transition；
- Todo boundary validation。

`git diff --check` 通过。

### 10.2 环境限制

运行完整 `test_runtime_hosts.py` 时，当前受限环境禁止测试创建 `127.0.0.1` 随机监听端口，产生：

```text
PermissionError: [Errno 1] Operation not permitted
```

同一文件中的两个新增 prompt 测试已经单独通过。该端口错误不能作为本次 prompt 修订失败的证据，也不能替代完整 Runtime 集成验证。

### 10.3 尚未验证

尚未使用 v6 对 task-054 执行新的真实 E2E，因此以下结论仍待验证：

- MAIN 是否在真实输出中显式形成共享 card outcome；
- 争议 Agent 是否按照公开策略选择与 replacement 一致的 `card_action`；
- card-lifecycle Agent 是否仍只产生一个换卡订单；
- MAIN 是否能发现并阻止跨任务参数矛盾；
- `log_verification` 差异是否仍然存在；
- 剩余 Todo append 字段和同 invocation 内存状态问题是否影响流程。

## 11. 下一轮真实 E2E 检查清单

重新执行 task-054 时，应使用新的输出目录，并检查：

1. 运行证据中的 prompt 版本必须是 `moa-banking-v6-linked-outcome-plan`。
2. assessment 阶段不得发生争议、换卡或 CLI 写入。
3. write plan 必须保持 CLI → dispute → replacement 的证据支持顺序。
4. dispute query 必须同时包含最终换卡意图和“本任务不执行换卡”的边界。
5. replacement query 必须依赖争议成功及其返回参数与换卡意图一致。
6. 争议记录和换卡 receipt 必须表达一致的用户 outcome。
7. replacement order 的实际写入次数必须为一。
8. 不得把任何未经用户明确选择的值描述为“per your instruction”。
9. 检查成功的 `log_verification` 是否存在；若不存在，应单独定位 native tool 选择问题。
10. 检查 Todo 是否仍出现缺少 `content`/`activeForm` 或 invocation 内重复 append。
11. 分别记录业务完成、官方 action/DB 比较、Todo 合法性和模型延迟，不用其中一项替代另一项。

## 12. 后续建议

建议按以下优先级继续：

1. 使用 v6 重新执行一次 task-054 真实 E2E，先验证共享 outcome 修订是否改变模型行为。
2. 若仍产生 `keep_active`，检查 MAIN 实际生成的 task query 是否包含共享 outcome；据此区分 MAIN 未遵守 prompt，还是领域 Agent 忽略了已传入约束。
3. 独立修复 `log_verification` 的 native tool 调用，不与 `card_action` 根因混在一起。
4. 完成 Todo append 必填字段校验，并在一次 ReAct invocation 内维护权威内存状态，避免磁盘状态滞后。
5. 修复后再选一个不同的关联任务做非 task-054 回归，以验证规则具有一般性。

## 13. 相关证据

- `reports/model-timeout-diagnosis-20261117.md`
- `reports/task060-v5-skill-evidence-prompt-20261117.md`
- `reports/task054-v5-deepseek-e2e-20261117.md`
- `runs/live-e2e-moa-task054-deepseek-v5-20261117-01/`
- `runs/live-e2e-moa-task054-deepseek-v5-20261117-02/`
- `runs/live-e2e-moa-task054-deepseek-v5-20261117-03/`
- `java/src/eval/BankingPrompts.java`
- `tests/test_runtime_hosts.py`

## 14. v6/v7 后续真实 E2E 更新

后续五次运行及两项 Runtime 修订记录在 `reports/task054-v6-v7-live-e2e-20261117.md`。

最新结果改变了本文此前“尚未执行 v6 E2E”的状态：v6/v7 已执行真实 task-054。共享 outcome 修订使实际争议参数从 `keep_active` 变为 `cancel_and_reissue`，并保持一个 replacement order；该问题已在两个 scored run 中未复现。

但整题仍未通过。MAIN 在证据明确表明 dispute/replacement 会阻止 CLI、且客户随后明确要求 CLI-first 的情况下，仍冻结 dispute → replacement → CLI 计划。CLI 没有提交或批准，官方 reward 仍为 0。v7 的通用 feasibility-preserving prompt 同样被 `deepseek-flash` 忽略。因此不能继续把增加同类 prompt 文本称为可靠修复；下一步需要决定是否在现有 MOA 能力范围内增加确定性的 plan consistency gate。
