# 企业主链路评测接入

本目录承载B组接入准备。它通过真实的 Runtime A2A HTTP 入口调用 MOA MAIN，再由 MAIN 委托本地银行 Skill。官方银行工具仍由 Python 官方环境执行，Java 只通过原有 stdio 帧请求工具和接收结果。

当前已验证：沙箱外编译；实际 Runtime/MOA 启动；本地 Agent Card HTTP 200；MAIN 实例经公开 `AgentInstanceCustomizer` 配置；官方 SDK 的完成结果及等待用户问题解析；stdout 协议与 stderr 日志分离。启动专项没有调用真实模型。

尚未验证：真实银行题评分、跨用户轮次的 Task 续接、Plan/Todo 与委派关联、重启恢复、安全、并发和长稳。因此 P11 尚未完成。

## 装配方式

- 复用 MOA 的自动配置创建 MAIN `JiuwenCoreAgentExtHandler`，不以直接调用 NativeSkillAgent 替换 MAIN。
- 通过业务 Bean 提供 `CandidatePack`、`LocalSkillDelegate` 和 `SkillScriptRunner`。本地委托器内部使用框架的 NativeSkillAgent。其全部银行操作来自官方初始化工具表，不读取题目答案或验收条件。
- 启用Runtime request-context。Skill整轮1200秒，与当前A组一致；MAIN整轮1500秒，为本地委派和返回处理保留余量；episode监督仍为1800秒。主/子时限分开写入manifest，MAIN不得短于Skill。模型temperature=0、top_p=1。路由、规划提示、会话数据范围、MAIN时限和观测开销都是A/B差异，不能把所有结果差异归因于Runtime。
- 冻结模型配置以高优先级的内存属性源注入，避免依赖JAR的默认 application.yml 空值覆盖配置。凭证不写文件。
- `runtime-events.jsonl` 保存实际 MAIN/Skill 创建事件和 A2A 返回快照。启动时没有 Task，不能据此计算R01/R02或宣称已有持久化恢复。
- B组的工具原文保存到当前Core Skill会话的状态中，快照含会话归属，不使用进程级业务数据缓存。注入模型时使用框架消息metadata标记去重，不按用户文字前缀删消息。已通过两个真实Core会话隔离、100KB全文、错误会话快照拒绝，以及真实NativeSkillAgent三轮工具到模型输入的本地专项。显式复制序列化状态不等于跨JVM持久化恢复。
- `TASK_STATE_FAILED`、其他未支持状态或空答案均作为错误返回；不编造用户可见答案。官方SDK负责选择终态业务结果，避免把展示事件当答案。

## 零模型专项

按执行计划在沙箱外运行：

```bash
bash enterprise-java/build.sh
java -cp "enterprise-java/target/classes:java/target/classes:$(cat java/classpath.txt)" eval.EnterpriseProtocolSelfTest
.venv312/bin/python python/probe_enterprise_bootstrap.py \
  --output runs/<新的专项目录> \
  --trace-source <已有episode的java初始化jsonl路径>
```

启动探针强制模型地址为 `http://127.0.0.1:9/v1`，仅验证启动、入口和stdout协议；不输入银行用户问题。每次使用独立目录。正式银行运行和采集器对接完成前，不把该探针计入银行成绩。

最新完整启动证据见 `runs/enterprise-v02-20261114/P11-native-otel-probe-a01/bootstrap/`；其中 `evidence-manifest.json` 记录启动前制品/源码指纹，`status.json` 核验启动后未改变。会话组件专项见同一批次的 `P11-session-context-selftest.log` 和 `P11-session-roundtrip-selftest.log`。这些专项没有调用真实模型，也没有完成P11正式银行题。

## 原生OTel采集

B组正式执行入口会启动独立回环OTLP HTTP/protobuf接收器，通过企业Runtime原生OTel自动配置导出，并向LocalSkillDelegate传入框架的SkillObservation端口。模型提示和完成内容配置为哈希脱敏，Span字符串属性上限4096；这是观测字段处理，不截断送入模型的工具原文。

解析依赖安装到独立环境，避免改变A组Python依赖：

```bash
python3 -m venv /tmp/tau3-otel-collector-venv
/tmp/tau3-otel-collector-venv/bin/python -m pip install -r config/otel-collector-requirements.txt
```

可通过 `TAU3_OTEL_PYTHON` 指定其他已准备的隔离解释器。原始OTLP、解析Span、接收计数和解析器版本保存到episode的 `java/otel/`。真实SDK导出诊断Span的验证见 `runs/enterprise-v02-20261114/P11-native-otel-probe-a01/`；该Span为手工命名的启动通道探针，不代表银行业务Trace。隔离协议测试日志为 `native-otel-isolated-regression.log`。

桥接器登记真实JVM PID、启动身份和boot ID；监督器在停止接收器前等待该JVM退出。正常关闭验证见 `P11-process-identity-probe-a00/status.json`。接收器会拒绝包含本轮完整模型凭证字节串的OTLP负载，已用假凭证夹具验证；这不替代完整脱敏或企业权限验收。Span接收数量、去重数量和可见丢弃计数均不等于完整业务覆盖率。

## 官方银行业务入口（待P10放行）

`python/enterprise_run.py` 默认只生成一题的独立B组计划。它复用正式题集发现规则，执行时使用 `enterprise_episode.py` 中的官方用户模拟器和官方评分器；该文件从冻结的A组episode适配器派生，仅切换Java传输子类并将缺失usage保存为null。原A组执行适配器保持不变。

```bash
.venv312/bin/python python/enterprise_run.py --output runs/<新的B组计划目录> --task-id task_001
# 正式执行需P10-stage-review.json为COMPLETED；先完成固定模型响应回放，不能用启动探针替代。
.venv312/bin/python python/enterprise_run.py --output runs/<新的B组执行目录> --task-id task_001 --execute
```

使用 `collect_enterprise_metrics.py` 单列B组采集结果。真实A2A响应中的Task ID及最后观测状态可记录，不能自动变成R01/R02分母、业务任务ID或父子Task关系。官方reward与企业完整验收仍分别报告。银行业务入口目前只生成计划并验证了P10未完成时拒绝启动，尚未调用真实模型执行业务题。

## 共享宿主与恢复的剩余条件

当前stdio回调协议仍是一个episode独占宿主。会话缓存修正只验证了Core组件的数据归属，不代表已经支持共享Runtime中的并发官方工具路由。P15必须先实现按会话、Task及call ID关联的多路回调，并使用独立官方银行环境；多个独立JVM不能替代同一宿主的隔离验证。

F03还需准备Core/Runtime持久化后端及官方银行资源快照。源码已有Redis及MOA openGauss存储扩展，不能把当前依赖未配置解释成框架不支持。当前Docker命令在WSL中不可用，提示需检查WSL集成；没有核查Desktop设置，也未发现运行中的Redis/openGauss/PostgreSQL服务。只读核查与专项缺口见 `config/special-study-v1.json` 和批次中的 `special-stage-readiness.json`。
