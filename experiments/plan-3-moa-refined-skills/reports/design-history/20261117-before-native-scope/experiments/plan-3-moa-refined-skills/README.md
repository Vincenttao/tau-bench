# 方案 3：plan-3-moa-refined-skills

先读[本方案准备报告](readiness-report.md)：区分本方案已有证据、专属缺口、共同依赖与下一放行条件。

- [详细测试设计](test-design.md)：目标、链路、用例、断言、失败标准与实施缺口。
- [独立配置](plan.json)：固定本方案身份及 `banking-evidence-guides` Skill。
- [共同测试契约](../../studies/banking-architecture-comparison/test-design.md)：英文22题，每方案每题一次。
- [MOA 场景与技术设计](technical-design.md)。

## 新入口

从仓库根目录运行：

```bash
python experiments/plan-3-moa-refined-skills/prepare.py --output experiments/plan-3-moa-refined-skills/runs/input-check
```

只核验题集、Skill和方案身份，生成 `preparation.json`。不会调用模型，不是业务执行或构建通过。输出目录必须不存在。旧执行器已归档，无兼容入口。

正式单题运行和四方案调度仍需实现/接线，`comparison_ready=false`、`execution_enabled=false`。历史分数不自动属于本方案。

实施任务、依赖和交付标准见[本方案实施细化](implementation-plan.md)。

## TDD 开发更新（2026-11-17）

已实现八个实际 Runtime、慢路由、英文确认及部分 A2A 官方链路；跨任务 A→B→A 恢复等完整门禁仍未完成，仅可运行明确标记的 pilot。

前述准备状态保留为设计基线。当前实现、实测范围与未完成项见[统一开发进展](../../studies/banking-architecture-comparison/reports/tdd-integration-progress.md)，结果见[诊断索引](../../studies/banking-architecture-comparison/reports/tdd-run-index.json)。`prepare.py` 仍只准备输入，正式执行开关保持关闭。

## 测试设计与真实失败复核（2026-11-17）

测试已细化为 [28个子用例](plans/scenarios.json)（27阻塞、1模型观察），覆盖路由、阶段闸门、唯一调度权威、远端恢复、迟到回执、故障窗口和业务证据。见 [测试设计](test-design.md) 与 [执行门禁](test-plan.md)。

[两次MOA pilot失败复盘](reports/moa-pilot-review-20261117/review.md)提供逐消息证据和严格离线DB重放。该复核不改历史分数，不代表新运行或完整架构通过。
