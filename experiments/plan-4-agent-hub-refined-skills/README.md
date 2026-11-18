# 方案 4：plan-4-agent-hub-refined-skills

最新交付：[003/054逐轮失败分析与第一组TDD修复](reports/failure-analysis-003-054-20261118/README.md)。覆盖136条官方消息，确认审查意见曾被格式化为用户回答，并修复来源隔离、上下文提案归并和旧问题生命周期。118项Python回归、Java4项来源检查及拒绝问询后的完整原生恢复夹具通过；本轮未重跑官方评分。

上一阶段见[控制链重放、输入绑定与验收记录](reports/control-replay-and-routing-20261118.md)：109项Python测试通过，已增加整链隔离重放、无效提案澄清、格式引用绑定、审计故障停止和模型工作目录去标识化。真实模型探针、原生恢复、官方接线与业务评分分别报告；完整39项发布验收及正式比较仍未开启。

当前独立运行器见[运行说明](python/RUNTIME.md)。`FullHubAgent`已连接Java持久任务、S2、Jev、原生DeepAgent/Skill/Todo、Go Hub和官方工具环境。执行链通过、业务完成和完整设计发布验收是不同结论。

下面的阶段报告保留其历史范围，状态以各报告日期为准：

最新接线与验收：[Java/Jev/Go控制链阶段报告](reports/controlled-chain-acceptance-20261117.md)。真实Jev＋隔离官方工具实现的单项提交链通过，多意图恢复仍进入未决；DeepAgent正式driver、完整政策及目标验收尚未接齐，完整方案未通过验收。历史报告保持各自证据范围。

J1进展：[输入路由提案](python/INPUT_ROUTING.md)完成离线TDD，[本轮记录](reports/input-routing-tdd-20261117.md)包含22项Python测试和43条Java断言。新增组合意图、暂缓、模型版本绑定和未决分支；正式driver接线仍待完成。

新版开发：[J0持久任务协调器](java/README.md)已有独立Java实现，[首轮TDD记录](reports/task-coordinator-tdd-20261117.md)包含41条断言及8项既有Python回归结果。尚未接入Jev输入路由、DeepAgent或Go效果边界，完整方案继续待验收。

Jev 原生接口进展：[接入与图片验证报告](reports/jev-native-integration.md)。6次合成推理已完成，实际响应为 `jev-1.14.0`；尚未接入Hub采纳/派发或正式银行测试，图片扩展不改变22题文本基准。

实施基线：[LLM Evidence Control测试方案](plans/llm-evidence-control/test-design.md)、[设计规格](plans/llm-evidence-control/test-spec.json)与[设计复核](plans/llm-evidence-control/design-review.md)。目标是执行既定22题，覆盖每轮输入解释、子目标推进、Jev/S1判断、Hub控制及官方结果验收；不扩展成手机银行产品。完整控制运行器已用于独立诊断，设计规格中的正式发布开关保持关闭。下列原方案设计和只读pilot保留为历史基线。

先读[本方案准备报告](readiness-report.md)：区分本方案已有证据、专属缺口、共同依赖与下一放行条件。

- [详细测试设计](test-design.md)：目标、链路、用例、断言、失败标准与实施缺口。
- [独立配置](plan.json)：固定本方案身份及 `banking-evidence-guides` Skill。
- [共同测试契约](../../studies/banking-architecture-comparison/test-design.md)：英文22题，每方案每题一次。
- [Hub 技术设计](design/README.md)。

## 新入口

从仓库根目录运行：

```bash
python experiments/plan-4-agent-hub-refined-skills/prepare.py --output experiments/plan-4-agent-hub-refined-skills/runs/input-check
```

只核验题集、Skill和方案身份，生成 `preparation.json`。不会调用模型，不是业务执行或构建通过。输出目录必须不存在。旧执行器已归档，无兼容入口。

正式单题运行和四方案调度仍需实现/接线，`comparison_ready=false`、`execution_enabled=false`。历史分数不自动属于本方案。

实施任务、依赖和交付标准见[本方案实施细化](implementation-plan.md)。

## TDD 开发更新（2026-11-17）

已实现实际 Go 控制组件、独立进程和只读官方链路 pilot；银行写入的证据判断及完整控制契约仍未完成，不得回退为普通 DeepAgent。

前述准备状态保留为设计基线。当前实现、实测范围与未完成项见[统一开发进展](../../studies/banking-architecture-comparison/reports/tdd-integration-progress.md)，结果见[诊断索引](../../studies/banking-architecture-comparison/reports/tdd-run-index.json)。`prepare.py` 仍只准备输入，正式执行开关保持关闭。
