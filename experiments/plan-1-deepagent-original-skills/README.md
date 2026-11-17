# 方案 1：plan-1-deepagent-original-skills

先读[本方案准备报告](readiness-report.md)：区分本方案已有证据、专属缺口、共同依赖与下一放行条件。

- [详细测试设计](test-design.md)：目标、链路、用例、断言、失败标准与实施缺口。
- [独立配置](plan.json)：固定本方案身份及 `1.0.0` Skill。
- [共同测试契约](../../studies/banking-architecture-comparison/test-design.md)：英文22题，每方案每题一次。
- [共享组件](../../shared/README.md)。

## 新入口

从仓库根目录运行：

```bash
python experiments/plan-1-deepagent-original-skills/prepare.py --output experiments/plan-1-deepagent-original-skills/runs/input-check
```

只核验题集、Skill和方案身份，生成 `preparation.json`。不会调用模型，不是业务执行或构建通过。输出目录必须不存在。旧执行器已归档，无兼容入口。

正式单题运行和四方案调度仍需实现/接线，`comparison_ready=false`、`execution_enabled=false`。历史分数不自动属于本方案。

实施任务、依赖和交付标准见[本方案实施细化](implementation-plan.md)。

## TDD 开发更新（2026-11-17）

已完成原始 Skill 的真实单题执行链核查；业务 reward=0 如实保留。正式比较尚未放行。

前述准备状态保留为设计基线。当前实现、实测范围与未完成项见[统一开发进展](../../studies/banking-architecture-comparison/reports/tdd-integration-progress.md)，结果见[诊断索引](../../studies/banking-architecture-comparison/reports/tdd-run-index.json)。`prepare.py` 仍只准备输入，正式执行开关保持关闭。
