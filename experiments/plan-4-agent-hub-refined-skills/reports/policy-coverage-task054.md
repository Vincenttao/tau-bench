# 参数来源与政策覆盖审查：054 单次回归

沿用上一轮 DeepSeek/Jev、冻结 Skill、种子 300、运行限制及官方评分器。本次执行链 10 项验收通过，官方数据库终态不匹配，reward 为 0。官方记录 508.15 秒、58 条公开消息，以用户停止对话结束。15 次查询和 6 次工具解锁完成，争议、补卡、提额均无业务写入回执。[官方评分与轨迹](../../../logs/hub-policy-bindings-task054-01/episodes/task_054/result.json)

## 实现

Hub 在形成工具提案前，使用现有 S2 从可见政策和已加载指南中独立提取候选义务，校验引文后编号。工具提案分别提交最终参数的来源和业务条件的条款映射。控制器检查参数集合、引用、可直接比较的字面值、事实来源和未映射条款。Jev 核查对象、取值语义、条款覆盖和原始政策中可能遗漏的要求。对同一上下文下仅改写措辞、条款与证据映射未改变的被拒提案，停止重复审查。独立抽取使用同一 S2 模型并计入既有预算。实现未读取参考动作或官方数据库目标。[控制入口](../python/episode_controller.py) · [证据检查](../python/dispatch_policy.py)

## 对照验证

完整回归 130 项通过。独立的四项合成对照固定工具与候选提案，用真实 S2 抽取政策、真实 Jev 审查、本地 Java/Go 控制链派发到模拟队列。授权和目标正确时派发一次并取得成功回执。换成另一客户编号时在参数绑定处阻断。缺少同意时定位到授权条款 P1。遗漏新增主管审批时定位到未映射的 P2。后三项派发均为零。[合成结果](../../../logs/hub-policy-four-witnesses-02/summary.json) · [可复执行的检查脚本](../tests/diagnostics/check_dispatch_policy.py)

## 实际阻塞

- 第一次登记的候选清单有 39 条，38 条与引用来源逐字匹配，一条不匹配，清单被整体拒绝。[抽取记录](../../../logs/hub-policy-bindings-task054-01/episodes/task_054/hub-control/controller/control-replay/providers/000056.json)
- 第二次登记抽出 7 条，均能在原文定位。S2 提供了 7 个参数绑定。修订后仍因 P3“确认具体提额金额”未被覆盖而拒绝。这个条款来自当前可见指南，但约束的是提额操作。当前实现把入选清单的每条义务都视为本次登记必须满足的前提。属于适用范围误判。[独立清单](../../../logs/hub-policy-bindings-task054-01/episodes/task_054/hub-control/controller/control-replay/providers/000057.json) · [修订提案](../../../logs/hub-policy-bindings-task054-01/episodes/task_054/hub-control/controller/control-replay/providers/000059.json)
- 争议提交也在提取政策时因引文无法核对被阻断。该次官方运行没有验证复杂写操作的放行路径。冻结代码离线重放通过，共 114 个事件、141 条提供方记录，抑制 21 次工具派发，外部推理及官方银行调用均为零。[重放结果](../../../logs/hub-policy-bindings-task054-replay-01/result.json)

后续可用独立的多业务合成样本检验两项改动：给原文片段分配稳定引用，让模型选择片段；再逐条判断其适用的操作与阶段。验收应同时覆盖“无关条款不能阻断当前操作”和“真正适用的新条款不能被跳过”。
