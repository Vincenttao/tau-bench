# 任务、Jev与Go控制链：实现与阶段验收

日期：2026-11-17。范围：新版方案4的J0/J1接线、部分J3/J4效果控制与合成端到端诊断。

**验收结论：单项提交组件链通过，完整方案验收未通过，正式22题运行关闭。** 本次真实调用了Jev，并执行了官方争议工具的原始实现；使用独立合成数据库，未运行官方用户模拟器、DeepAgent执行模型或官方评分，因此没有新版业务reward。

## 本次实现

| 模块 | 行为与代码 |
|---|---|
| Java进程宿主 | [TaskHost](../java/src/main/java/eval/hub/TaskHost.java)暴露状态、接收、预算、路由、澄清及停止接口；[TaskCoordinator](../java/src/main/java/eval/hub/TaskCoordinator.java)保存权威任务状态 |
| 输入链 | [task_session.py](../python/task_session.py)先持久接收并阻断、预扣预算、调用Jev、保存提案，再按期待revision提交；重启复用已落盘判断 |
| 输入判断 | [input_router.py](../python/input_router.py)生成原子问题；保留完整输入、原生响应和应用引用；取消、暂缓及恢复分别处理 |
| 业务条件 | [business_judgment.py](../python/business_judgment.py)将逐条件支持/违反观察组合为allow/deny/unknown；校验证据episode/goal范围，并绑定准确payload |
| 效果控制 | [controlled_effects.py](../python/controlled_effects.py)按episode/goal/step固定操作身份；前置采纳与最终派发分离；新输入、修订或取消阻断旧许可 |
| 回执 | 按官方争议工具文本契约解释accepted；操作结果与目标完成分离；重复回执幂等，错误身份拒绝，停止后仍可保存已在途结果 |
| 进程边界 | [hub_gate.py](../python/hub_gate.py)改用必要环境变量白名单；模型密钥不进入Go进程；启动前将账本路径解析为绝对路径 |

状态宿主与Go均是真实进程。Jev/Go不是新增自主Agent；任务状态仍由Java拥有。新组件尚未装配到DeepAgent正式driver。

## TDD与本地验证

先增加跨进程测试，观察缺少模块失败，再实现Java/Python接线。随后分别复现并修复：澄清未显式解决导致提交拒绝、恢复动作缺失、Go子进程继承TypeSafe变量、切换Schema工作目录后相对账本路径错误。

本次离线验证包含：真实Java进程重启、强制kill后的状态恢复、提供方失败不自动重试、审计失败不提交、已落盘判断恢复提交、暂缓A→处理B→显式恢复原A、真实Go派发、换调用ID不重复、入队失败后不重发、迟到回执及完成登记失联后的处理。

最终命令和结果见[校验摘要](controlled-chain-acceptance-20261117.json)。测试数量仅说明已执行的测试，不能换算为39项契约通过数。合成判断和业务条件不能充当真实模型能力证据。

```bash
bash experiments/plan-4-agent-hub-refined-skills/java/build-task-host.sh
bash experiments/plan-4-agent-hub-refined-skills/java/check-task-coordinator.sh
bash experiments/plan-4-agent-hub-refined-skills/go/check-gate.sh
.venv312/bin/python -m unittest discover -s experiments/plan-4-agent-hub-refined-skills/tests -v
```

## 真实Jev与官方工具实现诊断

每批使用新目录，失败和原始请求/响应均保留在忽略的`runs/`内。实际返回模型均为`jev-1.14.0`；共9次推理，输入8528 tokens、输出1075 tokens。认证目录请求不计入推理次数；本次不估算账户账单。

| 批次 | 结果 | 依据与限制 |
|---|---|---|
| `controlled-chain-20261117-a00` | 未通过 | 新目标可识别；新增＋暂缓组合出现未决及冲突，阻断后无银行写入 |
| `controlled-chain-20261117-a01` | 未通过 | 收紧“修改/覆盖”定义并排除不存在的待填槽问题后，组合步骤通过；恢复原目标时仍有未决观察，继续阻断 |
| `submission-chain-20261117-a00` | 未通过 | 输入及条件判断通过；Go因相对账本路径失效拒绝采纳，无银行写入 |
| `submission-chain-20261117-a01` | 单项组件链通过 | 修复路径后，Java→Jev输入判断→Jev条件判断→Go→官方工具实现→受理回执跑通；隔离DB一条新增，换ID重发拒绝，缺证据路径无额外写入 |

本次没有改变.3/.7合成阈值来消除失败。“恢复原目标”的实际响应中，`resume=.97`，但其他观察仍处于未决带；控制逻辑因此不派发。不能因最高分是resume就绕过冲突/未决门禁。该例暴露语义问题定义及问题组合仍需独立开发集验证，不能只对同一句话反复调参。

单项诊断直接构造合成客户、动作及一个合成条件契约，以验证组件接线。它没有证明公开银行政策前提被完整抽取、工具由Agent从KB自主发现，或客户真实资格成立；工具解锁使用官方公开方法，由测试驱动执行。该结果不能替代完整银行写入验收。

阶段A/B故障测试使用脚本观察；上述批次是开发诊断，不替代计划中冻结的24次阶段C观察，也不占正式22题位置。

## 尚未达到完整验收的原因

1. 新正式driver与DeepAgent执行循环未接线；当前新链未调用S2，也没有冻结的注册Workflow目录。
2. 新目标候选目前由可信调用方提供，尚未接入受约束的S2提案生成；用户要求、政策条件及完成条件的覆盖验收不完整。
3. 推荐、ask_user选项和最终自然语言出口未装配独立验收；不能阻止所有无依据建议。
4. 仅实现信用卡争议受理解析，缺完整工具能力表、全业务回执映射、Goal验收及待处理/未知结果的权威核对接线。
5. 真实多意图恢复仍进入澄清；没有完整的用户模拟器补充信息→恢复→总目标验收证据。
6. 累计模型预算目前覆盖Java输入判断预留，S2与业务判断还未接入共同512次预算；64次判断子上限也未形成完整运行层执行。
7. 原环境连续性、所有权限/修订反例、变异测试及四组共同调度门禁仍需完整验证。

因此，保留`execution_enabled=false`、`comparison_ready=false`，39项机器规格的待验收状态不变。没有调用旧只读pilot冒充新版端到端，也没有为了获得分数直接放开银行写入。

## 凭证处理

按用户授权将TypeSafe凭证存入仓库外临时运行环境文件，权限为0600，通过环境变量提供给Jev客户端，认证已成功。文件路径仅在会话中提供，报告、manifest、源码、请求正文和Go/Java子进程均不记录或继承该密钥。临时文件随本机临时目录生命周期保留，不是全机器永久环境设置。

## 下一实施顺序

先完成输入问题和独立正反例的契约冻结，再连接受控S2候选/节点执行与输出验收；同时补全公开政策条件、业务回执和Goal验收。共同预算及正式driver接好后，重新执行全部门禁，才进入官方用户模拟器→官方评分的诊断和正式比较。
