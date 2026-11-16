# DeepAgent＋Todo＋Skill/MCP 实验

代码、Skill、报告和运行证据集中在本目录。`python/`、`java/`、`skills/`、`tests/` 是本实验源文件；项目根目录的同名入口保留兼容链接。共用的官方episode、监督器、指标采集器及Java构建位于tau3根目录。

当前实验入口：[v0.4](v0.4/README.md)，包含[测试方案与架构评审](v0.4/测试方案与架构评审.md)及实验描述。基于 Skill 3.0.0，区分已实现的单 Agent/统一执行边界与待验证的业务效果，给出七能力覆盖、逐层判定和 v1/v3 配对方案。配对控制器及新增场景待实施，不把方案当作已有测试成绩。

从tau3根目录执行：

```bash
.venv312/bin/python experiments/deepagent-todo-skill-mcp/python/run_deepagent.py \
  --output experiments/deepagent-todo-skill-mcp/runs/live-NEW \
  --task-ids task_001 task_041 --execute
```

不加`--execute`只生成计划。输入API key时不回显、不落盘。网络和本机MCP服务测试按项目要求在沙箱外执行。每次使用新输出目录，保留失败尝试。

当前MCP Server按官方初始暴露的工具名逐项注册，不向模型直接注册底层银行工具。MCP各工具保留官方参数schema在`arguments`字段内，外层携带会话和Skill调用标识；这是本评测适配契约。隐藏业务能力仍走官方发现和解锁工具，不将隐藏全集提前暴露。

当前可执行Skill ID为`banking-mcp`。默认发布版本3.0.0按信用卡、支付结算、账户和争议领域组织七项业务指南；模型按入口条件读取`guides/<领域>/<业务>.md`。版本1.0.0保留第一轮原始合并文档，2.0.0保留三指南开发快照。新manifest锁定版本与hash，执行前验证；历史manifest不改写。设计与复原命令见[银行业务Skill设计](skills/README.md)。逐指南独立权限和完整业务前置状态机尚未实现。


- `runs/protocol-a06/result.json`：历史文档加载与真实Java/MCP确定性集成验证，使用合成业务数据和本机模拟模型。版本 1.0.0/3.0.0 的后续离线检查见[验证摘要](../../evidence/skill-release-validation-20261116.json)。
- `runs/live-a03/`：历史文档调整后的真实DeepSeek银行端到端验证，原始状态和评分见各episode；不是 Skill 3.0.0 的业务验证。
- `reports/`：设计、实现说明及本轮结果。

历史基线位于`../baseline-native-skill/runs/`，根目录`runs/`兼容入口保留。历史manifest和原始运行证据未因搬迁而重写。

## 第一轮分类抽样已完成

正式批次为 `runs/round-01-20261115-a00`：11类各2题，共22次唯一尝试。21题已评分，12题通过、9题失败；062用户模拟器空消息异常未评分，审查后仅继续未开始题，未重试。已评分通过率57.14%，通过题/计划22题覆盖口径54.55%。总墙钟4427.75秒，已观测20,390,417 Token。

[本轮执行报告](reports/round-01-20261115-a00/本轮执行报告.md) · [人工核查与建议](reports/round-01-20261115-a00/人工核查与建议.md) · [81卡缺失矩阵](reports/round-01-20261115-a00/指标缺失矩阵.md) · [完成审计](reports/round-01-20261115-a00/completion-audit.json)。每题一次，不能验证重复轨迹一致性或长期稳定性。
