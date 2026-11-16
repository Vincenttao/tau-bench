# DeepAgent＋Todo＋Skill/MCP 实验

代码、Skill、报告和运行证据集中在本目录。`python/`、`java/`、`skills/`、`tests/` 是本实验源文件；项目根目录的同名入口保留兼容链接。共用的官方episode、监督器、指标采集器及Java构建位于tau3根目录。

从tau3根目录执行：

```bash
.venv312/bin/python experiments/deepagent-todo-skill-mcp/python/run_deepagent.py \
  --output experiments/deepagent-todo-skill-mcp/runs/live-NEW \
  --task-ids task_001 task_041 --execute
```

不加`--execute`只生成计划。输入API key时不回显、不落盘。网络和本机MCP服务测试按项目要求在沙箱外执行。每次使用新输出目录，保留失败尝试。

当前MCP Server按官方初始暴露的工具名逐项注册，不向模型直接注册底层银行工具。MCP各工具保留官方参数schema在`arguments`字段内，外层携带会话和Skill调用标识；这是本评测适配契约。隐藏业务能力仍走官方发现和解锁工具，不将隐藏全集提前暴露。

当前可执行Skill ID仍是`banking-mcp`。`dispute-processing`是随入口一起加载的业务指南，尚无独立的逐Skill权限配置。`python/skill_assets.py`统一生成实际注入文本；冻结manifest同时记录两份Skill文档及加载器hash。模型可调用工具仍为Skill入口、Skill读取、Todo及ask_user。

- `runs/protocol-a06/result.json`：最新文档加载与真实Java/MCP确定性集成验证，使用合成业务数据和本机模拟模型。
- `runs/live-a03/`：更新文档后的真实DeepSeek银行端到端验证，原始状态和评分见各episode。
- `reports/`：设计、实现说明及本轮结果。

历史基线位于`../baseline-native-skill/runs/`，根目录`runs/`兼容入口保留。历史manifest和原始运行证据未因搬迁而重写。

## 第一轮分类抽样已完成

正式批次为 `runs/round-01-20261115-a00`：11类各2题，共22次唯一尝试。21题已评分，12题通过、9题失败；062用户模拟器空消息异常未评分，审查后仅继续未开始题，未重试。已评分通过率57.14%，通过题/计划22题覆盖口径54.55%。总墙钟4427.75秒，已观测20,390,417 Token。

[本轮执行报告](reports/round-01-20261115-a00/本轮执行报告.md) · [人工核查与建议](reports/round-01-20261115-a00/人工核查与建议.md) · [81卡缺失矩阵](reports/round-01-20261115-a00/指标缺失矩阵.md) · [完成审计](reports/round-01-20261115-a00/completion-audit.json)。每题一次，不能验证重复轨迹一致性或长期稳定性。
