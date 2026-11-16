# 银行业务 Skill：设计、版本与复原

## 业务设计

业务部门负责归属和维护，具体办理目标决定业务 Skill 边界。业务说明包含使用条件、必要信息、授权要求、办理步骤、成功凭据及异常出口。一个部门可以维护多项能力。

当前默认版本为 **3.0.0**，实际发布内容见 `releases/3.0.0/`。

最新可选发布为 **3.2.0**。本次中文单题复验显式选择该版本；通用入口默认 3.0.0、中文入口默认 3.1.0 保留，避免已有命令隐式改变测试条件。

| 领域 | 业务能力 | 指南（相对于 banking-mcp） |
| --- | --- | --- |
| 信用卡 | 信用卡申请与产品选择 | guides/credit-card/card-application.md |
| 信用卡 | 额度调整 | guides/credit-card/limit-adjustment.md |
| 支付结算 | 转账办理 | guides/payments/transfer.md |
| 账户 | 开户 | guides/accounts/account-opening.md |
| 账户 | 销户 | guides/accounts/account-closure.md |
| 争议 | 交易争议申诉 | guides/disputes/transaction-dispute.md |
| 账户 | 其他账户/卡变更 | guides/accounts/account-changes.md |

`catalog.json`记录能力ID、领域、建议责任角色、文档路径和执行边界；角色尚需项目登记具体责任人。业务负责人维护规则和验收，IT接口负责人维护operation、Schema及权限，平台负责人维护执行与证据记录。

目前这些是可独立维护和按需读取的业务指南，由同一个Agent通过`skill_tool`加载，统一使用`invoke_skill(skill_id=banking-mcp, ...)`执行。尚未实现逐业务Skill独立的权限、Agent或状态机。MCP工具由多项业务能力复用，不能按指南标题推断某个业务已获工具支持。

产品范围、金额阈值、资格和权限从授权政策与系统读取。指南不写入隐藏评分答案。转账成功不等于销户完成，申请受理不等于批准，争议提交不等于退款到账。组合目标要分别核验依赖和结果。

## 版本设计

| 版本 | 内容 | 证据 |
| --- | --- | --- |
| 1.0.0 | 原始入口与争议指南合并文本 | 从第一轮冻结源码重建，并与该轮全部已有部署文档逐字节比对一致；是补登记版本，不改写历史manifest |
| 2.0.0 | 产品咨询、争议、账户变更三份按需指南 | 上一次开发调整的快照；没有正式业务成绩 |
| 3.0.0 | 本次按领域组织的七项业务能力 | 默认新版本；业务有效性需独立测试 |
| 3.1.0 | 七项业务指南不变；入口答复语言服从会话与官方语言指导 | V0.4 中文端到端入口显式选择；原入口默认仍为 3.0.0 |
| 3.2.0 | 提额、争议、账户/卡变更三指南新增独立前置 Todo、证据要求、写入阻断和跨业务依赖；其余资产不变 | 中文入口显式选择；[组合题单次官方通过](../v0.4/reports/zh-skill32-20261116-a00/Skill3.2复验报告.md)，Todo 收尾和答复状态仍有缺口 |

每个版本包含`release.json`，列明文件清单及SHA-256。加载时核对版本、路径、全部文件哈希和额外文件。发布后不原地编辑旧版本；修改应复制为新版本、评审后生成新清单。实验阶段显式选择新版；默认版本升级需单独说明，避免旧命令静默改变。哈希提供一致性检查，不等于数字签名或审批证明。

`skill_assets.py`是唯一运行加载入口。顶层旧`banking-mcp/`和`dispute-processing/`路径保留迁移材料，不参与版本加载；权威资产在`releases/`。

新manifest记录`skill_release.version`、发布清单hash和所有文件hash。episode执行前按manifest验证并选择版本；Java会话的assembly事件再次记录版本和部署指南hash。新轮次freeze-sources同时保存Markdown及JSON发布清单。旧批次仍使用原始快照，不重写其成绩或元数据。

## 选择与导出

在仓库根目录执行；以下只生成计划，不调用模型：

```bash
.venv312/bin/python python/run_deepagent.py --skill-version 3.0.0 --output experiments/deepagent-todo-skill-mcp/runs/business-v3-plan --task-ids task_003
```

需要对照旧Skill文本时，选择`--skill-version 1.0.0`并使用另一个新输出目录。所有新运行仍走当前执行器，因此只能称为“旧Skill文本对照”，不能称为原始实验的完整复现。真实执行额外使用`--execute`并满足项目测试门槛。

独立导出旧版（目标必须不存在，不覆盖当前工作树）：

```bash
python python/skill_assets.py --version 1.0.0 --export /tmp/tau3-skill-1.0.0
```

输出包括`banking-mcp/SKILL.md`和`release.json`。导出只是资产恢复，不会启动实验或修改原运行目录。也可通过`TAU3_SKILL_VERSION`选择版本；显式runner参数和执行manifest优先。

## 能否恢复原来的测试条件

**Skill文本可以精确恢复；完整测试条件需要逐项复核。** 原项目已有manifest哈希、freeze.json和freeze-sources，但没有显式Skill发布版本或完整二进制归档。Java源码快照不能代替对应class/JAR字节。

只读核查第一轮：

```bash
python python/skill_assets.py --audit-run experiments/deepagent-todo-skill-mcp/runs/round-01-20261115-a00
```

报告区分当前匹配文件、已变化/缺失文件、可从历史源码快照恢复的文件，以及没有匹配快照的文件。每次构建后重新检查；报告是时间点快照。

本次已在隔离目录重建旧Java源码，12个class均与第一轮manifest哈希一致。增加了冻结输入恢复导出（需本地JDK和哈希匹配的依赖）：

```bash
python python/skill_assets.py --restore-run experiments/deepagent-todo-skill-mcp/runs/round-01-20261115-a00 --export experiments/deepagent-todo-skill-mcp/runs/restored-round01-inputs-new
```

目标必须不存在。导出逐一核验freeze清单中的文件；原文件变化时优先读取匹配的源码快照，仅剩class变化时按旧源码重建并比较hash。任何无法匹配的输入都会拒绝完成。`restoration-map.json`记录原路径、恢复路径和hash；原路径外依赖存于`external/<hash>/`。输出是已校验输入归档，尚不是自动可运行的新工作区：旧classpath/manifest保留原绝对路径，迁移运行时必须显式配置；不修改原工作区或旧批次。

完整复现应在独立目录恢复原源码、Skill、依赖、题集、classpath和配置，重新构建后逐个核对制品hash。若class或JAR无法匹配，应标为“重建环境对照”，不能说原条件已恢复。不要把旧freeze校验改成放行当前文件，也不要用新runner对旧manifest直接resume。

模型名称、参数和seed可记录并重设，但远端模型权重、服务状态、抽样及用户模拟过程不能由Skill版本恢复。因此相同输入条件不保证相同轨迹或分数；确定性检查需独立固定响应回放。

## 执行约束和验证边界

当前代码校验Skill ID、操作名、参数、会话、调用ID和重复提交，并禁止自动重放不确定业务写入。指南中的身份核验、业务授权和依赖关系仍需模型遵守官方政策及业务系统执行；没有新增完整业务状态机、逐Skill权限或精确参数确认门槛。

验证顺序为版本/路径回归 → Java构建 → 本地脚本模型与真实MCP协议检查 → 新目录中的业务对照。协议通过证明部署、按需读取、调用链和版本选择可用，不证明业务收益或正式成绩。
