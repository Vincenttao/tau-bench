# MOA v9 单轮22题分析

状态：已完成执行与离线复核。批次：`../runs/moa-v9-single-round-20261118-01`。仅汇总本批次每题一次结果；历史成绩不并入。配置与执行要求见[本轮计划](../moa-single-round-implementation-plan-20261118.md)。北京时间2026-11-18 00:08:29至02:19:13，批次墙钟约2小时11分钟。

## 结论与22题结果

通过5题，已评分未通过13题，执行异常未评分4题，未启动0题。固定分母成功率为5/22=22.73%；已评分成功率为5/18=27.78%；评分覆盖率为18/22=81.82%。异常题的reward为null，不伪造0分。单轮已暴露明显能力与接入问题，不能由历史单题成功推断稳定成功。

| task | 终态 | 本轮主要结果或阻断 |
| --- | --- | --- |
| 003 | 未通过 | 实际申请Gold，与参考Silver不同；推荐引入额外排序偏好 |
| 017 | 通过 | 两笔返现争议正确由客户提交，后续确认存在读取范围问题 |
| 031 | 通过 | 服务不符争议及keep_active正确，未误发临时贷记 |
| 036 | 未通过 | 补卡业务完成；额外查询尾号造成严格DB差异 |
| 043 | 未通过 | 关闭原因登记跨领域越权，MCP断流，后续变更目标未推进 |
| 051 | 未通过 | 人工转接被误认付款交接，未执行付款与后续提额 |
| 060 | 未通过 | 先开后关正确；唯一DB差异为关闭原因文字 |
| 076 | 通过 | Purple开户符合参考；后续借记卡查询暴露字段不一致 |
| 077 | 未通过 | 有权限的领域误称不能补信用卡，用户提前结束 |
| 093 | 未通过 | 利息纠正被派给无写权限领域，两次拒绝后未完成 |
| 098 | 通过 | 按双方合计奖励和实际存款选择Blue，客户提交推荐 |
| 016 | 未通过 | 缺少适用政策依据的第三方卡使用断言改变客户选择 |
| 022 | 未通过 | 漏一笔异常，另将四笔多返现排除于争议流程之外 |
| 033 | 通过 | 实际执行参考要求的人工转接；不代表付款已修复 |
| 041 | 未通过 | 计划确认/拒绝解析循环，零官方工具调用 |
| 049 | 未通过 | 信用卡关闭越权导致MCP失败，最终max_steps |
| 054 | 未通过 | 提额和争议已完成；换卡语义错误导致越权及后置跳过 |
| 062 | 未通过 | 跨产品资料规则泛化，客户决定暂缓开户与迁移 |
| 072 | 未评分 | 领域模型600秒无首段，子任务失败后MAIN未及时终结 |
| 087 | 未评分 | 官方用户模拟器TLS握手超时 |
| 097 | 未评分 | 官方用户模拟器DNS解析失败 |
| 100 | 未评分 | MAIN模型请求地址解析失败 |

机器审计见[batch-audit.json](../runs/moa-v9-single-round-20261118-01/review/batch-audit.json)，逐题官方结果见[case-results.csv](../runs/moa-v9-single-round-20261118-01/review/case-results.csv)。审计确认22题顺序、各启动一次、同一配置/制品、seed=300、trial=0、终态与台账一致。18个已评分案例均完成严格离线状态重放；官方task_049因max_steps未给出db_check，报告中的9处状态差异来自独立重放，不能冒充其官方DB检查。其余官方评分与独立重放分列保留。原始文件保存在本地忽略目录，不纳入Git。

## 执行前验证

Java路由、英文确认与Todo边界检查通过；MOA的12项Python回归通过，包含实际八Runtime启动；共同契约校验确认69操作、22题。编译后、运行前统一准备22份manifest与制品快照；串行运行。冻结输入、执行责任、各题started及终态记录在批次progress.json。未修改本轮业务prompt、Skill或授权实现。

## task_003：未通过，申请产品与参考不同

官方reward=0，user_stop，119.306秒。严格离线重放确认两处应用记录差异，实为实际Gold申请与参考Silver申请的替换；agent DB及user DB均不匹配。原始证据见批次`review/task_003-evidence.json`及`review/task_003-trace.md`。

M001客户要求零外币交易费、购买保护及可能达到至少$100,000额度，旅行是主要消费。M026答复将Silver的$100,000上限视为满足条件，但引入了超过门槛的额度余量作为推荐理由，推荐Platinum并给出免年费Gold替代；客户M027先用非规范Gold名称申请被拒，M029改用规范名称Gold Rewards Card后成功，M031停止。参考动作是客户申请Silver Rewards Card，不能把实际申请成功视为官方目标成功。

证据边界：Platinum的10%返现来自本次检索文档`doc_credit_cards_platinum_rewards_card_002`，不能认定为模型编造。用户初始并未明确年费排序，故不能仅凭隐藏参考断言任何非Silver推荐必然违反用户要求。可确认的问题是MAIN/领域推荐增加了额度余量偏好，用户最终选择与参考不同；需结合条件资格、年费与旅行收益比较分析推荐合理性。首次工具名值不规范由官方用户模拟器发出，不应归因于MOA工具调用参数生成。全程没有提额/争议/换卡等跨域依赖，因此不支持将本题归因为v9跨任务顺序或核验授权故障。

改进候选（本轮不修改）：满足硬条件后，明确区分用户偏好与自行推定的排序；对订阅资格未知的候选使用一致处理；按用户确认的费用/收益排序再建议产品。官方分数保持0，不能强制客户选择隐藏参考。

## task_017：通过，返现争议由客户正确提交；交互仍有缺口

官方reward=1，user_stop，331.937秒；严格重放的agent DB及user DB均匹配，无数据库差异。证据见批次`review/task_017-evidence.json`和`review/task_017-trace.md`。

M001客户要求检查返现。M009/M013提供两个身份因素，M016原生log_verification写入成功。M040/M046核对五笔交易，发现Amazon少141点、Sushi Kashiba少40点，合计181点/$1.81；旅行与软件4%、其他1%、向下取整的计算与记录对应。M042/M044给客户提交工具；M047由官方user主体调用两次，产生两个现金返现争议记录。客户侧操作主体正确，未由领域Agent代替客户提交。官方DB通过的核心是核验记录及这两条客户提交记录。

通过不等于全部动作检查匹配：give_discoverable_user_tool实参包含额外arguments，参考只要求工具名，017_1动作检查未匹配，但reward_basis为DB，数据库结果仍通过。M061重复核验日志返回记录可能已存在。客户要求确认收件后，领域只能读取普通交易争议而无法读取cash_back_disputes队列，不能用普通争议记录缺失否认客户侧现金返现回执；最终答复明确了此限制并执行人工转接（M081）。MAIN一度把内部skill-13调用标识说成转接参考，后续又澄清它不是可核验的客户case编号。M051/M077确认文本复制整个context JSON，形成明显交互负担。均属于需要修订的观察项，不改变官方通过结论。

成功原因：对应政策与交易证据足够、金额计算正确、官方user侧工具路径被实际执行、原生核验授权生效。建议后续保持可见客户工具回执为该写入的证据，不跨存储类型做否定判断；确认文本提取当前动作，避免展示完整历史包装；不将内部调用ID升级为客户业务编号。

## task_031：通过，酒店服务争议分类和临时贷记资格正确

官方reward=1，user_stop，185.184秒；严格重放agent/user DB均匹配。M001客户投诉Marriott订房与实际房型不同且商户拒绝处理。M017给出核验信息；M033明确选择goods_services_not_as_described、全额退款$167.34以及keep_active，M035确认今天发现。M048通过客户侧get_card_last_4_digits查询尾号，M051给出5320。M060报告争议SUBMITTED，未冒充退款已解决；无临时贷记，与该争议类别政策一致。证据见批次`review/task_031-evidence.json`和`review/task_031-trace.md`。

成功原因：没有把服务不符误当欺诈；有客户明确选择支持card_action=keep_active；尾号由客户侧工具获得；完整业务字段最终写入参考一致的争议记录。这里的keep_active正确，不能把task-054需要cancel_and_reissue推广成所有争议的固定值。

剩余观察：031_1及031_4动作检查未匹配但DB通过，说明动作实参与参考的差异不必然改变最终状态；需要保留动作与DB两种结果。M018/M042/M052确认出现历史JSON包装，M038/M040还需客户反复选择领域，交互成本偏高。题目通过证明这次业务结果正确，不证明普通补参/候选选择体验已经良好。

## task_036：未通过，目标换卡已完成，额外卡尾号工具日志导致严格DB不匹配

官方reward=0，user_stop，754.668秒，所有参考动作检查匹配。严格离线重放却在agent/user DB各发现同样两处额外记录：user_discoverable_tools中的get_card_last_4_digits GIVEN，以及user_discoverable_tool_calls中该工具针对cc_890389b165_silver的CALLED。不存在换卡参数、配送地址、核验日志或订单的其他DB差异。因此本题零分直接归因于额外工具日志，而非换卡漏执行或另行关闭账户。证据见批次`review/task_036-evidence.json`及`review/task_036-trace.md`。

过程：M001查询交易，M026展示16笔交易，M027报告两笔不认识的消费。M086对争议与换卡分别assessment；M087要求立即换卡。M100继续评估并提供尾号查询，M103客户运行后给出5320、工作地址及接受加急$10。M112实际完成fraud_suspected加急换卡，寄2500 Woodward Avenue, Suite 300；M113明确暂不提争议。参考要求也仅核验日志与该换卡订单，不要求提交两笔争议。查询尾号与潜在后续争议相关，但不是换卡工具的必填字段；扩大到未来争议准备增加了影响评分的日志。

第二条独立问题链：M112读回CLOSED，MAIN解释为客户不希望的账户关闭，随后多次委派card-lifecycle/account-closure只读核查，M182转人工。官方tools.py的order_replacement_credit_card_7291在创建订单后直接给credit_card_accounts原行写入status=CLOSED与closed_date，用于表达取消旧卡；同一工具回执又称账号保留、新卡换号。参考重放执行相同工具，因此同样有此字段。不能把该CLOSED归因为MOA误调用销户。模型对字段/业务概念映射的歧义解释，引发了长评估、客户担忧与额外转接，是交互与环境语义问题；也不能据此证明系统已实际整户注销。将ORDERED表述为in transit也超出回执证明的状态。

建议（不改本轮）：按当前已授权动作所需字段取证，潜在争议的尾号查询在客户选择提争议时再执行；不为匹配隐藏参考禁止所有有业务依据的额外读取。官方工具日志参与DB精确比较应在报告中明确。对旧卡状态与账户状态使用权威字段定义核对，不凭字段名推定额外业务动作；没有可证实的shipping回执不说in transit。原reward=0保持，另列“参考换卡动作全部完成、严格DB因额外日志失败”。

## task_043：未通过，跨域工具归属拒绝后陷入候选选择循环，年费减免未完成

官方reward=0，user_stop，386.989秒。严格重放发现6处DB差异：缺少annual_fee_waived一年标记、annual_fee销卡原因记录，以及四种discoverable工具调用状态。支付及核验结果与参考一致；参考最终目标是减免年费并保留卡，不是强行完成销卡。证据见批次`review/task_043-evidence.json`、`review/task_043-trace.md`和原始task_043/supervisor.log。

M001因年费要求销卡，M024发现$75余额，M025/M029要求checking还款。领域Agent指出付款在独立领域，MAIN后续安排payments并实际清偿：M080确认checking 05扣$75、余额$2775，卡余额$0。但销卡Agent随后执行log_credit_card_closure_reason_4521（其stderr.log 2381附近的skill-17）时，DomainBoundary抛PermissionError。冻结归属表将该操作及apply_credit_card_account_flag_6147都分配给card-lifecycle-agent；account-closure-agent不被授权。HTTP处理线程未将拒绝转换成可恢复结构化结果，而是断开请求，Java记录HTTP header parser received no bytes/EOF、Tool execution error: MCP call failed; no automatic business retry。MAIN最终收到AGENT_EXECUTION_FAILED。这是工具归属与任务路由不一致叠加拒绝异常处理的问题，不是本题模型连接超时，也不是Todo错误。

M081客户要求重试；M082起界面要求选择account-closure-agent或card-lifecycle-agent。客户反复给出“1 — account-closure-agent”等自然语言，界面重复不推进。M107后客户转向费用减免，M125/M129明确要求一年减免保留卡，M137撤回关闭请求；界面仍停在旧候选列表。M147客户因循环退出并打算电话处理。这里同时有选择输入兼容性、等待阶段目标变化处理问题，不能仅解释为客户没有选择。完整对话JSON被反复放进确认/候选文本，进一步增加交互负担。

直接评分原因是缺少减免标记及原因记录等DB状态；较早的触发点是销卡Agent越过其工具归属，后续恢复又没有转入能处理减免的card-lifecycle任务。付款成功不补足最终减免目标。建议后续核对“业务任务需要哪些前置写操作、由哪个Agent负责”，在委派前明确跨域责任；授权拒绝应回传可解释结果而非丢HTTP响应；候选等待需要识别合法选择及撤销/变更目标。不得为解决本题直接扩大所有Agent全部写权限。本轮保留原失败，不实施修复或重跑。

## task_051：未通过，人工转接被当作付款委派，未执行还款与提额

官方reward=0，user_stop，417.117秒。严格重放10处DB差异：checking仍$5000（参考$2000），信用卡余额仍$3000（参考$0），额度仍$4000（参考$5000），缺少high_utilization拒绝记录与$1000请求记录，以及5类工具调用状态。核验日志已成功。证据见批次`review/task_051-evidence.json`、`review/task_051-trace.md`及MAIN模型记录。

M046正确识别利用率75%高于Bronze的70%门槛，并将30%请求调整为25%/$1000上限；客户M047/M051同意全额$3000还款且要求交payments处理。问题发生在M052：credit-limit-agent调用的是transfer_to_human_agents(reason=specialized_department_required)，M053回执明确是human agent，而非payments-agent任务或付款回执。M054 MAIN却说付款请求已交payments并让客户等入账。后续M055起MAIN确实委派payments-agent，但query是只读查询已交接付款的状态，不是执行pay_credit_card_from_checking_9182；又把提额写入以付款入账为前提的when，所以始终跳过。

M097模拟客户在文字中说已在app付款，但没有任何对应客户/Agent工具调用，官方环境余额不变。后续重复读取得到同一事实。M124又把标准转账约12小时的文档解释成这笔卡还款的等待依据；M125客户因此选择稍后回来。等待叙述不能制造官方数据库资金变化，M052人工转接成功也不证明任何真实payments任务会异步执行。

本题有两个层次：未执行已授权还款、因此未完成提额，是实际业务缺口；参考还要求先提交并以high_utilization记录拒绝，本次选择在不符合时不提交，故即使后续提额完成仍可能缺少参考要求的审计记录。不能把后者单独视为模型危险行为。领域声明没有checking读取能力也不准确：get_all_user_accounts_by_user_id_3847在共享授权表中允许payments读取，但本题并未调用。

建议后续将human transfer、MOA同伴委派、资金写入及到账回执分开表达；MAIN收到用户授权还款后，使用现有native stage给payments下达明确付款任务，拿回回执/余额后再给提额任务，不把状态查询当作付款。禁止在缺乏付款提交证据时用“等结算”解释资金未动；检查权威Skill/目录后再声明能力缺失。本轮保持失败结果，不扩展跨进程恢复或异步账本。

## task_060：未通过，业务顺序和状态正确，唯一差异为销户原因自由文本

官方reward=0，user_stop，484.024秒。严格重放只有一处差异：Green checking的closure_reason实际为“Customer request - no longer needed; empty Green checking account, funds already moved out by customer; no early closure fee applies”，参考为默认“Customer requested closure”。其余开户、销户、余额及工具记录一致，060_6动作检查因显式reason不同未匹配。证据见批次`review/task_060-evidence.json`、`review/task_060-trace.md`。

M040先assessment解释账户关联；M041客户同意先savings，并给出提款次数、$2500–$3000余额、daily compounding、ATM rebate、goals及loyalty要求。M086领域评估选择Silver Plus，M087确认且要求无内部转账、Blue不变、savings开好后再关Green。实际M094调用open_bank_account_4821成功，M106调用close_bank_account_7392；M110汇总新savings OPEN/$0、Green CLOSED、Blue OPEN/$1500且未转账。此前销户破坏后续开户资格的问题本次未复现，但这是一轮结果，不能宣称规划稳定性100%。

直接失败来源是工具可选reason的精确字符串比较：官方tools.py中close_bank_account_7392默认reason即“Customer requested closure”；参考省略该参数，本次补充说明落入最终DB。实际说明与用户陈述相容，并无证据证明它代表不当销户。建议将此列为“业务目标完成、自由文本DB不一致”的参考敏感项，保留官方0分；可在通用工具使用规范中减少无业务需要的可选参数或使用契约默认值，但不得从隐藏参考复制特定字符串来追分。重复核验日志被拒仍是本轮可见问题；没有额外错误写入。

## task_076：通过，Purple开户完成；后续借记卡查询失败未纳入参考目标

官方reward=1，user_stop，208.485秒；所有参考动作匹配，严格重放agent/user DB均一致。参考仅要求身份日志与Purple checking开户。M001要求欧洲出差ATM成本低及early direct deposit；M024比较Bluest与Purple并询问高额资金门槛，M025客户拒绝$75000门槛选Purple，M027授权开户，M048确认新账号0516a4f7bca2d8d1 OPEN/$0。据此本题官方通过有真实写入证据。见批次`review/task_076-evidence.json`、`review/task_076-trace.md`。

后续客户M049要求合格后加急借记卡。M069读取新账号，明确account_type=checking/account_class=Purple Account；M070调用get_debit_cards_by_account_id_7823，M071却返回“not a checking account”。官方tools.py 3953行使用account.get("class", "")判定checking，新开户记录只有account_type而无class，构成环境字段契约不一致。该调用是卡信息读取，没有实际order_debit_card写入；不能把它说成订单提交后的失败。M074 MAIN却表示“tried to submit the order”，又让客户选择立即重试，而此前已知开户至少3个business days且$25余额的前提还不满足；这属于失败步骤定位和前提保持问题。实际没有订单、没有费用，不影响参考只要求的开户DB。

重复核验日志被拒、M026一度把ATM operator fee描述为不在rebate范围内（后文纠正为超cap仍自付）、将early direct deposit能力说成active也应保留观察。建议报告区分账户产品支持某功能与已配置工资入账，区分读取失败与订单写入失败。官方基准实现的字段问题作为外部依赖单列，不在本轮修改；后续卡业务请求未完成，因此不将本题官方1分扩展为“所有后续客户要求均完成”。

## task_077：未通过，冻结两张借记卡后误称信用卡换卡属其他团队，模拟客户提前结束

官方reward=0，user_stop，171.364秒；严格重放19处差异，主要是缺少信用卡replacement、两张旧借记卡后续解冻/关闭、Bluest新卡订单及激活和相关工具日志。实际两张借记卡停在FROZEN，信用卡仍ACTIVE。证据见批次`review/task_077-evidence.json`、`review/task_077-trace.md`。

M011客户同意先冻结两张不确定是否丢失的借记卡，M033确认且补充Silver信用卡也在钱包；M034/M040实际冻结两张卡。M047授权信用卡新号换卡并确认地址，选择“not sure—precaution”和免费配送。M056领域却说信用卡replacement由另一个credit-card team处理，虽已查到无pending order，仍只询问是否转接。M057客户答应并输出###TRANSFER###，模拟器结束；轨迹无transfer_to_human_agents实际调用，更无order_replacement_credit_card_7291调用。不能把###TRANSFER###文本当作真实转接回执。

授权核对：card-lifecycle-agent本来拥有信用卡replacement写权限；本题无边界拒绝证据。较可信的原因是领域Agent错误拆分自身能力/职责，把同属card-lifecycle的信用卡换卡说成另一团队；客户模拟器在口头转接同意时提前结束，后续借记卡补办流程无机会继续。参考包含RUSH/PREMIUM，但这次还未执行任何订单，不能仅用标准/加急或设计参数冲突解释失败；也不能覆盖客户“免费、不付额外配送或设计费”的要求去匹配隐藏参考。

建议后续让领域依据实际授权目录和已加载Skill确认能执行什么，再声明能力不足；MAIN汇总中区分“提议转接、客户同意、实际调用和回执”。参考所需的后续冻结→解冻→关闭→补办→激活只按可见客户授权和工具前提推进，不以评估答案驱动Agent。该题不是连接超时或Todo崩溃，关键是业务过程过早停止。

## task_093：未通过，利息更正写操作分配到错误领域，两次权限拒绝

官方reward=0，user_stop，238.714秒；严格重放5处差异：余额少$33、缺少interest correction交易、两个工具调用状态，以及客户额外发起的人工转接请求。参考要求$33更正及expected APY 4.275/actual 4.0的报告。证据见批次`review/task_093-evidence.json`、`review/task_093-trace.md`与task_093/supervisor.log两段PermissionError。

M001储蓄月息偏低，候选却只有payments/dispute；M003客户指出它不是转账或卡支付，最终选payments。M046计算$144000储蓄、4.0%基础+0.25%checking boost+0.025%relationship，October $480应为$513，差$33；M047授权更正及报告。payments-agent尝试apply_savings_account_credit_6831被DomainBoundary拒绝，M052 MAIN报下游执行失败。M053客户要求再试，改选dispute，M100重算并把relationship资格视为未证实，建议$30；客户同意后同一更正工具再次被拒。冻结归属表将apply_savings_account_credit_6831及submit_interest_discrepancy_report_7294都授权给account-opening-agent，payments/dispute无权。两个Agent均能先解锁该discoverable工具并获参数说明，但真正调用时权限边界才拒绝，造成EOF/MCP失败。不是远端模型超时或核验日志未授权。

MAIN的候选描述只把account-opening说成开户/身份维护，没有体现其被分配的储蓄利息维护写能力，路由与工具归属不一致。错误后MAIN说“nothing reviewed/calculated”和先前数字无依据，但轨迹已有真实账户/交易读取和计算；执行未完成不意味着此前所有证据失效。这种全盘否定导致客户重复解释并在M107要求人工。MAIN又声称现有能力无人能转人工，尽管各领域可调用原生transfer_to_human_agents；客户自行提交转接请求后退出，产生额外DB记录。

金额资格分歧是次要问题：第一条$33与参考一致，第二条$30更保守但均未写入；无论选择哪一金额，错误路由都阻断写入。建议后续对齐领域可见职责与实际工具归属，执行前校验discoverable目标权限并返回结构化拒绝，使用正确领域而不是在两个无权领域间重试；汇总保留已验证事实、计算假设与失败写入的区别；人工转接不能因未列为独立候选而宣称不存在。本轮不修实现、不补跑。

## task_098：通过，按可投入资金比较双方推荐奖励，客户实际提交Blue referral

官方reward=1，user_stop，134.615秒；所有参考动作匹配，严格重放agent/user DB一致。参考是核验、get_referrals_by_user及客户submit_referral(Blue Account)。见批次`review/task_098-evidence.json`与`review/task_098-trace.md`。

M001客户要求约$600首次工资可投入时双方合计最高推荐奖励。M011完成核验信息并确认不住同址，但室友历史账户未知。M046按入金门槛筛选，推荐Blue $35+$30=$65，比较Green Fee-Free $55及Green/Light Blue $50，并把更高入金方案作为额外选择而非假定客户能投入。检查推荐次数/年度上限，保留年龄及过去12个月账户资格未知，不承诺必然奖励。M047客户决定提交，之后官方客户工具生成referral ID 5f230becda28c604，M049确认提交。成功点是比较目标使用“双方合计奖励”、约束使用现实资金门槛、实际客户提交与Agent建议分开。

观察边界：客户端提交成功并不证明室友开户、满足留存条件或奖励已支付，本题只验证推荐记录；9天支付节奏只作为客户提问留存，不做未来到账保证。候选确认曾需两次选择，但最终进入正确开户领域，无越权写入或跨域错误。该题不依赖复杂任务顺序，不能用其通过证明MAIN多任务规划稳定性。

## task_016：未通过，政策答复改变客户选择，未产生参考中的朋友卡交易

官方reward=0，user_stop，143.208秒。严格重放仅一处差异：缺少friend_user_5839的Best Buy $750 Shopping交易（750 points）；核验日志一致。该交易参考主体是user侧submit_transaction，不是要求MOA替朋友执行银行写操作。见批次`review/task_016-evidence.json`与`review/task_016-trace.md`。

M019客户指明最近Silver referral；M026正确说明IN_PROGRESS、60天$750消费及奖金可能延后入账。M027客户说持有朋友交给其保管的卡，询问代购是否有助满足门槛；M038 MAIN/领域答复绝对化声称即使朋友许可也不支持第三人使用，并称可能被标记且大概不计入。M039客户接受并决定让朋友自己消费，结束。没有工具错误或权限拒绝，直接机制是建议改变了模拟客户后续动作。

证据边界：领域检索包含authorized users相关内容，但主要是储蓄账户与其他产品，针对信用卡第三人代购禁止的查询没有返回可直接支撑该绝对结论的条款。可确认存在政策依据不足和推断扩大；不能由此断言现实业务中第三人使用朋友卡必然允许。客户没有证明正式授权用户资格，持有卡或口头代购建议也不等于完整授权。建议后续澄清授权身份、依可见政策解释净消费及退款影响，并让持卡人自主进行合法正常消费；不为了匹配隐藏参考诱导客户执行特定商户/金额交易。保留官方0与这一授权/参考敏感性，不能归因为多任务顺序或v9日志授权失效。

## task_022：未通过，77笔审计漏Dell，多计返现被错误排除于客户争议流程

官方reward=0，user_stop，423.807秒；严格重放10处DB差异，对应5笔缺失cash_back_disputes及其5条客户工具调用日志。实际客户只提交5笔少计返现，参考要求10笔全部异常。核验及已提交5笔一致，没有额外错误争议。证据见批次`review/task_022-evidence.json`、`review/task_022-trace.md`。

M001要求四张卡全部交易、同时检查高低返现。M034审计77笔，称68匹配、9异常，列5笔少计与4笔多计。M035客户明确要求双向准确，少计走争议，多计也要review。M100交付少计5个ID，M101/M102后客户实际提交，M107给出5条SUBMITTED。多计4笔被转人工而未提供同一提交路径；Dell则完全未识别。缺失ID为Dell txn_ffeede5eeacd、Target txn_ba8b473f295d、ThredUp txn_4f5e249acc6c、Facebook Ads txn_1a4918670323、Marriott Bonvoy txn_30cb41175311。

根因一是检索覆盖：Dell真实交易已在工具返回中（Business Silver，$1849.99，Software，18499 points），但运行轨迹没有返回doc_business_credit_cards_business_silver_rewards_card_005。离线查询官方文档确认Dell属于软件bonus排除商户，只得1%而非10%；因此实际应1849点，是多计16650点。不是交易没读取，也不能说模型看见该排除条款后故意忽略；是排除文档未进入本次证据，领域按类别10%误判正确，汇总“审计完成”过早。

根因二是无依据收窄流程：运行轨迹早期已返回cash-back dispute政策，措辞是实得与应得有discrepancy、适用于所有信用卡交易，没有“只少计”限制。M096/M100却声称该路径仅用于少计，将4笔已识别多计全部转给specialist，遗漏与参考一致且有政策支持的客户提交路径。客户选择5笔是被Agent先前分类与交付工具引导，不能简单归咎客户漏点。奖励更正需已批准争议是后续调整前提，不能用它证明多计不能先提交审查。

后续还有跨存储核查问题：客户提交cash_back_disputes后，Agent查transaction_disputes为空，再反复报告5笔未验证并转人工；两种表不相同，工具提交回执本身已证明写入，无法查询该表不等于回执仅是用户叙述。没有重复提交，重复风险被控制住，但用户体验和证据汇总仍有偏差。本次没有Todo崩溃或连接错误作为首因。

建议后续每卡在基本费率之外覆盖exceptions/exclusions及promotion规则，对每笔异常保留所依据文档，未覆盖时不宣称全部审计完成；按政策真实范围处理差异，不自行加入under-only限制。提交清单要覆盖全部客户授权的异常，并核对官方客户回执；未来修改须在新批次验证，本轮不补跑。

## task_033：通过，特定付款未入账场景按政策完成分阶段人工升级

官方reward=1，user_stop，126.687秒；所有参考动作匹配，严格重放agent/user DB一致。参考只有initial_transfer_to_human_agent_1822、initial_transfer_to_human_agent_0218和最终transfer_to_human_agents，不要求修改付款或利息。见批次`review/task_033-evidence.json`、`review/task_033-trace.md`。

M001客户报$2847.53已从checking扣款、三天后卡未入账、两天后账单结算。M005无完整核验资料且要求人工；payments领域检索专门流程，M016说明第一步升级。M017再次请求，M024说明两阶段已记录但线路busy、还未连接；M025再要求转接，M030实际完成最终工具转接并保留未确认付款入账及无费用减免的事实。未为转接读取/修改未经核验的个人账户数据。与task_051把人工转接当作已付款不同，这里客户目标本身就是政策规定的人工升级，原生工具回执与计划相符。

通过边界：只证明该题的升级记录及工具流程与参考一致，不能证明human已实际修复后端付款或避免$50利息。多轮显式请求和确认增加交互成本，但本题有适用专项政策，不把所需阶段简单判为无意义重试。说明真实业务成功目标必须结合本题参考范围和可见客户后续要求界定。

## task_041：未通过，确认阶段重复，尚未进入任何银行工具执行

官方reward=0，user_stop，65.787秒。严格重放24处差异：16笔transaction_disputes、核验日志、客户尾号工具提供/4次调用，以及2类agent工具状态均缺失。全程官方银行tool_calls=0。见批次`review/task_041-evidence.json`与`review/task_041-trace.md`。

M001要求四张卡的欺诈及其他问题争议。MAIN生成dispute与card-lifecycle两个assessment-only任务，确认文本主要内容是“do not file/submit”。M003客户答Yes.（带句点）后，M004原样再次确认。M005客户澄清要实际提交不是只读，随后反复No./No加解释、请求16笔争议和人工转接，直到M023放弃。没有进入领域核验、政策读取或写入阶段，因此不能把零分归因为16笔金额计算、临时贷记选取或Todo错误。

机制证据：当前界面要求exactly Yes or No，运行中Yes.及No加说明均未推进或退出等待；既有Java确认回归只覆盖纯Yes/No和带修改条件的拒绝批准，没有覆盖句点/自然语言拒绝/转接。拒绝必须停止授权执行，但不应把多次拒绝和新目标一直困在同一确认。v5后assessment-only三阶段策略在此暴露交互适应性：客户认为只读不能满足目的，而系统未解释它是提交前必需步骤，也没有吸收客户拒绝进入新请求。

建议后续在保持授权边界下处理简单标点与明确否定，拒绝后关闭当前确认并允许客户重新选择目标或转人工；不要把附加条件的Yes直接当无条件批准。将评估向客户解释为核验/提交前准备，并清楚说明本次不会自动提交、还需后续授权，避免仅罗列长串禁止动作。保留本次0分，不代替客户补一个纯Yes、不重放该题。

## task_049：未通过，信用卡销户路由与工具授权矛盾，失败持续扩散至步数上限

官方reward=0，termination=max_steps，649.781秒；严格重放9处差异。Green未关闭，Crypto未记录annual_fee原因/未获$5 retention statement credit，缺少相关工具状态及参考客户人工转接请求。核验和若干eligibility读取完成。证据见批次`review/task_049-evidence.json`、`review/task_049-trace.md`及task_049/supervisor.log。

客户M001要求四张信用卡关闭先Green。M084读取四卡状态；M085明确Green符合条件并要求关闭。MAIN再安排长assessment，M152才核实Green $0、无争议/无pending replacement、超过60天，并要求确认2150点处理。M153客户接受45天窗口要求立即销卡。account-closure-agent随后调用close_credit_card_account_7834（stderr 963行、skill-23），但冻结归属表只允许card-lifecycle-agent执行信用卡销户，DomainBoundary抛PermissionError，M164报告失败。其余deposit账户关闭工具与信用卡关闭职责未在MAIN候选描述中区分，导致“account closure”自然被路由到无权Agent。

M165客户要求新尝试，M168又失败；M169暂缓Green要求Eco，后续Eco/Gold的只读assessment也在同一account-closure服务不断MCP失败，日志显示EOF/no automatic business retry与读取空结果。是首次权限拒绝关闭HTTP请求后服务调用链未健康恢复的级联，不是用户的新目标全部不合规。Eco的SHIPPED替换卡和Gold $175余额也各有真实阻塞，不能因失败而忽略这些政策约束；但参考会继续到Crypto年费$5留存和人工转接，本次在M193后达到200步预算，未到该阶段。

早期只读确认/重复身份询问、已具备Green条件后再次长评估和积分确认消耗大量步骤，放大后续故障。MAIN较准确地说明没有销户回执、没有把失败当成功；但继续让客户在同一已失败领域反复请求，没有定位权限owner或提供有效新路由，导致200步耗尽。不是通过加大max_steps就能修复工具归属问题。

建议后续明确deposit账户关闭与credit-card生命周期写入边界，对齐MAIN描述/候选绑定/工具授权；越权拒绝返回结构化业务错误并保持MCP可用，而非抛出导致断流；复用已完成eligibility证据、处理结果未知时先核对，不自动重放写操作。本轮保留首次episode，不提高步数或补跑。

## task_054：未通过，提额与争议已成功；误认争议自带换卡造成越权，失败汇总丢失已完成写入

官方reward=0，user_stop，515.565秒。严格重放只有4处差异：缺replacement工具CALLED状态、缺订单，以及旧卡status/closed_date未改变。CLI与核验、争议记录（包括cancel_and_reissue）均与参考一致。054_12批准动作未精确匹配是JSON字符串键顺序不同，但真实额度与DB正确；这不是零分的直接原因。见批次`review/task_054-evidence.json`、`review/task_054-trace.md`与transaction-dispute-agent.stderr.log 1354行附近。

M050三个assessment正确识别争议/pending replacement阻塞CLI；M051客户选择先CLI并授权换卡，但提出条件性假设“如果争议自带换卡就别重复下单”。M080解释50%上限，M081接受$2500，M088批准工具成功将额度升至$7500。M058核验日志成功。M114争议工具成功返回dsp_f8aab53ad42b，临时贷记eligible，写入cancel_and_reissue。先CLI后争议的顺序与参数本身没有回归。

关键错误在MAIN本次stage_plan（MAIN模型轨迹第20行）：要求“using cancel-and-reissue ... so that this same filing replaces ...”，并将“this dispute filing and its own card action”作为边界。它把客户的条件假设当成工具真实效果，要求dispute服务本身换卡；另一个card-lifecycle任务只在前者没有换卡且成功返回时执行。官方争议工具契约明确card_action仅record-keeping，不下replacement订单，MAIN没有把这一事实传清楚。领域提交争议成功后读回无订单，于stderr skill-25实际调用order_replacement_credit_card_7291，参数与参考一致，但actor是transaction-dispute-agent，无权限；DomainBoundary抛PermissionError引起MCP EOF/A2A失败，后置card-lifecycle依赖不满足而未执行。

补充追溯：不能把错误只归给客户假设或MAIN。争议领域首轮assessment（deepagent-events.jsonl第69行）已错误声称“that same filing can perform the cancellation/reissue”，并把另单replacement说成重复；card-lifecycle assessment（其第63行）却明确推荐“file dispute → order replacement”。MAIN应核对这两份互相矛盾的动作语义。它选择沿用争议领域的错误解释，客户又在M051重复该条件假设，形成错误证据在对话与委派中被强化的链条。v9有“矛盾先核实”的prompt，但本次未落实。

M124/M128 MAIN将下游失败描述为“no dispute receipt exists/no dispute open”，与M114真实成功回执及最终DB矛盾。业务写入没有因后续Agent异常回滚。客户M125提出新请求重试，但该领域MCP已失败，第二次也未修复；M129客户请求人工并输出###TRANSFER###后结束，没有真正换卡。因而本题更严重的缺口是部分写入成功后丢失证据并错误宣告未写入，可能诱发不安全重复提交；本次只有一条实际争议记录，没有观察到重复成功写入。

这解释同样v9曾单题通过而本轮失败：上次MAIN明说cancel_and_reissue是record only、实际订单由card-lifecycle执行；本次委派文本反过来要求争议本身换卡。不是v9未加载、日志授权失效或模型超时，也不能宣称prompt更新已确定性保证职责语义。建议基于真实操作契约表达副作用与写责任，客户的“如果”必须验证；遇下游异常保留成功回执，状态未知应先读回，不说全部没执行。不得把失败依赖简单绕过来下单，应通过原生新请求核对已有争议和零订单后再授权正确领域。保持本轮0，不用历史v9的1分替代。

## task_062：未通过，正确保护开户前置关系，但跨产品资料要求泛化使客户暂缓全部执行

官方reward=0，user_stop，464.520秒；严格重放15处差异。两新账户均不存在，Bronze与Evergreen仍OPEN，$150/$3500未移动，缺少开户/转账/关户工具记录；仅身份核验与读操作完成。参考要求Navy Blue business checking、Silver Plus savings，转$150+$2500到savings、$1000到business，再关两个旧户。证据见批次`review/task_062-evidence.json`、`review/task_062-trace.md`。

M001四项目标按客户叙述先关再开；M080 assessment正确指出business opening要求无CLOSED账户、personal savings需成熟checking关系，故先开后关，Evergreen需保留到开户。M081客户同意顺序，提出费用、提款、daily compounding和ATM等约束；M104推荐Navy Blue与Silver Plus基本符合目标。M105客户选定但询问资料是否可后补；M112建议先gather LLC packet，M113采纳并保留原资金计划。M115后客户多次明确“selections only，不提交”，最终退出等待资料。MAIN没有越过最终明确暂缓指令执行，这一点正确；零分原因是四个真实业务目标始终未产生状态，而不是错误先关闭导致资格丢失。

前置门槛的来源存在适用性问题：本次检索的Joint Business Holders Legal Requirements（business savings joint holders + user roles _005）要求形成文件、resolution、tax/beneficial-owner资料；Platinum Reserve enterprise savings _004提corporate documentation；business Bronze credit-card申请条目里EIN还注明if available。MAIN/开户Agent把这些当作新LLC Navy Blue开户前必须准备完整packet的依据，Navy Blue自身文档没有该完整硬条件；内部open_bank_account_4821只收user_id/account_type/account_class，没有上传或验证这些材料的字段。M114也承认没有文档字段和已公开的Navy后补流程，却仍将完整packet视为必须。

不能由工具字段少就推断真实银行不需要法定资料；本结论限于该benchmark可见政策与执行合同，模型没有证明所引用资料规则适用于当前单一LLC Navy Blue开户。客户被这一建议引导暂缓，尚未授权写入时不能为评分强开。建议后续分别列必需且适用的政策前提、待确认资料和其他产品说明；缺乏适用依据时不自行升级为阻塞所有目标的硬门槛，独立目标能否先推进需明确客户选择。重复身份询问、末尾把Silver Plus月费说成$10而此前产品文档$8也属上下文一致性观察。本题没有模拟器异常，本轮官方评分正常保留0。

## task_072：未评分，领域模型无首段超时后，父任务未及时结束

官方summary为execution_error/RuntimeError，reward=null。局部journal保留32条消息、13次官方工具调用，包括核验成功、账户及ATM交易和政策读取；没有费用退款写入。不能把读取成功算业务通过，也不能将本题记为官方0分。见批次review/task_072-evidence.json、task_072目录内日志及线程转储。

领域模型请求于01:49:21开始，600秒没有首段，01:59:21报BEFORE_FIRST_SEGMENT、stream_idle timeout after600.0s。实际领域层600秒与计划摘要的120秒不同，后续必须明确每一层生效配置，不能只查manifest顶层。子A2A任务转FAILED，MAIN父任务仍WORKING。MAIN虚拟线程转储显示停在A2AEnabledServeOrchestrator.syncResumePending的CompletableFuture.get，实际依赖字节码也有无界get；这是父链路等待没有及时结束的直接证据。仅凭转储无法确定是回调丢失、通知时序还是其他关联问题。

外层只GetTask轮询同一父任务，没有重新发送原query；最终桥1500秒截止返回“task remained working until the bridge call deadline”。启动和回收在内的台账耗时约1564秒。需要分别解决模型无响应与子失败向父终态传播，不能只延长等待。没有429、HTTP5xx或上下文过长响应证据，也不能证明是模型计算复杂导致。切换官方DeepSeek曾避免某次超时，不代表所有请求均不会超时。本题未生成有效官方评分，局部journal与线程转储仍保留。

## task_087：未评分，官方用户模拟器TLS握手超时

summary为execution_error/Timeout，reward=null，台账约177秒。三个消息、八Runtime已启动，MAIN返回候选选择，但官方工具调用为零。异常发生在官方用户模拟器生成下一条消息时：httpcore.ConnectTimeout，SSL handshake operation timed out，经OpenAI客户端与LiteLLM包装为Timeout。见review/task_087-evidence.json中的完整异常链。

不能据此判定MOA借记卡处置政策错误，也没有足够业务执行可分析。问题属于用户模拟器模型连接，和072的领域流超时、MAIN父任务等待不是同一层故障。本轮保留异常，不补跑。

## task_097：未评分，首次客户发言前DNS解析失败

summary为execution_error/InternalServerError，reward=null，台账约39秒。只保留初始助手问候，用户模拟器尚未产生客户任务，Runtime启动数与官方工具调用均为零。底层为[Errno -3] Temporary failure in name resolution，依次包装为ConnectError、APIConnectionError及LiteLLM InternalServerError。见review/task_097-evidence.json。

异常类型名称不能证明服务端返回了HTTP500；这里的直接证据是名称解析失败。没有发生储蓄利息核算，不能据此评价MOA利息业务能力。

## task_100：未评分，MAIN首个模型请求地址解析失败

summary为execution_error/RuntimeError，reward=null，台账约102秒。用户已提出LLC推荐奖励问题，八Runtime已启动，journal两条消息，官方工具调用为零。MAIN首次模型请求报ConnectException，其底层是UnresolvedAddressException；A2A转TASK_STATE_FAILED，桥再抛“Runtime task is neither completed nor awaiting customer input”。见review/task_100-evidence.json及banking-moa.stderr.log的异常链。

这里的RuntimeError是运行桥包装，实际阻断是模型地址解析。不能归因为推荐规则选错、授权拒绝或领域职责误判；业务尚未执行。

## 跨案例判断与后续优先级

通过的五题共有特征是实际工具路径与参考目标对应，且职责和政策语义足够明确。017/031正确提交争议，098按可行资格优化推荐，076完成参考开户，033完成参考人工转接。076与033的通过范围有限，不能把开户评分通过解释为后续卡片可用，把转接评分通过解释为付款已修复。通过题也存在重复确认、完整JSON泄漏到确认文本和跨存储查询问题。

| 优先级 | 证据与问题 | 建议修订范围 | 后续验证 |
| --- | --- | --- | --- |
| P0 | 043/049/093职责描述、候选与工具授权不一致；054争议域越权换卡 | 对齐操作归属、领域说明与发现范围；保留最小权限；拒绝返回结构化错误并保持MCP连接 | 已有权限契约和路由回归；新批次才做真实复测 |
| P0 | 054已有争议回执却被汇总为未提交 | MAIN和领域保留已成功回执；区分部分成功、失败、未知；明确争议card_action仅登记 | 回执后下游故障的定向测试，确认不声称回滚、不盲重写 |
| P1 | 041确认/拒绝循环；043目标变更未处理 | 改善标点、拒绝和新请求解析，沿原生确认/新请求路径处理 | 补充确认边界检查，不放宽修改后计划的授权 |
| P1 | 051虚构付款交接；077虚构不能服务；093未发现正确利息责任域 | 依据实际领域目录及工具能力委派；区分人工转接和Agent委派 | 检查实际调用主体与写入，不以自然语言交接为完成 |
| P1 | 022漏检及自创多返现不受理；062跨产品条件泛化 | 检索覆盖完整适用政策；明确事实、适用前提和未知 | 逐笔清单/政策依据审查，禁止读取隐藏答案指导模型 |
| P1 | 072子失败后父任务持续等待；087/097/100连接异常 | 分层记录实际timeout、关联父子终态；完善基础设施异常分类 | 定向故障验证，不重复本批次业务写入 |
| P2 | 036额外工具状态、060关闭原因文字导致严格DB失败 | 分开记录客户目标完成度与官方精确匹配，减少不必要工具调用 | 保留官方分数，不硬编码隐藏参考文字追分 |

本次没有修改业务实现、prompt、Skill或权限以追分。单轮不是稳定性估计，不构成相对其他架构的提升证明，也未完成原架构设计全部核心driver验收。是否开展修订及下一批次应基于上述证据决定。

## 执行控制偏差与交付核查

实施计划为运行前冻结原件，保留其中“待执行”及当时入口说明，不用执行后状态覆盖其hash。本报告和progress.json记录当前已完成状态；新增批量封装位于`../python/run_single_round.py`。报告整理时曾修改计划措辞，审计据此检出文档hash变化；现已恢复与冻结清单完全相同的原件，业务制品和原始结果均未改变。

计划要求持续连接故障时停止新题，但本轮runner只将连续两个精确类型APIConnectionError/InternalServerError计作连续连接失败。末四题包装类型依次为RuntimeError、Timeout、InternalServerError、RuntimeError，导致计数重置，未提前停止。这是测试控制实现对异常根因分类覆盖不足，不能掩盖，也不应删除后四题以提高比例。下一批前应覆盖Timeout与包装后的DNS/连接根因；本批已终结，不重启任何已启动题。

最终核查：22题顺序与共同cohort一致、每题starts=1、18题官方评分与summary一致、4题无评分明确保留、制品和冻结输入hash一致，审计audit_pass=true。离线分析不调用模型，不更改官方分数。证据链接指向本地runs忽略目录；Git交付仅整理报告、计划及执行/分析脚本，原始日志和客户轨迹不提交。原始证据继续本地保留。
