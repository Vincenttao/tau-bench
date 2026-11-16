# openJiuwen Java × τ³ 银行评测实施方案

后续执行顺序见 [逐项测试计划 V0.2](测试执行计划-V0.2.md)：沙箱外执行、单项落盘、仅记录Token、不设置累计Token预算。


指标卡采集统一遵循 [数据采集方法 V0.2](数据采集方法-V0.2.md)。当前 benchmark 成绩与企业指标分开报告；逐卡结果见 [本次81卡采集表](runs/smoke-20261113T154715Z/metrics-v02.md)。


> **执行状态（2026-11-14）**：沙箱外构建及真实银行冒烟已完成；当前1200秒A组已完成P06六次重复预试，正在执行全新P07的97题覆盖。task_001三次通过、task_041三次失败，两题的精确工具轨迹均不同。最新数量见[当前进度](runs/enterprise-v02-timeout1200-20261114/progress.md)及[97题覆盖报告](runs/enterprise-v02-timeout1200-20261114/P07-full-suite-analysis.json)。B组真实Runtime/MOA启动、会话数据和原生OTLP诊断检查已完成，正式银行业务未执行。此前单题冒烟见[历史实测](runs/smoke-20261113T154715Z/smoke-summary.json)，不补入正式重复次数。


## 当前修订结论

银行bench适合作为业务载体。A组NativeSkillAgent stdio基线正在全题实测；B组Runtime/MOA MAIN接入适配器及OTLP接收已准备并通过限定专项，正式银行题、P12对照与P13—P15仍待执行。当前严格轨迹一致要求未在P06样本中满足，尚不能单独归因于模型或框架。源码、构建、启动、诊断Span和真实银行评分分别报告。

源码审查快照：Core `1ffbfb81a`、Runtime `77004f14`、Solution `0298dcd28`。Solution POM 当前管理 Core 0.1.17、Runtime 0.1.4、Solution 0.1.3。NativeSkillAgent 与 StagePlanningRail 均在当前源码中。实际执行以 manifest 的源码提交、工作区状态、加载制品 SHA-256 为准；源码提交不自动证明 JAR 由该提交构建。

## 已刷新内容

1. Python 用户模拟器与 Java Agent 从同一 manifest 取得模型和网关。默认使用指定火山网关 `/v1`，由客户端调用 `/chat/completions`，不使用 Responses 或 Anthropic 协议。
2. 官方工具返回error=true时，Java向Skill返回success=false并保留已观察原文；已通过函数级回调错误传播专项。B组另将原文存入当前Core Skill会话状态，并通过真实NativeSkillAgent本地脚本模型的100KB原文往返检查；不把这些组件检查当成真实银行或持久化恢复验收。
3. 默认所有 trial 使用同一 seed；`--trial-seed-mode varied` 保留原来变化 seed 的实验方式。同 seed 仍不能保证远端模型或用户模拟器完全确定。
4. manifest 增加源码提交及脏状态、全部 Java 源码 hash、加载 JAR/桥 class hash、网关、模型、等待超时及调度参数。变更配置或重建后使用新输出目录。
5. 空题集及不存在的任务 ID 立即报错；进程组终止等待 5 秒后升级为强制结束。

## 本地运行

```bash
source config/volcano.env.sh
read -rsp 'API key: ' OPENAI_API_KEY; echo
export OPENAI_API_KEY
python python/check_gateway.py
export TAU2_REPO=/absolute/path/to/tau2-bench
export JAVA_AGENT_COMMAND="bash $PWD/java/run.sh"
```

凭据只放在当前 shell 环境，不写入文档、脚本、manifest 或 Git。`check_gateway.py` 仅发一个短请求，不打印密钥、完整服务端错误或模型正文。它不检查工具调用、流式输出和官方裁判可用性。

官方题集仍固定 `fc0055dc4e0a316c3f83133267fbd6faaa770992`。构建当前三个 Java 仓库并安装匹配依赖后，在本项目执行：

```bash
mvn -f java/pom.xml -DskipTests package dependency:build-classpath -Dmdep.outputFile=classpath.txt
python -m unittest discover -s tests -v
python python/full_run.py --output runs/plan --trials 5 --trial-seed-mode fixed
python python/full_run.py --output runs/smoke --task-ids task_001 task_002 --trials 1 --concurrency 1 --execute
python python/analyze_v2.py runs/smoke
```

每次实验使用独立目录。正式全量先确认计划 97 题 × 5 次、裁判可用性、冒烟及网关实际用量，再执行。官方指定裁判不随被测模型替换；不支持时保留未评分轨迹。

## 三组实验与验收

| 组别 | 接入 | 验收对象 | 当前状态 |
| --- | --- | --- | --- |
| A | NativeSkillAgent → 官方模拟工具 | 官方成绩、重复成功率、业务工具轨迹 | 代码已修订，待构建与真实冒烟 |
| B | Runtime → MOA 主 Agent → 本地 NativeSkillAgent → 同一官方工具 | 路由、阶段规划、冻结计划、交互、任务状态 | 待实现 |
| C | B + 固定位置故障注入 | 超时、暂停、进程重启、写响应丢失、并发隔离 | 待实现 |

B 组应使用 `MoaRuntimeAutoConfiguration` 装配的 MAIN rails 和原生 Handler；不能认为直接调用 NativeSkillAgent 已覆盖主编排。先使用本地 Skill，不为多 Agent 指标强行拆远端服务。公开业务政策可配置操作确认和约束，禁止使用隐藏评分答案。A/B 应记录提示与业务资产差异，不将全部成绩差异归因于 Runtime。

严格重复实验固定用户输入策略、模型配置、初始数据库及工具环境，比较规范化工具名称、业务参数、顺序和最终状态。框架确定性另用固定模型响应回放。当前分析只比较业务工具轨迹，不覆盖完整 Plan/Todo 状态，也不证明未来每次结果必然一致。

恢复实验须同时保存官方模拟数据库、Core checkpoint、Runtime Task 和全文观察缓存。当前 ObservedToolContext 为进程内列表，换成持久化 checkpoint 不会自动保存它。MOA 暂停默认须显式启用；ACCEPTED 不代表已挂起；未完成远端 Todo 现场恢复不在已支持范围内。幂等键传递不等于业务端去重已实现。

## 本次验证边界

已进行 Python 配置回归、语法及模拟题集计划检查。当前环境未配置 TAU2_REPO，网关与 GitHub 域名解析失败；离线 Maven 构建条件不足。未调用真实模型，未完成 Java 构建或银行 E2E。历史实验数字不作为本次结果。

桥接层现通过 JAVA_AGENT_COMPLETION_TIMEOUT 显式配置 Core completion deadline，默认仍为600秒；值写入 manifest，由 episode 按 manifest 设置。桥事件等待默认300秒，episode默认3600秒，两者不替代 Core 的整轮限制。零网络专项 CoreTimeoutSelfTest 已验证实际 Core 超时帧可被识别；历史未采集的帧不追补。全文注入、arguments_json 包装与操作确认未配置等限制仍在，需要通过后续对照实验处理。

---

## 历史移植指南（保留追溯，非当前执行基线）

以下固定提交、旧实验统计、环境估算和验证状态均为原移植资料。若与上方当前方案冲突，以上方方案及实际 manifest 为准。

# openJiuwen Java × τ³-bench 银行业务本地测试实施建议

版本：2026-11-13；状态：已完成小规模验证，尚未完成 97 题 × 5 次全量评估。

## 1. 测试目标和结论边界

目标不是证明“框架里有某个功能”，而是验证同一复杂业务任务能否完成、重复完成，以及失败是否可定位。

本轮采用官方 `banking_knowledge`，固定 τ³-bench v1.0.1，共 97 题，每题独立运行 5 次，共 485 个 episode。使用官方 BM25 检索、政策、模拟业务工具和评分，不自行改答案或放宽分数。

四个观察方向：

| 方向 | 本轮测什么 | 不能仅凭本轮证明什么 |
|---|---|---|
| 结果质量 | 官方业务状态、指定动作、必要交流是否达标 | 真实银行生产合规、所有企业任务通用性 |
| 执行一致性 | 同题 5 次结果分布、成功轨迹之间的关键差异 | 5 次通过不等于生产级近乎必胜 |
| 执行可靠性 | 模型/工具/适配/执行/评分异常和明确失败原因 | 默认题集不包含系统化故障注入 |
| 执行连续性 | 一次多轮业务办理的状态保持 | 跨进程恢复、跨天接续、审批后自动恢复 |

**重要：目前接入是真实 Java MOA NativeSkillAgent + DeepAgent/Core，不是完整 Runtime 服务路径，也不是完整 MOA 多智能体编排。** Runtime 制品已作为依赖构建，不等于 Runtime 的 HTTP 服务、调度、恢复能力被测试。

## 2. 固定实验版本

| 组件 | 固定提交 |
|---|---|
| τ³-bench v1.0.1 | `fc0055dc4e0a316c3f83133267fbd6faaa770992` |
| agent-core-java | `0db55c68e306d8d35fbbfdc8a9d47fe406e12faa` |
| agent-runtime-java | `8fc83a4136257f41dfd9332742e40bef23544216` |
| agent-solution / MOA | `bf702bc95064d3491cf8b374f54d271363d84230` |

官方仓库：[sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench)。仓库名和 Python 模块仍叫 tau2，不代表本次使用旧 τ² v0.2.0。

官方 loader 实际读取 `data/tau2/domains/banking_knowledge/tasks/task_*.json`。同版本汇总 `tasks.json` 与其中 13 道独立文件不同，**不能以汇总文件替代实际运行数据**。应逐文件记录 SHA-256。

## 3. 推荐本地环境

在 Windows 上推荐 **WSL2 + Ubuntu/Linux 用户空间**。本次 Python supervisor 使用 `os.killpg`、Unix 进程组，Java 启动 classpath 使用冒号；不能直接宣称原脚本支持原生 PowerShell。

准备：
- Python 3.12 或 3.13，官方约束为 `>=3.12,<3.14`。
- JDK 17、Maven 3.9.x、Git。
- Python 虚拟环境及官方 `[knowledge,dev]` 依赖。
- 能访问代码仓、Maven/Python 依赖源及用户批准的模型网关。
- 运行期间保持系统唤醒，预留日志空间。模型远程运行，不要求本地 GPU；内存和磁盘需求应由冒烟实测，不能据现有证据给出保证配置。

不要通过关闭 TLS 校验来解决证书问题。企业代理环境应使用获准证书和代理配置。

## 4. 建议交付和目录结构

```text
$HOME/tau3-local/
├── tau2-bench/                  # 官方固定版本
├── agent-core-java/
├── agent-runtime-java/
├── agent-solution/
├── tau3-local-source/python/    # 源码包中的评测 Python 代码
│   ├── full_run.py
│   ├── episode.py
│   ├── java_agent.py
│   └── analyze_v2.py
├── tau3-local-source/java/      # 源码包中的独立全文桥接源码
│   ├── pom.xml
│   ├── src/main/java/eval/...
│   ├── run.sh
│   └── FULL-CONTEXT-ADAPTER.md
├── results/
└── .venv/
```

可复用现有 supervisor、官方 episode 调度、Java stdio 桥和后处理代码；**随附源码移植包已移除主要云端路径依赖，但必须先按第 6 节核验**。本指南不是“无需适配的一键安装”承诺。

不应复制云端 `.venv`、JDK 二进制、Maven 缓存、`target`、旧 `classpath.txt` 或包含凭据的 shell 历史。应在本地重建。原始业务轨迹另行保护，不和源码混装。

## 5. 安装与构建

以下命令在 WSL/Linux Bash 执行；将源码包解压为 `$ROOT/tau3-local-source`。

```bash
mkdir -p "$HOME/tau3-local"
cd "$HOME/tau3-local"
export ROOT="$PWD"

git clone https://github.com/sierra-research/tau2-bench.git
git -C tau2-bench checkout fc0055dc4e0a316c3f83133267fbd6faaa770992
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e './tau2-bench[knowledge,dev]'
python -m pip freeze > requirements-resolved.txt

export TAU2_REPO="$ROOT/tau2-bench"
export TAU2_DATA_DIR="$TAU2_REPO/data"
export LITELLM_LOCAL_MODEL_COST_MAP=True
```

`pip install` 的依赖解析结果可能随时间变化，因此保留 lock/freeze 文件；若使用仓库 lock 工具，应以该版本说明为准，不混用另一版本依赖。

Java 仓库和构建路径：

```bash
git clone https://gitcode.com/openJiuwen/agent-core-java.git
git clone https://github.com/openJiuwen-ai/agent-runtime-java.git
git clone https://gitcode.com/openJiuwen/agent-solution.git

git -C agent-core-java checkout 0db55c68e306d8d35fbbfdc8a9d47fe406e12faa
git -C agent-runtime-java checkout 8fc83a4136257f41dfd9332742e40bef23544216
git -C agent-solution checkout bf702bc95064d3491cf8b374f54d271363d84230

java -version
mvn -version
mvn -f agent-core-java/pom.xml -DskipTests install
mvn -f agent-runtime-java/pom.xml \
  -pl service/agent-service-app,service/agent-service-adapters/agent-service-adapters-agentcore \
  -am -DskipTests install
mvn -f agent-solution/pom.xml -Pall -pl common/agents/moa-agent -am \
  -Dmaven.test.skip=true -Dspring-boot.repackage.skip=true install
mvn -f tau3-local-source/java/pom.xml -DskipTests package dependency:build-classpath \
  -Dmdep.outputFile=classpath.txt
```

这些是依赖安装/编译步骤，不等于产品测试通过。若企业镜像或仓库权限限制导致依赖不可用，记录具体制品和错误，不替换成其他未验证版本。以本地 Maven reactor 实际输出确认选定模块构建结果。

## 6. 必须检查的代码移植点

### 6.1 消除硬编码路径

随附包已将原云端硬编码路径改为 `TAU2_REPO` 与包内相对路径。Java 桥源码 hash 从包内 `java/src/main/java/eval/Tau2Bridge.java` 计算；无需设置 `JAVA_BRIDGE_SOURCE`。

```bash
export JAVA_AGENT_COMMAND="bash $ROOT/tau3-local-source/java/run.sh"
```

随附 `run.sh` 使用本机 `JAVA_HOME`/Java 与本机 Maven 生成的 classpath。不要复制其他机器的 `classpath.txt`。为避免 `JAVA_AGENT_COMMAND` 的 shlex 分词问题，工作目录建议不用空格。

**随附移植包仅完成 Python 语法检查和静态秘密扫描，尚未在用户本机编译或端到端运行。** 它修改了路径、启动脚本和默认 trial 数，需重新冒烟，不能把原云端结果当成该移植包的验证结果。

### 6.2 保留三层协议

```text
官方 TextRunConfig / run_single_task
  → Python JavaMoaAgent
  → Java stdio bridge
  → MOA NativeSkillAgent / Core DeepAgent
  → 官方工具回调至 Python 环境
  → 官方 SimulationRun 与 evaluator
```

- Java 不执行真实银行交易，业务动作在官方模拟环境执行。
- 只能给被测 Agent 公开政策、工具 schema、用户消息和它已观察的工具结果。
- 不得给模型输入 task 的答案、gold actions、required_documents 或 evaluation_criteria。
- 官方工具参数以 `arguments_json` 包装传给 NativeSkillAgent，最终仍由官方工具校验执行。这改变工具呈现，应在报告披露。
- 初始 assistant 问候以角色标记的上下文转录保留，不是原生历史消息注入。`tool_calls:null` 不应误判为真实工具调用。

### 6.3 全文检索适配必须披露

现有版本原生工具模型摘要硬限约 8192 字符，业务结果约 65536 字符；实际 BM25 `top_k=10` 检索结果有 14k～26k 字符。单纯提高 schema 字符串上限不能解决摘要硬限。

本次独立适配利用公开 `ModelContextContributor`：
1. 桥按 episode 保存已观察工具原文。
2. 原生操作结果只存引用、长度、SHA-256。
3. 后续模型调用注入完整原文，不截断、不减少 top_k、不替换检索结果。

这是**评测桥补充能力**，不是产品已具备原生持久化长结果支持。缓存随进程结束丢失；累计上下文可能很大并触及模型限制。全文内容作为不可信工具数据，不应被当成高优先级指令。

建议保留离线测试：5 条真实 BM25 结果逐字/hash 一致，10 万字符边界测试，重复注入不丢失或覆盖旧结果。原实验已通过这些检查，本地仍需重新验证。

## 7. 模型配置与凭据

使用用户批准的 OpenAI Chat Completions 兼容网关，环境变量方式设置，不把 key 写入文档、代码、manifest 或 Git：

```bash
export OPENAI_API_BASE='https://YOUR-APPROVED-GATEWAY/v1'
export OPENAI_BASE_URL="$OPENAI_API_BASE"
export OPENAI_MODEL='deepseek-v4-flash'
read -r -s -p 'API key: ' OPENAI_API_KEY; echo
export OPENAI_API_KEY
```

运行结束可 `unset OPENAI_API_KEY`。不要将 key 作为命令行参数；异常日志需脱敏。曾在聊天中明文提供过的 key 建议轮换。

初始配置冻结为：Agent/User 均使用指定模型、temperature=0，Java top_p=1；不支持 Java seed，不能声称逐 token 可复现。记录服务实际返回的 model 标识，网关别名不保证底层权重始终一致。

评分方面，97 题中 87 题以 DB 为基础，9 题以 ACTION 为基础，`task_102` 使用 DB + NL_ASSERTION。其官方裁判为 `gpt-4.1-2025-04-14`，之前经指定网关预检返回 404。本地若仍不支持，保留轨迹、单列未评分；不能悄悄用 DeepSeek 替代并混入官方主分。若之后获准替换，只能作为明确标注的非标准对照。

## 8. 运行顺序

### 8.1 离线与计划检查

先不要配置模型 key，做语法、构建和计划检查。计划生成不应发出推理调用。

```bash
python -m py_compile tau3-local-source/python/full_run.py tau3-local-source/python/episode.py tau3-local-source/python/java_agent.py tau3-local-source/python/analyze_v2.py
python tau3-local-source/python/full_run.py --output "$ROOT/results/plan97x5" \
  --domains banking_knowledge --trials 5 --concurrency 3
```

确认输出 `unique_tasks=97`、`episodes=485`。随附移植包默认 trials 已改为 5，但仍建议显式写 `--trials 5`，避免和原实验脚本默认 2 混淆。 核验 manifest 中 commit、97 个题目文件 hash、桥和适配器 hash、模型、检索策略。

### 8.2 两题冒烟

配置 key 后，单并发、小样本执行：

```bash
python tau3-local-source/python/full_run.py --output "$ROOT/results/smoke" \
  --domains banking_knowledge --task-ids task_001 task_002 \
  --trials 1 --concurrency 1 --execute
python tau3-local-source/python/analyze_v2.py "$ROOT/results/smoke"
```

冒烟门槛：协议完整、官方模拟工具真实执行、结果全文未丢失、轨迹保存、官方评分可产出。冒烟业务失败不一定是适配失败，需诊断后决定是否继续。冒烟样本与正式样本分开，不合并为正式成功数。

### 8.3 正式 97 × 5

```bash
python tau3-local-source/python/full_run.py --output "$ROOT/results/banking97x5" \
  --domains banking_knowledge --trials 5 --concurrency 3 \
  --max-steps 200 --max-errors 10 --episode-timeout 3600 \
  --max-hours 72 --execute
```

以上参数名与现有 supervisor 一致。没有显式 token limit 时，原实现采用很大的内部限额，不是零成本运行。建议本机保持前台或使用受控进程管理，不能只看一个陈旧的 active 数字判断仍在运行。

2 条冒烟平均约 105 万 token；线性外推 485 次约 5.09 亿 token、3 并发约 16.6 小时。**只有两题且采用累积全文注入，这只是粗估，不是预算或时长承诺**，价格未知。应先查看模型账户实际计费、上下文上限和限流能力。

原调度顺序是“先跑全部题目的第 1 次，再跑第 2 次……”。所以早期完成 10 道题，不代表任何一题已有 5 次稳定性结果。

## 9. 停止与恢复建议

- 明确 `insufficient_quota`/余额耗尽等网关错误：停止新增任务，终止在途进程，保存证据并更换凭据后人工决定恢复。
- HTTP 429 不必然是余额不足，可能是速率限制；401/403 为认证或权限问题，不应无限重试。
- 连续 6 次执行基础设施异常：暂停新任务并诊断；官方业务 reward=0 不应触发这个熔断。
- 现有 supervisor 会保留完成状态，不自动重跑失败；发现旧 process.log 但无状态时，会标为中断。
- **现代码没有“自动修复后无损续跑中断题”的完整功能。** 不要直接删 status/覆盖结果。重试应新建 attempt 目录，保留父尝试、原因、配置差异及时间。
- 换 key 后不要盲目在原目录再次运行：旧 quota-stop 证据可能再次触发停止。建议新批次只列未启动项；中断/失败项单独作为重试层，主结果保留第一次正式尝试。
- 如果要把多个目录合并为 97×5 主结果，应按 `(task_id, trial)` 去重，只在事先约定规则下替换基础设施中断，不按成功与否择优。

停止后核验 OS 进程、最新日志时间、网关用量三方面，不能仅凭监控命令失败断言后台已退出。

## 10. 超时与错误处理代码改进

目前至少有四层限制，应分别配置和记录：

| 层 | 当前值或行为 |
|---|---|
| Python 用户模拟模型请求 | timeout 120 秒、num_retries=0 |
| Python 等待 Java 桥事件 | 300 秒 |
| Core 整轮 completion deadline | 默认约 600 秒 |
| Supervisor episode 上限 | 3600 秒 |

NativeSkillAgent 每次调用最多 100 迭代，不等于整题能一直执行 3600 秒。实际 task_012 在约 600.002 秒结束，仅到 21/100 迭代，源码与时序高度支持 Core 整轮超时；因为旧桥未保存原始嵌套 timeout 帧，该归因是高置信推断而非直接字段证据。

建议本地改进先建独立版本：
1. 将 Core completion deadline 和桥等待超时显式配置，并写入 manifest。
2. 捕获原始 `round/final_result` 错误结构，区分 timeout、模型错误、工具错误和无内容，不一律报 `No user-visible output`。
3. 超时先关闭进程组，等待退出并检查残留子进程。
4. 不要在 485 次中途调整参数；调整后作为新实验版本，另表比较。
5. 若当前 NativeSkillAgent API 不暴露 deadline，需先检查可用构造/API，再修改适配或产品代码，不能假设存在某个环境变量。

## 11. 结果文件与统计口径

```text
results/banking97x5/
├── manifest.json
├── supervisor.jsonl
├── progress.json
├── episodes/<key>/
│   ├── status.json
│   ├── result.json                 # 已评分
│   ├── trajectory-unscored.json    # 完成对话、评分前保存
│   ├── official-trajectory.jsonl   # 每步观测，异常时也保留
│   ├── exception.txt
│   ├── user-usage.jsonl
│   └── java/                      # Java调用与双向桥轨迹
├── analysis-v2.json
└── task-summary.csv
```

```bash
python tau3-local-source/python/analyze_v2.py "$ROOT/results/banking97x5"
```

至少报告：
- 计划 485、已结束、已评分、未评分、未开始、异常、截断数。
- 成功/已评分是条件成功率；不能静默排除未评分后称为全量成功率。
- 每题 0/5 到 5/5 的分布，以及 5 次全成功题占比。
- `pass^k = C(s,k) / C(n,k)`，含义是抽取 k 次全部成功，不是“至少一次成功”的 pass@k。完整数据按 97 题等权平均；缺失时说明子集分母。
- 结果成功与路径一致分开：稳定失败也可能有高一致性。
- 成功—成功、失败—失败、所有完整已评分轨迹分别比较；异常、截断、空轨迹不计为 100% 一致。
- 双端（Agent 与用户模拟器）工具调用角色、名称、参数和顺序都保留。
- 规范化去除生成的 tool-call ID、无关文本等，保留业务账户/交易 ID、金额和有意义顺序。不要把不同账户操作“归一化成相同”。
- 选定操作序列可能含只读查询，不能称为纯写动作或完整语义等价性。
- 编辑距离相似度只是诊断；额外查询和错误金额的风险并不等价，应人工审查关键分叉。
- token 汇总至少拆 Agent、用户模拟器、裁判；网关实际账单是费用依据。缺失 usage 不等于零消耗。

## 12. 已有早期证据，不作为全量结论

截至最近一次可核验状态：正式 14 次结束，13 次已评分，其中 11 次通过、2 次官方失败；另 1 次执行异常。两条独立冒烟均通过，但不计入正式 14 次。尚无完整每题 5 次结果。

三个值得复测的案例：

| 案例 | 官方/运行结果 | 已有诊断 |
|---|---|---|
| task_010 第 1 次 | reward=0，DB不匹配 | 两个预期业务动作完成；额外授予 get_referral_link 使 user_discoverable_tools 多一条记录。严格离线 replay 只发现此差异。保持官方0，不改判通过 |
| task_014 第 1 次 | reward=0，ACTION不匹配 | DB匹配，但缺少要求的 transfer_to_human_agents 动作，不能笼统归为数据库问题 |
| task_012 第 1 次 | 执行异常，未评分 | 约600秒截断，高置信为Core整轮deadline；不能当成官方业务reward0 |

正式批次未完成的外部执行环境限制，不应统计为 openJiuwen 产品缺陷。迁移本地的目的应是用户在其获准环境中执行测试，不是关闭或绕过安全措施。

## 13. 下一阶段：真正验证 Runtime 与 MOA 协同

建议与官方主成绩分开实施：

### A. Runtime 服务路径

把 stdio 直接调用替换为实际 Runtime 受理请求、会话/任务标识、状态查询与结果返回。保持相同模型、任务和评价器，比较直连与 Runtime 模式结果。需保存请求、任务、执行实例、工具调用关联 ID。

### B. 完整 MOA 协同路径

固定职责：任务规划、政策检索、账户业务、争议业务等。实际通过 MOA 规划/分派路径完成，记录父子任务、消息、等待与汇总。不能仅在 prompt 中写“你是多个角色”就称为多智能体测试。

### C. 故障注入与连续性

另建扩展集：读工具超时、写成功但响应丢失、进程重启、用户审批等待、Agent 交接失败。验证：无重复扣款/重复写、正确恢复点、重新授权边界、最终状态一致。每种注入固定发生点和随机种子，保留正常对照。

优先选择 `task_062`（依赖顺序）、`task_080`（多卡丢失及改意图）、`task_041`（多交易与全局额度约束）等复杂题，但扩展结果不能冒充未修改的官方成绩。

## 14. 启动前验收清单

- [ ] 固定4个仓库提交、依赖版本和本地源码hash。
- [ ] 独立题目文件97个、正式episodes485个。
- [ ] 无答案/评分条件泄漏给被测Agent。
- [ ] API key只在本地环境变量，日志脱敏。
- [ ] 所有模型角色只走已批准网关，无默认外部服务回退。
- [ ] BM25全文适配与超时行为有离线测试。
- [ ] 正式配置与冒烟配置差异明确。
- [ ] 明确裁判不可用时的未评分处理。
- [ ] 额度不足停止，基础设施异常熔断，不无限重试。
- [ ] 初次尝试与重试分开，结果不择优覆盖。
- [ ] Runtime/多Agent未覆盖部分在最终结论中显式列出。

## 官方参考

- [固定版本源码](https://github.com/sierra-research/tau2-bench/tree/v1.0.1)
- [官方银行环境 loader](https://github.com/sierra-research/tau2-bench/blob/v1.0.1/src/tau2/domains/banking_knowledge/environment.py)
- [独立任务文件目录](https://github.com/sierra-research/tau2-bench/tree/v1.0.1/data/tau2/domains/banking_knowledge/tasks)
- [τ-Knowledge 论文](https://arxiv.org/abs/2603.04370)

本指南依据固定版本源码和已有实验记录编写。未在用户本地机器执行，因此本地构建、网络、依赖和全量结果仍需现场验证。
