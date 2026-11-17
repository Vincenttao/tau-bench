# 四方案 TDD 开发进展

日期：2026-11-17。状态：开发中，四方案完整架构验收尚未通过。

范围更新：用户要求方案3不超出现有MOA能力。下文记录的是原开发阶段事实；其中远端A→B→A、动态依赖/检查点扩展不再是当前方案3门禁。当前待验收的是原生阶段、问答续接、切换、权限及业务适配，见方案3/test-design.md。旧真实业务分数与运行证据不变。

最新实施：方案3已修订MAIN银行提示与领域描述，补回英文确认中的前置条件，通过现有Rail采集MAIN输入输出。两个真实Runtime的阶段确认、领域补参和结果返回已用本机脚本模型验证，八Runtime启动复验通过。详见[实现检查记录](../../../experiments/plan-3-moa-refined-skills/reports/implementation-check-20261117.md)；没有新增真实模型业务成绩，完整原生门禁仍待完成。

## 验收口径

用户已确认：以执行链和架构验收判断开发完成，保留真实业务分数。reward=0 不自动表示执行器故障；reward=1 也不能替代 MOA 恢复或 Hub 控制验收。当前全部真实运行都是开发诊断，不计入正式 22×4 单轮比较，不覆盖旧批次。

## 已落实的开发链

1. 公共开发执行器先做失败测试，再实现独立目录、方案绑定、凭证仅经进程环境传递、源码/字节码冻结、deadline 和结果分类。新增执行前输入漂移检查及依赖 hash。早期诊断尚无完整源码快照/依赖 hash，不能追溯声称具备后加的能力。
2. Java 客户端原先默认重试两次；通过配置回归改为显式零重试、120 秒请求超时。方案 1 首次诊断发生在修复前，随后另建批次复验。
3. 实际 DeepAgent 装配、Skill 文件、语言/提示词、MCP 调用参数及官方回执有独立核查。该核查范围是单题接线，不能自动放行整个 study。
4. MOA 实验通过私有 classpath 补丁修正普通、显式 intent 和 TARGET 的快路径，禁用快识别/任务数分析；不修改邻接 agent-solution 仓库。八个实际 Runtime 的独立进程、端口及 Agent Card 已验证。
5. MOA 真实诊断暴露中文确认模板问题；修复后通过英文 Yes/No、拒绝及不泄露内部编号的回归。第二批已真实进入领域 Agent、MCP 和官方评分。
6. Hub 使用实际 Go adopt/ledger 包与独立进程，验证参数绑定、当前授权、重复派发、未知效果恢复、进程失联拒绝，以及最终官方工具队列前的控制。只读 pilot 的允许目录由 Go 再次核验，不依赖 Python 单侧检查。

## 真实运行证据

运行索引及独立核查见 [tdd-run-index.json](tdd-run-index.json)。原始轨迹保留在各实验 `runs/`，按仓库规则不提交 Git。

| 方案/批次 | 实际范围 | 业务结果 | 架构判断 |
| --- | --- | --- | --- |
| 1 / product-consultation-attempt-01 | 原始 Skill，首次接线 | reward=0 | 有客户端默认重试偏差，仅诊断 |
| 1 / zero-retry-product-consultation | 修复客户端后实际官方全链 | reward=0 | 单题接线核查通过；不是全 study 放行 |
| 2 / product-consultation-attempt-01 | 优化 Skill，实际官方全链 | reward=1 | 后验单题接线核查通过 |
| 3 / seven-runtime-product-pilot | 八 Runtime，中文确认阻塞业务 | reward=0 | 未通过；保留失败 |
| 3 / english-confirmation-product-pilot | MOA→领域 Runtime→MCP→评分 | reward=0 | 完整跨任务恢复验收仍待完成 |
| 4 / actual-go-read-product-pilot | DeepAgent→真实 Go 只读许可→MCP | reward=0 | 写入判断未实现，不能计为完整方案 4 |

## 尚未完成的门禁

- MOA：A→B→A 的真实远端检查点恢复、多层依赖、重启/取消、重复与迟到回调、业务完成证据核对。当前普通 A2A 对话恢复不等于跨任务恢复。
- Hub：银行写入的证据工作流、judgment/evidlog/replay 全链接线、业务依赖、持久化业务幂等与故障恢复。当前只读 pilot 拒绝写入，不能通过全部阻塞契约。
- 公共：正式 88 位置控制器、跨层累计调用预算、完整暂停/未知效果处理、全量能力证据索引与正式配对放行。开发执行器不是正式控制器。

不得把已通过的启动检查、单题接线或合成 Go 控制测试替代这些门禁。`plan.json`、`study.json` 的正式执行开关保持关闭。

## 复核命令

```bash
python -m unittest discover -s shared/tests -v
bash experiments/plan-3-moa-refined-skills/java/check-routing.sh
python -m unittest discover -s experiments/plan-3-moa-refined-skills/tests -v
bash experiments/plan-4-agent-hub-refined-skills/go/check-gate.sh
python -m unittest discover -s experiments/plan-4-agent-hub-refined-skills/tests -v
```

MOA 补丁先校验上游源码 hash；Go 构建依赖邻接 `agent-hub-alpha/agent-festival/go`，工具链默认位于忽略目录 `.deps/toolchains/go/`。构建前还会核验实际 Go/schema 源码指纹。模型诊断使用 `shared/python/diagnostic_run.py`，`--execute --prompt-key` 从无回显终端读取凭证。方案 3/4 仅提供明确标记为部分实现的 `--runtime-pilot`，不会返回完整架构验收通过。

## 本轮额外检查

共享 Python 回归 50 项通过，Hub Python 回归 3 项、Go 控制测试 2 项通过；Java 客户端配置/错误传播以及 MOA 慢路由/英文确认检查通过。MOA Runtime/权限/协议测试为 5 项，包含八进程启动检查。目录检查通过；默认 Runtime 日志目录已迁入实验 runs，后续进程工作目录隔离。6 个模型诊断均已评分；其中 2 个为修复前保留记录。诊断输出 808 个文件的凭证扫描未发现提供的 API key。上述检查不表示所有架构门禁通过。
