# 方案3：现有MOA银行接入

2026-11-17范围更新：以agent-solution现有MOA机制为准，不新增远端恢复协议、动态依赖调度器或任务事务账本。保留七领域银行适配及既有slow-only实验裁剪；后者不同于上游默认快慢路由。

- [测试设计](test-design.md)：22个细化用例，20核心阻塞、1模型观察、1可选本地暂停专项。
- 面向业务汇报可使用[八页图解 PDF](reports/moa-testing-briefing-20261118.pdf)或[可编辑的汇报稿](reports/moa-main-task054-debug-retrospective-20261117.md)。工程核查可查阅[技术复盘](reports/moa-debug-technical-notes-through-v10.md)和[逐题回归结果](reports/moa-v10-three-case-regression.md)。
- [本次范围修订与剩余调整](reports/native-moa-scope-20261117.md)：上游依据、退出项和验证边界。
- [实现检查与修订结果](reports/implementation-check-20261117.md)：MAIN提示词、确认条件、只读采集及真实Runtime补参验证。
- [技术接入与能力边界](technical-design.md)、[架构](architecture.md)、[业务场景](scenario-design.md)。
- [执行计划](test-plan.md)、[实施任务](implementation-plan.md)、[准备度](readiness-report.md)。
- [两次真实pilot失败复盘](reports/moa-pilot-review-20261117/review.md)：事实与评分保持不变，旧扩展建议以本次范围为准。
- [独立配置](plan.json)、[共同测试契约](../../studies/banking-architecture-comparison/test-design.md)。

```bash
python experiments/plan-3-moa-refined-skills/prepare.py --output experiments/plan-3-moa-refined-skills/runs/new-input-check
```

只生成输入准备记录，不调用模型。正式执行与比较开关仍关闭。已有八Runtime及单题链路不代表完整验收；不把原生问答续接等同远端检查点恢复。

旧扩展设计保存于 reports/design-history/20261117-before-native-scope；旧恢复schema退出当前范围。历史run、原始分数、冻结资产均保留。
