# 四方案对比：目录评审与整理设计

> 后续实施记录：四方案目录与历史归档已落地，见[迁移清单](directory-migration.json)和[验证记录](directory-migration-validation.json)。下文保留迁移前的评审及长期目标；公共根目录代码尚未进一步拆分。

核查日期：2026-11-16。本文是目录与实验管理设计，不是已完成的代码迁移或新的测试成绩。本次没有启动模型、恢复暂停任务、移动历史数据或修改 AGENTS.md。

## 1. 评审结论

现有目录能够保存迭代过程，但不适合直接作为四方案对比的长期结构。主要问题是“实现、实验方案、迭代版本、运行批次”混用目录层级，结果归属容易被目录名称误导。根目录文件多数有历史用途，不能按名称陌生就删除。

| 发现 | 影响 | 建议 |
| --- | --- | --- |
| `baseline-native-skill` 使用 NativeSkillAgent | 容易误当作方案 1，实际上同时改变了 Agent 架构 | 单列历史参考，不纳入四方案主对比 |
| 同一 DeepAgent 目录包含原始及多次优化 Skill | 方案 1、2 没有稳定身份 | 共用一份实现，使用两个显式实验配置 |
| `v0.4` 内嵌 plans/reports/runs，其他实验直接放在根层 | 工具发现和导航规则不一致 | 新实验统一层级；旧路径保持可读 |
| Agent Hub 目录存在尚未接入 Hub 的 DeepAgent 测试结果 | 目录名不能证明实际使用的架构 | 运行记录显式填写实际组件、实验用途和所属方案 |
| 根目录混合源码、文档、兼容链接和生成目录 | 很难找到权威入口 | 按职责收敛根目录，并保留迁移映射 |
| MOA 计划采用中文新基准，Hub 最新计划采用英文旧基准 | 不能直接横向比较成功率 | 在共同研究批次中统一基准、语言和任务快照 |

## 2. 四个方案的稳定定义

| 展示名称 | 稳定英文 ID | 实现及 Skill | 当前状态 |
| --- | --- | --- | --- |
| 方案 1 | `deepagent-original-skills` | DeepAgent + 原始 Skill 文本 | 执行器及历史 1.0.0 资产可用；尚未形成统一四方案批次 |
| 方案 2 | `deepagent-refined-skills` | 同一 DeepAgent + `banking-evidence-guides` | 已有运行记录，需按共同条件重新归组 |
| 方案 3 | `moa-refined-skills` | 完整 MOA + 优化 Skill | 设计阶段，配置明确 implementation_ready=false |
| 方案 4 | `agent-hub-refined-skills` | 实际接入 Agent Hub 控制链 + 优化 Skill | 最新设计明确 executable=false；尚无增强成绩 |

原始 Skill 建议锁定历史 `1.0.0` 的文件清单和 hash，它由第一轮冻结文本重建。这个名称仅保留历史身份；以后使用有含义的英文名称。使用旧文本与当前执行器进行测试，不等于完整复现原始测试环境。

`banking-evidence-guides` 是历史 3.2.0 英文业务资产的语义命名发布。方案 2、3、4 应引用同一资产 hash。MOA 将指南分配给业务 Agent 所需的包装、权限和提示词必须另行记录，不能无记录地改写业务内容。

## 3. 建议的目标目录

以下是迁移目标，不表示这些执行模块已经存在。方案是配置；实现是代码；研究批次固定共同条件；运行目录保存一次执行的证据。

```text
AGENTS.md
README.md                         # 总入口：方案、命令、资料和结果索引
docs/                             # 架构、指标、采集方法、历史设计
implementations/
  deepagent/                      # 方案 1、2 共用，不复制两份代码
  moa/
  agent-hub/
  native-skill/                   # 历史参考实现
shared/                           # 经确认可复用的基准桥接、评分、观测
tools/                            # 诊断、报表、迁移和计划生成工具
viewer/                           # 轨迹工作台
skills/releases/                  # 不可变发布及文件 hash
experiments/                      # 四个稳定方案的配置和专属说明
  deepagent-original-skills/
  deepagent-refined-skills/
  moa-refined-skills/
  agent-hub-refined-skills/
studies/banking-architecture-comparison/
  study.json                      # 共同条件、方案绑定、运行策略
  cohort.json                     # 唯一任务清单及输入 hash
  reports/                        # 可提交的对比报告
  evidence/                       # 精选证据和来源索引
runs/<study-id>/<arm-id>/<run-id>/ # 原始数据，本地保留，不提交
config/                           # 非敏感配置模板
tests/                            # 共享回归；实现专属测试随实现保存
```

共同研究批次下可以各跑一次，每题每方案一次；不因为目录设计而增加重复次数。诊断重跑另建批次并标记用途，不覆盖正式结果。英文和中文应分别建立研究批次，不能混在同一成功率中。

## 4. 根目录现有内容如何归位

| 当前内容 | 目标及处理原则 |
| --- | --- |
| `python/` | 逐文件分到 shared、tools 或所属实现；不能整目录一刀切 |
| `java/` | NativeSkillAgent 桥接归 historical/reference 实现；先检查其他适配器对它的依赖 |
| `enterprise-java/`、`replay-java/` | 按实际 Runtime 集成与固定响应回放职责归位，不能直接改名为 MOA 完整实现 |
| `experiments/deepagent-todo-skill-mcp/{python,java}` | 归 implementations/deepagent；原入口暂留兼容包装 |
| 原实验下 `skills/releases/` | 归统一 Skill 资产库；核验所有发布文件 hash，不修改历史内容 |
| 根目录指标卡、采集方法、执行计划、中文用例说明 | 归 docs 相应主题；明确历史版本及权威入口 |
| 根目录四个 DeepAgent 文档软链接、`tau3-local-guide.md` | 主导航收敛到 README；引用更新后再移除冗余入口 |
| `reports/`、`evidence/`、实验内历史报告 | 保持历史归属；新报告统一按 study 归档并建立索引 |
| `reports/banking-cases-zh/build_catalog.py` | 报告生成代码归 tools，生成结果与源码分离 |
| `runs`、`python/run_deepagent.py`、`skills/banking-mcp` 等软链接 | 先登记目标和使用方；它们是兼容入口，不是多余副本 |
| `.deps/`、`.venv*/`、`logs/`、Java target | 本地依赖、环境及产物继续忽略，不纳入源码整理提交 |

不要把所有旧内容塞入一个无说明的 archive。每次迁移应记录“旧路径 → 新路径 → 用途 → 兼容入口 → 验证结果”。

## 5. 对比所需的最低实验契约

每个批次固定：benchmark commit、数据/任务 hash、语言及本地化开关、用例集合、seed、模型请求名与实际响应版本、用户模拟器、检索方式、工具定义、评分器、超时/步数/Token 预算和并发度。运行保存代码提交与未提交变更快照、Skill 清单 hash、系统提示词 hash、实际启用组件及执行入口。

方案 1 对方案 2 若要衡量“只改 Skill”的收益，必须使用相同 DeepAgent 代码和系统提示词。若同时改变提示词，应标记为组合优化，不能只归因于 Skill。方案 2 对方案 3、4 衡量整体架构方案效果；额外规划/控制模型、上下文包装和工具限制均须披露。

结果统一保存：official reward、是否成功评分、终止原因、业务失败/基础设施失败分类、墙钟耗时、全部组件与模拟器的 Token、工具调用、恢复次数、证据位置。明确分母，同时报告全体计划任务完成情况和已评分任务成功率，不能悄悄排除未评分样本。官方分数与人工业务解释分别展示。

并发执行必须隔离每个 episode 的银行数据、会话、Todo、检查点、MCP 队列及日志。相同并发度仍不保证相同吞吐；记录全局模型限流和机器资源。恢复/暂停验收是独立结构性指标，不能只凭最终 reward 证明。

Git 提交计划、代码、配置模板、报告和精选证据；原始轨迹、完整模型回包、缓存、凭证继续排除。另一台设备仅拉 Git 只能看到已提交的资料；要显示完整对话，需要另行同步经过检查的轨迹导出包，不能仅凭一个报告链接承诺可见。

## 6. 分阶段迁移与验收

1. **先建立索引与实验身份。** 不移动历史产物，为四方案登记当前入口、资产和实现状态；新批次使用统一 manifest。现有诊断成绩不自动变成正式四方案数据。
2. **整理文档和根导航。** 更新引用后移动普通文档；AGENTS.md 保持不变，因此它引用的旧执行计划路径需要兼容入口。保留本地未提交工作。
3. **提取代码和资产。** 按依赖关系逐个迁移，修正 import、Java 构建路径与 runner 的 parents 层级假设，保留旧命令包装。执行受影响的单元测试、计划生成和协议夹具；不自动启动付费模型测试。
4. **升级结果发现机制。** 工作台当前只扫描固定的 runs/manifest 层级；先支持新批次索引并验证新旧轨迹都能打开，再启用新运行目录。根 runs 当前是历史实验的软链接，不能直接把它当新目录写入。
5. **验证再切换。** 确认冻结文件 hash 不变、报告链接有效、原始产物仍被 Git 忽略、四方案入口不会静默回退。完整 MOA/Hub 接入及隔离验收通过后，才开展正式对比。

历史运行含冻结源码、路径引用和暂停恢复状态。不要为美观改写旧 manifest、移动仍需恢复的运行目录或替换其依赖。遗留目录可以继续原位保留，通过索引减少日常导航干扰。

## 7. 核查依据与验证边界

- [当前项目说明](../README.md)及[现有贡献指南](../AGENTS.md)：根目录职责和执行入口。
- [Skill 发布说明](../experiments/deepagent-todo-skill-mcp/skills/README.md)：原始文本、语义发布及复现限制。
- [MOA 配置设计](../experiments/moa-banking-orchestration/config/experiment.json)：设计状态、中文基准和待实现扩展。
- [Hub 最新设计说明](../experiments/agent-hub-banking/v1.1/README.md)及[测试规格](../experiments/agent-hub-banking/v1.1/plans/test-spec.json)：英文基准、实际 Go 接入要求、尚不可执行。
- [Hub 目录中的基线报告](../experiments/agent-hub-banking/v1.0/reports/english-e2e-20261116-task054-a00/端到端验证报告.md)：明确没有接入 Hub 控制链。
- [工作台发现逻辑](../python/trace_viewer.py)、[中文执行器](../experiments/deepagent-todo-skill-mcp/v0.4/run_zh_e2e.py)、[忽略规则](../.gitignore)：目录迁移需要处理的实际约束。

本次完成文件布局、软链接、配置及报告的只读核查，并生成本评审。没有验证迁移后的可执行性，也没有完成四方案运行能力建设。
