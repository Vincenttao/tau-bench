# MOA现有能力范围修订与后续调整

日期：2026-11-17。结论：本轮以本地agent-solution的现有MOA为参照，修改银行适配和测试设计；不以新增编排底座作为通过条件。本报告替代此前复盘中的扩展实施建议，保留原始失败证据与评分。

## 依据与范围

源码基线为 `0298dcd28a1f3613b47f2af9def52512bab7dbd6`，模块为 `/home/vincent/openjiuwen/agent-solution/common/agents/moa-agent`。相关文档和源码摘要如下；核验文件hash见同目录 `native-moa-scope-validation-20261117.json`。

| 现有机制 | 来源 | 本轮处理 |
| --- | --- | --- |
| 阶段规划、绑定、HIGH全计划确认、冻结后串行执行 | docs/task-orchestration.md；StagePlanningRail.java | 保留并验证 |
| 静态前序依赖、when条件 | 同上；ConditionEvaluator.java | 按原生执行/跳过/阻塞规则验证 |
| A2A普通输入续接、关联委派结果 | docs/task-orchestration.md；IntentRoutingRail.java | 验证真实Runtime与下游交互 |
| 意图切换后挂起未完成计划，按最新原文路由 | docs/task-orchestration.md；docs/suspended-tasks.md | 保留；不等同远端取消或定向恢复 |
| 显式启用后的本地计划恢复 | docs/suspended-tasks.md；IntentRoutingRail.requestResume | 当前七远端Agent部署不以此放行；启用才专项验证 |
| 未完成远端执行现场恢复 | IntentRoutingRail.requestResume明确拒绝该场景 | 记录能力边界，不新增checkpoint协议 |
| 执行完成通知 | docs/operation-completion.md | 与官方业务成功分开核验 |

上游默认具有快慢路由。本实验保留已有slow-only私有补丁，只观察原生慢规划及后续委派；它不代表默认MOA，也不证明新增了独立慢意图识别模型。若比较默认路由，应另冻结配置和批次。

原设计中的动态依赖调度、自动A→B→A、远端检查点、事务任务账本/outbox和跨进程恰好一次均退出本轮。旧设计21份文件及其hash保存于 [修订前快照](design-history/20261117-before-native-scope/snapshot.json)。旧恢复schema仅作历史参考。

## 还需调整什么

| 优先级与位置 | 具体调整 | 验证依据 |
| --- | --- | --- |
| P0：银行确认文案、规划prompt | 确认模板、todo.query、领域答复和MAIN汇总保持客户语言一致；不只修改固定模板 | 首次pilot被中文确认循环阻塞；第二次仍出现中文子任务 |
| P0：MAIN汇总prompt及领域目录 | 保留用户已表达的硬条件和排序偏好；区分“至少达到阈值”与“额度越高越好”；对照下游事实完成比较。产品公开额度与提额服务职责要清楚 | 第二次领域结果正确，但MAIN引导申请Gold，官方参考为Silver |
| P1：既有只读观测 | 记录MAIN和领域实际模型输入、有效prompt/Skill版本以及原生调用关联；避免把未入模的回包当成模型已知事实 | 现有MAIN输入证据不足，不能断言唯一根因是上下文丢失 |
| P1：真实组件测试入口 | 为新版场景绑定真实MOA/Runtime配脚本模型的driver，先验证原生阶段、补参和切换，再做独立模型诊断 | 当前完整用例仍pending，既有局部组件通过不能覆盖全部门禁 |

这些是待实施调整，本次没有修改运行代码、部署补丁或Skill发布。全部候选当前标为HIGH；如需减少只读咨询确认，必须利用现有能力目录与工具权限证明该候选确实只读，不能把整个可写Agent直接降为LOW。

当前Skill已包含比较条件与推荐原则，且有读取证据。先检查这些要求如何通过领域输出进入MAIN；没有消融对照前，不把失败归因于Skill缺少规则。若修改共用Skill，需新建版本并保持方案2/3/4的比较条件一致。

## 测试设计与验证边界

[新版测试设计](../test-design.md)与 [机器场景](../plans/scenarios.json)包含22个子用例：20核心阻塞、1模型行为观察、1可选本地暂停专项。正式银行题仍是22题；两种“22”含义不同。原28子用例已被替代，历史结果不能自动迁移到新编号。

已同步共享验收矩阵、执行契约和study契约hash。计划执行与比较开关保持关闭。新验证记录独立保存，不覆盖旧设计验证或官方运行报告。

本次运行配置契约单测、study契约校验、目录与链接检查，并检查子用例映射/hash及旧证据hash。结果见 [验证记录](native-moa-scope-validation-20261117.json)。这些检查证明规格一致性，不证明真实MOA场景全部通过；没有新增模型调用、Java构建或真实银行评测。

两次pilot的原分数仍为0：首次没有完成申请；第二次成功提交的是Gold申请，状态PENDING，参考要求Silver。完整事实及归因边界见 [原失败复盘](moa-pilot-review-20261117/review.md)。业务执行成功与官方任务成功必须分列。
