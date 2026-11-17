# 银行业务 Agent 四方案对比

本仓库用于比较 DeepAgent、完整 MOA 与 Agent Hub 在同一银行任务上的执行效果。当前已按四个方案整理目录；**正式四方案对比尚未运行，MOA 和 Agent Hub 整合仍处于设计阶段。**

## 从这里开始

| 方案 | 目录 | 绑定的 Skill | 当前能力 |
| --- | --- | --- | --- |
| 1：DeepAgent，原始 Skill | [plan-1-deepagent-original-skills](experiments/plan-1-deepagent-original-skills/) | 历史 `1.0.0` 原始文本 | 共用 DeepAgent 执行器 |
| 2：DeepAgent，优化 Skill | [plan-2-deepagent-refined-skills](experiments/plan-2-deepagent-refined-skills/) | `banking-evidence-guides` | 共用 DeepAgent 执行器 |
| 3：完整 MOA，优化 Skill | [plan-3-moa-refined-skills](experiments/plan-3-moa-refined-skills/) | `banking-evidence-guides` | 设计及契约，完整流程待实现 |
| 4：Agent Hub，优化 Skill | [plan-4-agent-hub-refined-skills](experiments/plan-4-agent-hub-refined-skills/) | `banking-evidence-guides` | 实际 Hub 整合待实现 |

每个方案的 `plan.json` 固定身份和 Skill 清单 hash。配置中的 `execution_enabled=false` 表示本次仅登记方案；不是新增执行器的开关。原始 Skill 与优化 Skill 使用同一份 DeepAgent 代码，不复制实现。

## 目录职责

- [experiments/](experiments/README.md)：四方案入口、方案配置和新计划/报告。
- [implementations/](implementations/README.md)：共享实现；DeepAgent 的真实代码位于此处。
- [archive/](archive/README.md)：未压缩的历史计划、报告、证据及本地轨迹。历史 NativeSkillAgent 不属于方案 1。
- [docs/](docs/comparison-directory-review.md)：目录评审；[迁移记录](docs/directory-migration.json)列出旧路径、新路径和字节校验结果。
- `python/`、`java/`、`enterprise-java/`、`replay-java/`：现有公共监督、基准桥接、Runtime 接入和回放代码。它们仍被执行入口依赖，本次保留路径。
- `config/`、`tests/`：公共配置及回归测试。
- [viewer/](viewer/README.md)：轨迹工作台。

根目录旧文档、`runs`、`reports`、`evidence` 及旧实验名是兼容软链接；实际历史文件已归档。新工作请从四方案目录进入，不再新增数字版本目录。AGENTS.md 保持原样。

## 对比规则

统一基准提交、任务集合、会话语言、模型及模拟器、检索、工具、预算、seed 和并发条件后再运行。方案 1、2 若只比较 Skill，系统提示词也必须相同；方案 2、3、4 引用同一优化 Skill 内容，框架适配差异另行记录。

现有中英文批次、失败复验、Hub 目录中的 DeepAgent 基线均属于历史诊断，不能拼接为四方案成功率。官方评分、业务解释、基础设施异常和结构性恢复验收分别报告。

## 本地使用

保留 Python 3.12、JDK 21 和现有依赖环境；环境与构建细节见[历史本地指南](archive/reference-documents/tau3-local-guide.md)。

```bash
# 只生成计划；显式绑定 Skill，并使用全新输出目录
.venv312/bin/python python/run_deepagent.py --skill-version 1.0.0 --output experiments/plan-1-deepagent-original-skills/runs/new-plan
.venv312/bin/python python/run_deepagent.py --skill-version banking-evidence-guides --output experiments/plan-2-deepagent-refined-skills/runs/new-plan

# 公共回归测试，不启动真实模型
python -m unittest discover -s tests -v

# 轨迹工作台（命令参数见 viewer/README.md）
python python/trace_viewer.py --help
```

真实执行需显式 `--execute` 并满足现有前置条件。凭证通过环境注入，不保存到配置、代码或报告。

## 历史数据与同步

归档使用普通目录，不压缩，不覆盖历史 manifest 或结果。原始轨迹、日志、模型回包、依赖和构建产物继续被 Git 忽略；计划、最终报告和精选证据可以提交。因此另一台设备拉取仓库可查看已提交资料，但完整轨迹仍需单独同步。

本次目录迁移未启动或恢复任何测试；保留旧路径不等于已验证暂停进程可以无条件恢复。

## 四方案详细测试计划

[共同测试设计](studies/banking-architecture-comparison/test-design.md)统一英文基准、22题、每方案一次（共88个正式位置）；四个方案目录各有 `test-design.md`。检查结论及剩余实施缺口见[设计评审](studies/banking-architecture-comparison/design-review.md)。这些文件是设计，不是已实现的执行配置。
