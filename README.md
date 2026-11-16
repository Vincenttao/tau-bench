# τ³ 银行业务 Java 框架评测

本项目使用官方 τ³ 银行 benchmark 评测 openJiuwen Java。所有实际测试在沙箱外执行；仅记录模型Token消耗，不设置累计Token预算。官方benchmark评分与企业完整验收分别报告，缺少证据的正式指标保留null。

当前使用指定火山网关的Chat Completions协议和 `deepseek-v4-flash`。凭证只通过交互输入或进程环境提供，不写入源码和配置文件。

## 当前状态

A组 `NativeSkillAgent → stdio → 官方工具环境` 已完成当前1200秒Core配置的P06六次预试，P07全新97题覆盖正在逐题执行。task_001三次均官方通过，task_041三次均官方失败；两题各自的三条精确业务工具序列均不同。这组样本没有满足“每次轨迹相同”的严格要求，模型与框架责任仍待固定响应回放区分。

B组 `Runtime A2A HTTP → MOA MAIN → 本地Skill → 官方工具回调` 的接入代码、真实启动、SDK协议、Core会话原文隔离和原生OTLP导出检查已完成。真实银行业务尚未执行，须P10放行；启动及诊断Span不计入银行成绩。

P09、P10和P11的独立执行入口已准备。P13—P15已有场景与前置条件清单，故障、安全、共享宿主并发和长稳尚未正式执行。原600秒批次的部分结果单独保留，不与新配置合并。

| 内容 | 权威记录 |
|---|---|
| 逐项顺序与门槛 | [测试执行计划V0.2](测试执行计划-V0.2.md) |
| 81卡采集、未知值与证据边界 | [数据采集方法V0.2](数据采集方法-V0.2.md) |
| 当前执行进度 | [当前批次进度](runs/enterprise-v02-timeout1200-20261114/progress.md) |
| P07全97题分母、在途、未开始和评分 | [P07覆盖报告](runs/enterprise-v02-timeout1200-20261114/P07-full-suite-analysis.json) |
| P06重复性及条件可比性 | [重复预试分析](runs/enterprise-v02-timeout1200-20261114/P06-repetition-analysis.json) |
| 实际源码、制品、题集与模型配置 | [冻结manifest](runs/enterprise-v02-timeout1200-20261114/freeze-plan/manifest.json) |
| B组范围及验证限制 | [企业接入说明](enterprise-java/README.md) |
| 旧批次及独立复验 | [原批次进度](runs/enterprise-v02-20261114/progress.md) |

进度报告是生成时的快照；没有终态文件的尝试需要结合实际进程核查，不能仅凭目录存在重启。官方reward不是Q08完整安全验收。NL裁判只允许官方指定模型走同一授权网关，路由不支持时保留未评分，不替换裁判。

## 执行入口

| 入口 | 用途与默认行为 |
|---|---|
| `python/run_baseline_pipeline.py` | 按门槛衔接P06→P07→P08，单并发、逐项独立目录、追加台账 |
| `python/full_run.py` | A组监督器；默认只生成计划，`--execute`才调用模型 |
| `python/episode.py`、`python/java_agent.py` | 官方模拟/评分及A组真实Java回调适配器 |
| `python/run_variation_stage.py` | P09两题×三个seed；默认计划，执行需P08完整复核 |
| `python/run_fixed_response_stage.py` | P10沿用两道预选题，每题捕获一次、回放两次；执行需P09复核 |
| `python/enterprise_run.py` | B组单题监督器；默认计划，真实银行执行需P10复核 |
| `python/collect_metrics_v02.py`、`python/collect_enterprise_metrics.py` | 分别采集A/B组81卡与限定范围的观测事实 |
| `python/report_full_suite.py`、`python/report_repetitions.py` | 离线刷新覆盖及重复性报告，不调用模型 |
| `config/special-study-v1.json` | P13—P15场景、断言、缺口及预先声明的负载参数 |

查看当前P07快照：

```bash
.venv312/bin/python python/report_full_suite.py --suite runs/enterprise-v02-timeout1200-20261114
```

确认旧执行进程已终结后，才使用恢复入口；已有未解决的在途/错误目录会拒绝继续，不自动覆盖或重跑：

```bash
.venv312/bin/python python/run_baseline_pipeline.py \
  --suite runs/enterprise-v02-timeout1200-20261114 \
  --prerequisite-suite runs/enterprise-v02-20261114
```

执行器会隐藏输入API key。B组、回放及专项采用不同目录，历史冒烟和失败后的独立复验不补入正式重复次数。

## 环境与构建

本轮实际使用Linux/WSL、Python3.12和Temurin JDK21.0.12。部分POM声明Java17目标；本轮没有单独验证JDK17端到端运行。脚本使用Bash、POSIX进程与Linux进程身份读取。

官方题集固定commit为 `fc0055dc4e0a316c3f83133267fbd6faaa770992`，97题，BM25检索。Core/Runtime/Solution实际提交与加载JAR/class hash以各尝试manifest为准，构建通过不等于银行业务或企业能力验收通过。

依赖已安装到本地Maven仓库后，构建A组桥：

```bash
mvn -B -ntp -f java/pom.xml -DskipTests package dependency:build-classpath -Dmdep.outputFile=classpath.txt
```

B组及隔离OTLP解析环境的构建、启动和协议检查见 [企业接入说明](enterprise-java/README.md)。OTLP依赖与正式A组虚拟环境分离；版本固定在 `config/otel-collector-requirements.txt`。网关地址等非秘密配置见 `config/volcano.env.sh`。

模型等待、Core整轮、桥事件等待和episode监督时限分别记录。未指定 `--token-limit` 时Token停止条件关闭；真实额度、限流、上下文或超时错误仍须保留并分类。原始轨迹及模型输出属于证据，不因报告刷新而修改。

## DeepAgent＋Todo＋Skill/MCP 新装配

实现入口、沙箱外验证方法和证据边界见 [搭建与验证 V0.3.1](DeepAgent搭建与验证-V0.3.1.md)。使用 `python/run_deepagent.py`，旧NativeSkill入口保留。当前为开发验证，不代表97题正式测试已经通过。

## DeepAgent 第一轮分类抽样结果

2026-11-15，按11类各2题完成22次单轮尝试：21题已评分，12通过、9失败，062为用户模拟器空消息异常未评分。总墙钟约1小时14分钟，已观测Token 20,390,417。

[正式第一轮报告](experiments/deepagent-todo-skill-mcp/reports/round-01-20261115-a00/本轮执行报告.md)与[逐项归因](experiments/deepagent-todo-skill-mcp/reports/round-01-20261115-a00/人工核查与建议.md)为当前结果入口；上文enterprise历史批次与live开发验证分别保留，不混入本轮分母。

## 本地轨迹工作台

运行 `python python/trace_viewer.py --port 8877`，打开 <http://127.0.0.1:8877>，即可按批次、用例查看用户与 Agent 对话、Skill 加载/执行、Todo、MCP 和业务工具记录。新增“本轮能力与判定”面板，可查看部署 Skill 文档、可调用工具的说明与参数，以及本轮和单题的成功/失败标准、预期动作及实际评分。页面只读，不调用模型。数据来源、筛选范围及证据边界见 [使用说明](viewer/README.md)。
