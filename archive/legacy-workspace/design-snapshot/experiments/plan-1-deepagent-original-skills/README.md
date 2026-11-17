# 方案 1：DeepAgent + 原始 Skill

本方案四方案对比的权威入口：[详细测试设计](test-design.md)。共同条件采用英文22题各一次；下方旧中文或多轮专项设计独立保留，不自动执行。

稳定标识：`plan-1-deepagent-original-skills`。

- [方案配置](plan.json)：显式固定 Skill 发布及清单 hash。
- [共享实现](implementation/)：两个 DeepAgent 方案使用同一份代码。
- [Skill 资产](skill-release/)：本方案绑定 `1.0.0`，不要通过默认版本推断。
- [历史记录](../../archive/deepagent-history/)：历次诊断，不是正式四方案结果。

当前未启动新测试。旧英文入口可使用 `python python/run_deepagent.py --skill-version 1.0.0 --output <全新目录>` 生成计划；不要省略版本。正式对比还需统一基准、语言、系统提示词和用例，不能直接使用不同历史批次的成绩。
