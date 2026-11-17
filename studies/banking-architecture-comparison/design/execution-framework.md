# 四实验公共执行框架详细设计

日期：2026-11-17。状态：实施设计，未实现。本文细化已确定的四方案，不增加方案、正式题数或重复次数；不改变study.json及其冻结契约。本文件中的模块和接口是拟新增内部接口，不是已经存在的MOA、A2A或Hub API。

## 1. 目标与范围

公共框架只负责可重复的测试环境、协议、资源监督和证据。四个方案负责各自的业务判断与执行机制。正式规模仍为22题×4方案×1次，比较方案2−1、3−2、4−2。

首要约束：共享代码不能把优化方案的业务判断带入对照组。相同工具、同一银行环境和相同外层限制是公共条件；MOA委派、业务权限分工、Hub证据审查和业务幂等是被测能力，必须显式归属方案。

## 2. 层次和模块责任

| 模块（拟新增） | 输入/输出 | 负责内容 | 禁止承担的内容 |
| --- | --- | --- | --- |
| StudyCompiler | study/plan/契约 → CompiledArmSpec | 校验和展开共同条件、输出差异清单 | 自动修改Skill、替换模型或放宽预算 |
| EpisodeSupervisor | spec/位置 → episode终态 | 初始化、deadline、进程、暂停/停止和清理 | 推断银行业务顺序、替用户同意 |
| OfficialSessionAdapter | 客户消息/Agent动作 → 官方交互及结果 | 沿用官方用户模拟、工具主体和评分接口 | 修改客户分支、隐藏参考或评分语义 |
| BankingBridge | 标准工具请求 → 原始官方回执 | Schema、身份/episode绑定、通信和调用记录 | 增加银行资格判断、纠正参数、通用业务去重 |
| ArmDriver | 客户输入/回执 → 业务动作或答复 | 方案特定Agent执行链、内部状态 | 绕过官方桥直接修改DB |
| TraceCollector | 边界事实 → 事件与文件索引 | actor、request、effect、usage关联 | 依据工具名字猜测成功、伪造缺失调用 |
| ResultAssembler | 官方结果/结构验收/运行状态 → 三轴结果 | 原分数、分母、缺失和停止原因 | 把框架通过换算为官方reward |
| FailureAnalyzer | 冻结证据 → 偏差定位报告 | 评估端离线解释 | 将隐藏参考反馈给仍在运行的Agent |

公共桥可拒绝非法Schema、错episode或已到期的新请求，并保持各方案一致。官方工具自身的银行规则仍由官方环境执行，不旁路、不补强。禁止把Hub语义检查放入默认公共桥，或用公共代码自动重排业务操作。

## 3. 四方案在框架中的装配

| 方案 | ArmDriver内部 | 公共桥前的方案专属边界 |
| --- | --- | --- |
| 1 | DeepAgent + 原始Skill | 无新增MOA/Hub控制；原框架工具边界保留 |
| 2 | 同一DeepAgent + 优化Skill | 同方案1；只换冻结Skill资产 |
| 3 | MOA原生阶段规划 + 业务Agent + 原生Session/A2A | 按实际业务Agent核验工具归属，委派/输入关联 |
| 4 | DeepAgent + 优化Skill + 实际Go Hub | 证据/授权/参数绑定、最终效果许可和业务幂等 |

方案3沿用业务权限桥和原生阶段约束；方案4的Hub控制由专属组件拥有。BankingBridge只暴露同样的工具执行接口；对3/4通过显式接线接入专属控制，不通过默认开关影响1/2。

共用MCP传输不能自动去除模型提出的两次相同业务请求：不同request_id可能是独立意图，也可能是业务错误，由被测方案判断。相同传输request_id的重复到达应拒绝/标记传输异常，不盲目重新调用；不得在公共层推断业务意图并返回缓存“成功”。观察到严重重复效果后，按共同停止契约处置，不将补救建议注入Agent。

## 4. 拟新增内部接口

| 接口 | 输入 | 输出/事件 | 所有权 |
| --- | --- | --- | --- |
| compile_study | study与四个plan路径 | CompiledArmSpec、差异清单、输入hash | 评测侧只读输入 |
| prepare_runtime | spec、分配的端口/目录 | RuntimeDescriptor、实测能力及就绪状态 | driver启动组件；监督器核对 |
| begin_episode | EpisodeContext、公开初始输入 | episode/session关联、准备事件 | 官方环境状态由公共侧拥有 |
| advance | 客户消息或官方工具回执 | bank_tool_request / customer_reply / await_customer / terminal | 业务选择由driver拥有 |
| request_pause / cancel | episode、原因、deadline | accepted及独立quiesced确认 | 接受请求不等于已停 |
| inspect_runtime | episode | 组件身份、状态、在途请求、checkpoint摘要 | 只读观察，不据此虚构完成 |
| close_episode | 官方结束或异常 | 资源释放和最终证据索引 | 不自动重跑或抹掉异常 |

advance允许异步事件流，不要求把完整MOA塞进一次同步函数调用。工具请求由真实组件产生；适配层不得替Agent添加缺失操作。客户侧工具交给官方模拟器，内部Todo/路由消息不得作为客户对话或官方工具操作。

所有请求携带study_id、arm_id、episode_id、session_id、request_id、actor_id、deadline和trace_id。MOA记录实际plan revision/todo/toolCallId/A2A task/context，不强加新business_task_id/checkpoint协议；Hub另有decision_revision/grant_id/operation_id/payload_hash。字段缺失不能由控制器猜测；结构扩展有schema版本。

## 5. EpisodeContext与状态隔离

EpisodeContext包含本题官方环境句柄、受限工具接口、公开政策、输出目录、剩余预算和证据记录器。完整task、reference actions、评分DB和覆盖表只保留在评估端；driver只能收到官方Agent正常可见的信息。

同题多个MOA业务Agent共享同一银行环境，不分别复制DB；不同题和不同方案独立初始化可变状态。只读KB可共用，但检索参数固定。Hub账本按episode隔离，不跨正式题学习或重用知识。持久化命名空间至少包含study/arm/episode，不能只用task_id。

运行位置状态为planned/running/scored/unscored/cancelled，另记stop_scope和censored；业务Todo和A2A任务状态不能替代位置终态。已评分结果不得因后续日志失败被覆盖为null；缺失必要证据另标review状态。

## 6. 预算与故障传播

监督器持有唯一episode截止时间；所有driver和子调用继承剩余预算。恢复、创建子Agent、重连不能刷新整题时钟。具体数值以study.json为准，本文不复制数值成为第二份权威配置。

公共错误至少区分invalid_input、environment_error、model_error、simulator_error、tool_transport_error、deadline、cancelled、unknown_effect和contract_violation。不得把内部异常拼成客户回答。错误必须带实际作用范围；范围不明按全study停止，不擅自判为局部。

业务写入发送后超时不代表未执行。实际请求、官方接受与回执分别记事件；停止新派发后保留unknown_effect。业务对账由已授权的方案操作完成；监督器可以离线检查证据，但不能偷偷替Agent补业务动作。

## 7. 条件等价与防止方案混入

方案1/2必须来自同一代码构建与公共框架版本；展开条件差异只允许Skill资产和由其导致的实际上下文变化。不能要求整段模型输入hash相同，因为Skill不同；应分别比对系统提示词、工具Schema、公共策略及标注的Skill区域。

每题输出declared capabilities、observed component descriptors和verification evidence三部分。声明不等于观察；观察到Go进程不等于Go参与效果判断。详细矩阵见[能力装配设计](capability-assembly.md)。

禁止能力应有负例：方案1/2不加载Hub包或MOA路由；方案3不得调用快速意图；方案4停Go不能继续银行写入。若运行中装配与声明不符，终止受影响方案或study，保留已产生结果并标记不可作为原方案对照。

## 8. 实施顺序与当前状态

先完成可复用的官方环境循环和DeepAgent driver，再验证1/2的唯一变量；并行设计MOA/Hub接口，但没有完成真实组件门禁前不执行正式22题。最小链路、责任和验收见[交付计划](delivery-and-diagnosis.md)。

本文各模块尚未实现为统一控制器。已有prepare.py继续只做输入准备，executable=false；本文不是新运行入口或真实业务验证记录。
