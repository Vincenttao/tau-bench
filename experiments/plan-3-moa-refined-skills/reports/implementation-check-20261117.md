# MOA银行适配检查与修订

日期：2026-11-17。本次已修改实验实现并运行检查。调整使用现有prompt、能力目录、确认模板和Rail扩展点；未增加MOA调度器、远端恢复协议或业务任务账本。正式执行与比较开关仍关闭。

## 已修订内容

| 位置 | 发现与修订 | 验证边界 |
| --- | --- | --- |
| BankingPrompts.java、BankingRuntimeHost.java | MAIN原先只要求最终英文回复。新增版本moa-banking-v2，要求新生成的子任务、问答和汇总使用英文，保持原生确认机制；对照硬条件与排序偏好、正确处理阈值等于、补充询问和申请状态 | 实际模型请求已包含新prompt；脚本模型不能证明真实模型必然遵守 |
| moa_pilot_agent.py | 能力描述明确产品公开额度范围由产品咨询领域处理，已有卡额度调整由提额领域处理，避免按“额度”关键词拆开一次产品比较 | 目录和prompt静态核查；真实模型路由质量待诊断 |
| planning-language.patch | 旧英文确认补丁删掉了前置依赖和when条件说明。补回前序任务名称、条件、条件不成立时跳过及不确定时停止的说明，保持原生执行语义 | 对真实StagePlanningRail验证条件展示、Yes/No、带改参的Yes不能授权 |
| MainModelEvidenceRail.java | 通过现有MoaAgentRailProvider补MAIN输入输出采集，记录session、call ID、消息和工具；不采集请求headers，采集异常只标记日志缺失 | 与本机模型HTTP请求逐次核对消息角色、正文、工具调用和schema；输入输出关联完整，观察器不修改输入或请求重试 |

所有可写候选仍为HIGH。共用Skill发布未改动：现有指南已经要求按硬条件过滤，再按客户偏好排序，并区分公开范围、已提交和已批准；没有证据支持删除或重写这些规则。先补MAIN对领域事实的使用要求。

## 实际检查

使用JDK21和本地已安装依赖。构建、单测、真实Runtime接线与真实模型业务结果分别记录。

| 检查 | 结果及证据 |
| --- | --- |
| shared/java Maven离线构建；MOA私有补丁编译 | 通过；上游源码hash仍匹配既有补丁基线 |
| Java组件检查 | slow-only普通/显式/TARGET；英文确认和条件保留；MAIN观测不改变控制流，均通过 |
| Python权限与协议检查 | 4项通过；包装器不能绕过领域权限，错误/空终态不能伪装正常答复 |
| 公共配置契约与Skill发布检查 | 9项配置契约、7项Skill资产测试通过 |
| MAIN与七领域Runtime启动检查 | 见[本次验证记录](implementation-validation-20261117.json)及其中运行日志 |
| 两个真实Runtime的原生阶段与补参 | [最终夹具结果](../runs/native-scope-check-20261117-04/result.json)通过；MAIN脚本模型5次、领域脚本模型2次；外部模型调用0 |

真实接线夹具依次验证：stage_plan → stage_bind_next → stage_finalize英文确认 → stage_execute_next → 领域INPUT_REQUIRED → 客户关联回答 → 领域结果到达MAIN → 汇总。MAIN与领域均为实际Java Runtime，模型和业务事实是合成脚本；未执行官方银行写入或评分。

复现入口（输出目录必须不存在）：

```bash
bash experiments/plan-3-moa-refined-skills/java/check-routing.sh
python experiments/plan-3-moa-refined-skills/python/check_native_flow.py --output experiments/plan-3-moa-refined-skills/runs/new-native-flow
python -m unittest discover -s experiments/plan-3-moa-refined-skills/tests -v
```

本地Runtime和脚本服务器需要允许绑定回环端口。首次沙箱运行无法创建socket，保留为native-scope-check-20261117-01；获准运行后才验证接线。

## 检查中发现的判定问题

1. native-scope-check-20261117-02通过正文核对。随后-03扩展全消息核对时失败：Core日志包含工具回包的内部name，实际BaseModelClient发送时只保留tool_call_id。依据SDK源码修正表示格式转换后，-04通过。未忽略正文、角色、工具调用参数或工具schema的差异，旧失败记录保留。
2. 八Runtime检查第一次已通过八个独立PID/端点和Agent Card断言，最后将工具环境的.agents/.codex/.aws挂载消失误报为Runtime污染工作目录。只将这三个工具管理路径排除，其余目录一致性检查保留；复验结果单列。

这两项是本次夹具/环境判定问题，不改变此前两次task_003的业务评分。此前第一次无申请，第二次实际申请Gold而参考要求Silver，原分数均为0；不能将它们改称纯粹评分误判。

## 尚未证明的部分

本次对P3-03a/03c/04a/06a及采集提供局部证据，不将整项标为通过。未完成的负例包括越权阶段调用、跨会话错误答案、执行中改绑等；静态条件的实际执行、意图切换、重复/迟到回调、失联及持久化边界也仍需专门真实组件夹具。原22子用例完整验收状态继续pending。

尚未调用真实模型复测推荐行为，因此不宣称英文子任务或产品推荐问题已彻底解决，也不宣称分数提高。后续业务诊断需新建冻结批次，保留实际模型版本、全部层输入输出和官方原分数；不读取隐藏参考来决定Agent输出。
