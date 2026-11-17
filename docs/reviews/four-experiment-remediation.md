# 四实验设计复审整改记录

日期：2026-11-16。对应[复审R1–R8](four-experiment-design-review.md)。本次修订设计、准备校验与离线规则，不启动正式测试。四方案comparison_ready和execution_enabled继续为false。

| 问题 | 已完成 | 验证/剩余边界 |
| --- | --- | --- |
| R1 配置冲突 | 严格Schema、arm_bindings、版本/路径/内容绑定、题数/次数/模式/预算/模型条件联合校验 | 原两个漏洞及新增负例被拒绝；四正常配置通过。D2制品和运行环境冻结仍待接线 |
| R2 MOA覆盖 | 官方69项操作静态归属、用户/Agent边界、22题评估端覆盖表；补齐奖励/ATM/利息及身份服务职责 | 源码清单一致性、唯一写归属规则和覆盖检查通过；真实路由/权限执行未验证 |
| R3 停止范围 | episode/arm/study分级；暂停、在途未知、恢复和截断统计规则 | 离线范围选择负例通过；真实调度与停止确认未接线 |
| R4 预算计量 | 外层deadline、内层调用上限、SDK/网关重试、暂停计时、跨重启剩余预算及全层计量 | 离线超时/上限/暂停判定通过；deadline传播及在途请求取消未验证 |
| R5 门禁冲突 | 各方案执行步骤与共同D1统一；blocking契约和模型行为观察分离 | 38个检查有stage/blocking/定义；原始Skill普通业务错误不得因放行被修改 |
| R6 指标与判断 | 主指标pass/22，固定三个对照；覆盖不下降、严重违规和截断约束；成本独立 | 三种预设结果演算通过；不承诺单轮泛化或稳定性 |
| R7 独立判定 | 38项检查、23个Hub CT、独立程序及12个合成正反例，记录驱动和证据状态 | 离线判定器通过；真实组件driver全部仍待接线，不能视为运行验收闭合 |
| R8 Hub范围 | 核心CT保留；CT14/23改为本轮禁用证明门禁，完整专项保留 | 禁用仍需真实证据，不能仅凭配置宣称通过；不增加本轮88次规模 |

## 关键资产

- [执行与验收契约](../../studies/banking-architecture-comparison/execution-contract.md)：共同规范。
- [严格准备校验](../../shared/python/experiment_plan.py)、[实验Schema](../../studies/banking-architecture-comparison/schemas/plan.schema.json)、[共同Schema](../../studies/banking-architecture-comparison/schemas/study.schema.json)。
- [69项操作归属](../../studies/banking-architecture-comparison/contracts/business-ownership.json)及[22题覆盖](../../studies/banking-architecture-comparison/contracts/cohort-coverage.json)。覆盖表仅评估端使用，不向Agent暴露task ID路由提示。
- [验收矩阵](../../studies/banking-architecture-comparison/contracts/acceptance-matrix.json)、[离线正反例](../../studies/banking-architecture-comparison/contracts/oracle-fixtures.json)、[独立规则程序](../../shared/python/study_policy.py)。
- [新增回归](../../shared/tests/test_experiment_contract.py)、[验证记录](four-experiment-remediation-validation.json)。

## 验证结果

共享回归40项全部通过（含新增9个测试方法及其多组负例）。四方案均重新生成准备记录，executable=false；69项操作/22题/38项检查/23项Hub契约及12个离线oracle验证通过。没有调用外部模型，没有改写旧Skill发布或历史轨迹，没有构建/运行完整MOA或Hub。

离线负例至少覆盖：版本与清单不一致、配置次数矛盾、模式/语言/seed/提示词冲突、缺字段、未知字段、预算不一致、重复方案、总位置数不守恒、合法请求全拒、固定allow、伪完成、恢复创建新任务、重复写入、暂停后派发及提前截断排名。

本次新增内部模型请求保护上限512次/题是设计值，计入所有层和模拟器；不是实测最优值，不是Token预算。执行前应在D2正式冻结并验证，不能临时放宽来提高通过率。

## 下一实施阶段

把上述契约接入四个真实运行适配器、服务端权限和效果边界；补齐每项driver的独立故障注入证据；验证deadline/暂停/重启后的控制行为；完成完整制品、政策、数据和评分器冻结。此前的设计问题已具体化，但运行时验证缺口仍明确保留，不能直接进入88次正式执行。
