# Hub/Jev使用v10冻结Skill测试054

## 配置与范围

用户要求沿用当前方式，复用v10冻结Skill执行054一次。实际运行器为`hub-evidence-control`，包括当前持久任务、S2/Jev判断、Java DeepAgent、Go Hub和官方工具环境。历史MOA运行器及MAIN提示词未导入。

| 项目 | 本次设置 |
|---|---|
| 用例与次数 | `task_054`，trial=0，seed=300，仅一次，不自动重跑 |
| Skill来源 | `plan-3-moa-refined-skills/runs/moa-v10-remediation-sample-20261118-01/task_054/manifest.json` |
| 实际Skill发布 | `moa-evidence-guides-v2`，9个文件全部匹配原冻结身份 |
| release.json SHA-256 | `e3a92fd8d9151b28e9ba9f6b86066a9a0473fa628f300d0639ea851c0e2943a8` |
| S2及官方用户/评分模型 | DeepSeek官方接口，`deepseek-flash`；合成预检实际响应名也为`deepseek-flash` |
| S1 | `jev-latest`，预检实际模型`jev-1.14.0`；判断阈值仍为.3/.7 |
| 系统提示词 | 当前Hub的`evidence-todo-v1`及当前接线，未套用MOA MAIN v10 |
| 官方工具与评分器 | 原实现；正式四方案比较开关保持关闭 |
| 运行证据 | `logs/hub-frozen-v10-skill-task054-20261118-01/` |

模型端点与请求名同时符合历史v10清单和[DeepSeek官方接入说明](https://api-docs.deepseek.com/quick_start)。这里冻结的是客户端配置、代码与Skill文件；实际响应名记录在各层模型用量/身份文件中，不声称冻结了远端权重。

## 执行前验证

新增允许显式选择端点和历史Skill来源的诊断参数，默认配置保持原状。回归共121项通过，包括冻结Skill身份不一致时拒绝、未允许端点拒绝、Skill原文随本次清单复制，以及来源MOA配置不会进入Hub运行器。凭证预检各调用一次合成DeepSeek/Jev请求，均通过，未调用银行工具。

原始Skill未修改。本次生成的`operations.json`仍依据当前Hub接线所公开的官方工具契约，不能由Skill文字增加权限。凭证仅存在私有运行环境，没有写入清单或报告。

## 结果口径

最终结果分别核对官方DB评分、单题执行链检查、逐轮轨迹和离线控制链重放。MOA v10此前通过054不能替代本次Hub验收。与旧Hub诊断相比，模型入口、Skill和当前修复代码均有变化，单次结果不能单独归因于Skill或Jev。

本报告最终结果见下方验收段及配套JSON；未将运行中状态当成通过。

## 最终验收

**官方业务失败：reward=0，DB状态不匹配，用户停止对话；官方记录耗时608.67秒，共64条公开消息。** 单题执行链10项检查通过，但全部39项契约及正式四方案比较均未宣告通过。

| 验证对象 | 实测结果 |
|---|---|
| 官方工具执行 | 24次：18次查询、6次工具解锁；没有银行业务写入 |
| 三个业务目标 | 争议处理、补卡、提额均为`undetermined` |
| 控制拒绝 | 方案证据/覆盖不足9次；条件证据缺失或虚构2次；发现工具包装不合法2次；步骤已派发、未知或过期2次 |
| 输出检查 | 发生`independent-output-validation-failed`，最终仍请求澄清 |
| 冻结Skill | 9个文件及实现代码均无漂移；实际发布证据包含入口与争议、提额、账户变更指南，内容哈希匹配冻结文件 |
| 请求隔离抽查 | 检查全部108个保存的`.request.json`：无`task_054`字符串，无已知“控制审查冒充用户回答”前缀组合 |
| 离线控制链重放 | 通过：147个事件、159次提供方磁带调用、24次工具派发被抑制；外部推理和官方银行调用均为0 |

失败直接表现为查询和解锁完成，但没有形成可派发的业务操作。证据覆盖拒绝与输出检查失败反复出现，最终用户要求继续全部事项并转人工。现有证据支持“执行器提出的计划/证据未满足当前控制契约，流程未推进到写入”；不能仅凭拒绝文本认定Jev误判，也不能认定每一次拒绝都正确。判断根因还需要逐条对照原提案、证据引用及业务政策。

复用历史Skill没有复现MOA v10的成功结果。历史v10表示MOA主提示词版本，其Skill实际发布名是`moa-evidence-guides-v2`。本次保留Hub主提示词、节点和门禁，所以不能把两个结果作为只改变Skill的对照实验。下一组TDD应从首个证据覆盖拒绝开始，验证计划生成与控制器要求的字段、范围和引用是否一致，再检查输出拒绝后的恢复动作。

## 可核查证据

- [官方摘要](../../../logs/hub-frozen-v10-skill-task054-20261118-01/summary.json)、[官方完整轨迹及评分](../../../logs/hub-frozen-v10-skill-task054-20261118-01/episodes/task_054/result.json)
- [执行链检查](../../../logs/hub-frozen-v10-skill-task054-20261118-01/architecture-acceptance.json)、[冻结清单](../../../logs/hub-frozen-v10-skill-task054-20261118-01/manifest.json)
- [离线重放结果](../../../logs/hub-frozen-v10-skill-task054-replay-20261118-01/result.json)、[本报告结构化摘要](hub-frozen-guides-task054-20261118.json)

原始日志保留在本机忽略目录，未自动提交远端。以上完整轨迹链接用于本机核查。
