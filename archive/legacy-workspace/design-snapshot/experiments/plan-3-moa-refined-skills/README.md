# MOA Banking Orchestration

本方案四方案对比的权威入口：[详细测试设计](test-design.md)。共同条件采用英文22题各一次；下方旧中文或多轮专项设计独立保留，不自动执行。

本目录研究并规划“慢意图识别 → 独立业务 Agent → Todo → 挂起 → 处理依赖 → 接续原任务”的完整银行测试。

**状态：方案已建立，执行器及远端恢复扩展尚未实现，未启动模型测试。** 当前 MOA 可复用慢路径规划和委派，但不能直接承诺远端任务自动接续。既有 DeepAgent 测试保持暂停，历史结果不改写。

- [场景设计](scenario-design.md)：用户流程、需求映射及验收边界。
- [技术详细设计](technical-design.md)：接口、状态机、持久化、Runtime部署与故障处理。
- [设计评审](reports/design-review.md)：已修订问题和实施前门禁。
- [架构与实施方案](architecture.md)：五项要求、源码证据、接口、状态归属及改造位置。
- [测试方案](test-plan.md)：分阶段门禁、官方评分与恢复验收、运行和产物要求。
- [源码评审](reports/source-review.json)：按 Calling/Delegation/Coordination 规则记录发现和限制。
- [实验设计配置](config/experiment.json)：设计数据，不是 MOA 可直接加载的 application.yml。
- [恢复接口草案](contracts/task-continuation.schema.json)：待实现契约，不是现有 MOA/A2A API。
- [场景清单](plans/scenarios.json)：完整流程及负向专项。
- [22 题范围](plans/banking-cohort.json)：复用已选定题号与官方中文题目摘要，不带答案。

目录和新能力使用有含义的英文 kebab-case；不新建数字版本目录。`runs/` 存本地原始轨迹并由 Git 忽略；`reports/` 只保留脱敏汇总和精选证据。方案中的模拟场景必须标注 synthetic，不混入官方分数。
