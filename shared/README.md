# 四实验共享基础能力

此处是从原工程提取的当前组件；完整旧工程位于 archive/legacy-workspace 和 archive/deepagent-source，不保留旧命令兼容入口。

| 目录 | 职责 |
| --- | --- |
| python/experiment_plan.py | 四方案准备记录生成；只核验输入，不执行模型 |
| python/diagnostic_run.py、run_episode.py | 独立开发诊断及官方模拟/评分；不进入正式比较 |
| python/episode_acceptance.py | 单题实际装配、Skill、MCP与官方回执核查；业务原分数单列 |
| python/skill_assets.py、skills/releases/ | 不可变Skill发布及完整性校验 |
| python/benchmark_mcp.py | episode内官方工具MCP桥 |
| python/java_agent.py、deepagent_java_agent.py | 官方模拟器与Java桥的适配组件，尚需接入新正式执行器 |
| java/ | DeepAgent桥接和装配的Maven工程 |
| python/trace_viewer.py、trace_inspection.py、viewer/ | 本地轨迹读取与页面 |
| config/ | 非秘密模型网关配置 |
| tests/ | 当前组件回归测试 |

## 构建与验证

```bash
mvn -B -ntp -f shared/java/pom.xml -DskipTests package dependency:build-classpath -Dmdep.outputFile=classpath.txt
python -m unittest discover -s shared/tests -v
python shared/python/validate_layout.py
python shared/python/trace_viewer.py --help
```

使用已安装依赖和JDK21。构建不等于模型业务测试。MCP测试会绑定本地回环端口。

脚本模型协议检查入口为 `shared/python/check_deepagent_protocol.py`；显式指定 --skill-version、--language、--prompt-version 和 --output。它需要先构建Java，使用本地合成模型，不调用外部模型。原始Skill用1.0.0；优化Skill用banking-evidence-guides。

准备校验使用JSON Schema（jsonschema依赖），并校验共同契约和业务操作归属。`python shared/python/study_contracts.py`可独立检查业务覆盖与合成oracle；`study_policy.py`仅提供离线判断函数，不代表已经具备运行时取消或强制授权能力。

## 开发诊断

```bash
python shared/python/diagnostic_run.py --arm 1 --task task_003 --output experiments/plan-1-deepagent-original-skills/runs/new-diagnostic --execute --prompt-key
```

输出目录必须不存在。凭证通过无回显输入或 `OPENAI_API_KEY` 传入；不要写入配置。方案 2 使用 `--arm 2` 及对应目录。方案 3/4 还需 `--runtime-pilot`，分别是七领域 Runtime 的部分 MOA 集成、真实 Go 控制的只读链路；两者完整架构门禁仍未通过。详情见 [TDD 进展](../studies/banking-architecture-comparison/reports/tdd-integration-progress.md)。
