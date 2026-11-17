# 银行业务 Agent 四实验

本仓库按四个独立实验组织。旧代码、旧入口和历史材料完整归档，不再保持旧命令兼容。**当前进入 TDD 开发：方案 1/2 已完成真实单题接线诊断，MOA/Hub 提供部分集成 pilot；完整四方案架构验收和正式调度尚未完成。** 见 [TDD 进展与证据](studies/banking-architecture-comparison/reports/tdd-integration-progress.md)。

| 实验 | 设计与入口 | Skill |
| --- | --- | --- |
| 1：DeepAgent原始Skill | [方案1](experiments/plan-1-deepagent-original-skills/README.md) | 原始1.0.0 |
| 2：DeepAgent优化Skill | [方案2](experiments/plan-2-deepagent-refined-skills/README.md) | banking-evidence-guides |
| 3：完整MOA | [方案3](experiments/plan-3-moa-refined-skills/README.md) | 同一优化Skill |
| 4：Agent Hub | [方案4](experiments/plan-4-agent-hub-refined-skills/README.md) | 同一优化Skill |

## 主目录

- `experiments/`：只保留四个实验；各自有README、plan.json、test-design.md、prepare.py、plans和reports。
- `studies/`：共同基准、22题清单和对比规则；英文22题×4方案×1次，共88个正式位置，尚未执行。
- [shared/](shared/README.md)：公共输入准备、Skill、Java/MCP组件、工作台和测试；方案1/2复用同一代码。
- `docs/`：目录设计和迁移记录。
- [archive/](archive/README.md)：未压缩旧工程、历史设计、报告和本地轨迹。

隐藏目录 `.deps/`、`.venv*` 是本地基准和环境；`.git/`及工具管理目录保留。历史AGENTS.md按用户原要求保持字节不变，其中旧目录和命令已失效；当前入口以本README和shared/README.md为准。

## 当前可用命令

```bash
# 只生成方案1的输入准备记录，不调用模型
python experiments/plan-1-deepagent-original-skills/prepare.py --output experiments/plan-1-deepagent-original-skills/runs/input-check

# 当前组件回归
python -m unittest discover -s shared/tests -v

# 工作台启动参数
python shared/python/trace_viewer.py --help
```

其他实验使用各自目录下prepare.py，不通过默认Skill选择推断方案。生成的preparation.json明确executable=false；不会冒充可执行manifest或新成绩。

## 数据与边界

原始轨迹、日志、凭证、缓存及构建产物不提交Git。历史冻结文件和评分原样保留，但旧绝对路径、暂停进程恢复和旧命令不再保证可用。历史代码用于查阅，不是新实验的执行入口。工作台可从archive读取已有manifest；MOA/Hub新事件展示仍待接入。

详细规则见[共同测试设计](studies/banking-architecture-comparison/test-design.md)。最新整理记录见[主目录迁移](docs/root-layout-migration.json)。

## 设计复审整改

[R1–R8整改记录](docs/reviews/four-experiment-remediation.md)明确配置联合校验、业务职责、停止/预算边界和指标；[执行契约](studies/banking-architecture-comparison/execution-contract.md)为共同规范。离线规则与准备检查已验证，真实运行接线及故障注入仍待完成。

## 从观察者视角了解准备进展

先读[四实验准备度横向报告](studies/banking-architecture-comparison/readiness-report.md)，再进入各方案的readiness-report.md。四方案已固定输入和检查规则，但尚未完成新正式运行链；公共测试通过不代表四组业务验收通过。

## 从设计到实施

[四实验实施设计](studies/banking-architecture-comparison/design/README.md)定义公共执行框架、方案能力边界、W1–W7交付步骤与五段失败定位。每个实验目录另有implementation-plan.md；这些是待实施任务，不是新运行入口。
