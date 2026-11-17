# 四个测试方案

1. [方案 1：DeepAgent + 原始 Skill](plan-1-deepagent-original-skills/)：`shared-runner-available`。
2. [方案 2：DeepAgent + 优化 Skill](plan-2-deepagent-refined-skills/)：`shared-runner-available`。
3. [方案 3：完整 MOA + 优化 Skill](plan-3-moa-refined-skills/)：`design-only`。
4. [方案 4：Agent Hub + 优化 Skill](plan-4-agent-hub-refined-skills/)：`design-only`。

每个目录都有 plan.json，固定方案身份与 Skill。旧名称软链接仅供历史记录及命令兼容，不是额外方案。所有方案 comparison_ready=false；目录整理不代表正式对比已完成。

## 详细测试设计

四方案各有独立 `test-design.md`；共同入口见[统一测试设计](../studies/banking-architecture-comparison/test-design.md)，[设计检查与修订记录](../studies/banking-architecture-comparison/design-review.md)。正式设计为英文22题×4方案×1次，共88个位置，尚未执行。
