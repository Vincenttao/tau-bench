"""Offline report renderer. Reads official cases; never invokes a model or changes cases."""
import collections, hashlib, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / '.deps/tau2-bench/data/tau2/domains/banking_knowledge/tasks'
OUT = ROOT / '银行Bench全部测试用例-中文版.md'
NOTES = Path(__file__).with_name('case-notes.tsv')
notes = {}
for line in NOTES.read_text().splitlines():
    num,title,scenario,focus=line.split('\t')
    key='task_'+num
    assert key not in notes
    notes[key]=(title,scenario,focus)
files=sorted(BASE.glob('task_*.json'))
cases={p.stem:json.loads(p.read_text()) for p in files}
assert set(cases)==set(notes), (set(cases)-set(notes),set(notes)-set(cases))
old=json.loads((ROOT/'runs/enterprise-v02-timeout1200-20261114/P07-full-suite-analysis.json').read_text())
assert set(cases)=={x['case_id'] for x in old['rows']}
labels={
'apply_for_credit_card':'申请信用卡','transfer_to_human_agents':'转接人工客服','log_verification':'记录身份核验','change_user_email':'修改用户邮箱','submit_referral':'提交推荐','get_referral_link':'获取推荐链接','submit_transaction':'提交消费交易',
'submit_cash_back_dispute_0589':'提交返现争议','update_transaction_rewards_3847':'更新交易奖励','get_card_last_4_digits':'获取卡片尾号','file_credit_card_transaction_dispute_4829':'提交信用卡交易争议',
'initial_transfer_to_human_agent_0218':'发起人工转接（0218入口）','initial_transfer_to_human_agent_1822':'发起人工转接（1822入口）','request_human_agent_transfer':'记录客户人工转接请求','emergency_credit_bureau_incident_transfer_1114':'征信紧急事件转接',
'order_replacement_credit_card_7291':'订购替换信用卡','get_user_dispute_history_7291':'查询用户争议历史','get_pending_replacement_orders_5765':'查询在途补卡订单','get_all_user_accounts_by_user_id_3847':'查询全部用户账户','pay_credit_card_from_checking_9182':'从支票账户偿还信用卡','get_closure_reason_history_8293':'查询销卡原因历史','log_credit_card_closure_reason_4521':'记录销卡原因','apply_credit_card_account_flag_6147':'设置信用卡账户标记','apply_statement_credit_8472':'发放账单抵扣','close_credit_card_account_7834':'关闭信用卡账户',
'submit_credit_limit_increase_request_7392':'提交提额申请','get_credit_limit_increase_history_4829':'查询提额历史','get_payment_history_6183':'查询还款历史','approve_credit_limit_increase_5847':'批准提额','deny_credit_limit_increase_5848':'拒绝提额',
'open_bank_account_4821':'开立银行账户','deposit_check_3847':'存入支票','transfer_funds_between_bank_accounts_7291':'银行账户间转账','close_bank_account_7392':'关闭银行账户','get_bank_account_transactions_9173':'查询银行账户流水','apply_checking_account_credit_5829':'补记支票账户款项',
'get_debit_cards_by_account_id_7823':'查询账户借记卡','freeze_debit_card_3892':'冻结借记卡','get_credit_card_accounts_by_user':'查询用户信用卡账户','unfreeze_debit_card_3893':'解冻借记卡','close_debit_card_4721':'注销借记卡','order_debit_card_5739':'订购借记卡','activate_debit_card_8292':'激活借记卡','get_debit_dispute_status_7483':'查询借记卡争议状态','file_debit_card_transaction_dispute_6281':'提交借记卡交易争议','clear_debit_card_fraud_alert_4892':'清除借记卡欺诈警报','request_temporary_debit_card_limit_increase_8374':'申请借记卡临时提额','reset_debit_card_pin_6284':'重置借记卡PIN','apply_savings_account_credit_6831':'补记储蓄账户利息','submit_interest_discrepancy_report_7294':'提交利息差异报告','get_referrals_by_user':'查询用户推荐记录'}
keylabels=dict(x.split('=',1) for x in '''account_class=账户产品
account_id=账户ID
account_type=账户类型
actual_apy=实际APY
address=地址
agent_tool_name=代理可发现工具名
amount=金额
amount_difference=金额差额
annual_income=年收入
arguments=内层参数
card_action=卡片处理方式
card_design=卡面设计
card_id=卡片ID
card_in_possession=是否持有实体卡
card_last_4_digits=卡片后四位
card_name=卡名称
card_type=卡类型
category=交易类别
check_amount=支票金额
checking_account_id=支票账户ID
closure_reason=销卡原因
contacted_merchant=是否已联系商户
credit_card_account_id=信用卡账户ID
credit_card_type=信用卡类型
credit_type=补记类型
customer_max_liability_amount=客户最高责任金额
customer_name=客户姓名
cvv=卡片校验码（模拟数据）
date_of_birth=出生日期
delivery_fee=配送费
delivery_option=配送选项
denial_reason=拒绝原因
design_fee=卡面费用
destination_account_id=收款账户ID
discoverable_tool_name=用户可发现工具名
discovery_date=发现日期
dispute_category=争议类别
dispute_reason=争议原因
disputed_amount=争议金额
eligible_for_provisional_credit=是否符合临时贷记资格
email=邮箱
expected_apy=应适用APY
expedited_shipping=是否加急
expiration_date=有效期
flag_type=账户标记类型
full_name=姓名
issue_noticed_date=发现问题日期
last_4_digits=卡片后四位
limit_type=限额类型
merchant_name=商户名称
months=月数
name=姓名
new_credit_limit=新信用额度
new_email=新邮箱
new_limit=新限额
new_pin=新PIN（模拟数据）
new_rewards_earned=修正后奖励
partial_refund_amount=部分退款金额
phone=电话
phone_number=电话号码
pin=PIN（模拟数据）
pin_compromised=PIN是否泄露
police_report_filed=是否已报警
provisional_credit_eligible=是否符合临时贷记资格
purchase_date=购买日期
reason=原因
requested_increase_amount=申请增加额度
resolution_requested=期望解决方式
rho_bank_subscription=是否有Rho-Bank+订阅
shipping_address=收件地址
source_account_id=付款账户ID
summary=摘要
time_verified=核验时间
transaction_date=交易日期
transaction_id=交易ID
transaction_type=交易类型
user_id=用户ID
written_statement_provided=是否提供书面陈述'''.splitlines())
enums={'checking':'个人支票账户','savings':'个人储蓄账户','business_checking':'企业支票账户','business_savings':'企业储蓄账户','keep_active':'保留卡片有效','cancel_and_reissue':'取消并补发','full_refund':'全额退款','partial_refund':'部分退款','unauthorized_fraudulent_charge':'未经授权或欺诈扣款','duplicate_charge':'重复扣款','goods_services_not_as_described':'商品或服务与描述不符','goods_services_not_received':'未收到商品或服务','incorrect_amount':'金额错误','canceled_subscription_still_charging':'取消订阅后仍扣款','refund_never_processed':'退款未到账','fee_refund':'费用退款','fraud_suspected':'疑似欺诈'}
def val(v):
    if v is True:return '是'
    if v is False:return '否'
    if v is None:return '空值（原文null）'
    if v=='':return '空字符串'
    if isinstance(v,str):return (enums[v]+'（`'+v+'`）') if v in enums else '`'+v.replace('`','\\`').replace('\n',' / ').replace('|','\\|')+'`'
    return '`'+json.dumps(v,ensure_ascii=False).replace('|','\\|')+'`'
def action_info(a):
    args=a.get('arguments',{});name=a['name'];wrapped=name in ('call_discoverable_agent_tool','call_discoverable_user_tool')
    inner=args.get('agent_tool_name',args.get('discoverable_tool_name',name))
    if name=='unlock_discoverable_agent_tool':desc='解锁代理工具：'+labels[inner]
    elif name=='give_discoverable_user_tool':desc='向客户提供工具：'+labels[inner]
    else:desc=labels.get(inner,inner)
    params=dict(args)
    if wrapped and isinstance(params.get('arguments'),str):
        parsed=json.loads(params['arguments'])
        params=parsed
    else:
        wrapped=False
    return name,inner,desc,params,wrapped

def group(n):
    if n<=16:return '产品咨询、推荐奖励与服务升级'
    if n<=29:return '返现核算、卡片收益与审批状态'
    if n<=35:return '消费争议与紧急转接'
    if n<=41:return '盗刷补卡与多卡争议'
    if n<=49:return '销卡、留客与虚假陈述'
    if n<=54:return '提额与跨操作依赖'
    if n<=71:return '开户、资金迁移与组合收益优化'
    if n<=76:return 'ATM费用核查与账户选择'
    if n<=92:return '借记卡生命周期、争议与安全处置'
    if n<=97:return '储蓄利息核算与差额纠正'
    return '复杂推荐资格与奖励优化'
counts=collections.Counter(group(int(k[-3:])) for k in cases)
hashes={p.stem:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
missing=[f'{n:03}' for n in range(1,103) if f'task_{n:03}' not in cases]
lines=['# 银行 Bench 全部测试用例（中文版）','',
'用途：后续汇报、场景介绍和评测范围说明。覆盖当前 τ³ banking_knowledge 题库全部 **97题**，与已执行P07正式清单逐题一致。', '',
'本文件是**中文汇报整理版**：逐题归纳客户背景、诉求、关键交互条件和能力考察点，并列出官方验收动作及参数。不是对重复模拟器台词、全部账户初始化流水或知识库政策的逐字翻译；这些内容可通过各题原始JSON链接核查。', '',
'## 使用说明','',
'- 客户姓名、产品名、工具名和标识保留原文，中文解释其含义；金额一般为美元，以原始题目为准。日期保持源格式，模拟业务日期不替换成当前日期。',
'- “场景与关键条件”描述客户行为；“能力考察点”是本次整理的分析归纳；“官方验收”来自题目数据。三者不能互相替代。客户声称的余额、费率、资格或操作成功不一定真实。',
'- DB表示比较官方模拟数据库终态；ACTION表示按官方动作规则检查；NL_ASSERTION表示自然语言断言。参考动作列表不是必须逐字复现的唯一轨迹，动作序号也不自动构成严格顺序验收。',
'- 身份核验、解锁工具和客户侧操作的主体分别保留。“客户”动作由用户模拟器执行，不能改成Agent代办。存在compare_args时，展开表会明确记录；空列表并不表示必须比较所有参数。',
'- 资料含隐藏用户行为及官方目标，仅供评测与汇报，不能放入被测Agent的Skill、检索库或提示。示例客户及卡片字段均来自测试数据。',
'- 本册不混入历史通过/失败结果，不把官方目标视为真实银行政策。例如005的目标动作存在明显安全解释风险；091年龄与生日、082/086日期叙述等原文差异不在此擅自修正。',
'- 题号跨度001—102，但源题库缺少 '+ '、'.join(missing)+'；本册不补造这些题。', '',
'## 场景分类概览','', '| 分类（汇报归类） | 题数 |','|---|---:|']
for g,c in counts.items():lines.append(f'| {g} | {c} |')
lines+=['| **合计** | **97** |','','## 全量目录','','| 题号 | 中文标题 | 官方判分 |','|---|---|---|']
for k,d in cases.items():lines.append(f'| [{k}](#{k}) | {notes[k][0]} | '+ '、'.join(d.get('evaluation_criteria',{}).get('reward_basis',[]))+' |')
lines+=['','## 逐项用例','']
unknown_keys=set();unknown_tools=set();action_count=0
for k,d in cases.items():
    title,scenario,focus=notes[k];ev=d.get('evaluation_criteria',{});actions=ev.get('actions',[])
    lines += [f'<a id="{k}"></a>',f'### {k}｜{title}','',f'**场景与关键条件：** {scenario}','',f'**能力考察点（整理）：** {focus}','',f'**官方判分：** '+ '、'.join(ev.get('reward_basis',[]))+f'。原始参考动作共{len(actions)}项。','']
    summaries=collections.Counter()
    for a in actions:
        name,inner,desc,params,wrapped=action_info(a)
        if name not in ['log_verification','unlock_discoverable_agent_tool','give_discoverable_user_tool']:
            summaries[(a.get('requestor','未标注'),desc)]+=1
    lines+=['**官方目标动作概览：** '+'；'.join(({'assistant':'Agent','user':'客户'}.get(role,role)+'：'+desc+f'×{num}') for (role,desc),num in summaries.items())+'。','']
    if k=='task_005':lines+=['**判分边界：** 源目标确实包含将特殊绕过码写入核验字段并修改邮箱。本册忠实保留，不认可其作为企业身份核验规范；汇报时应将benchmark一致性与安全验收分开。','']
    if ev.get('nl_assertions'):
        assert k=='task_102'
        lines+=['**自然语言验收目标：** 应推荐TechFlow Labs而非Ember Analytics办理Sky Blue Account推荐，并识别Ember Analytics已超过该产品4年的公司年龄上限。','']
    for field in ['communicate_info','env_assertions']:
        if ev.get(field):lines+=['**额外官方条件（原文）：** `'+json.dumps(ev[field],ensure_ascii=False)+'`','']
    agent_data=((d.get('initial_state') or {}).get('initialization_data') or {}).get('agent_data') or {}
    tablecounts={name:len(obj.get('data',{})) for name,obj in agent_data.items() if isinstance(obj,dict) and isinstance(obj.get('data'),dict)}
    if tablecounts:lines+=['**初始数据范围：** 本题显式初始化的数据表记录数为 '+ '；'.join(f'`{name}`：{num}' for name,num in tablecounts.items())+'。这是题目增量配置，不代表完整数据库记录总数。','']
    else:lines+=['**初始数据范围：** 未列出可直接统计的agent_data表覆盖；使用官方基础环境及本题其他配置，以源文件为准。','']
    lines+=['<details>','<summary>展开官方参考动作与完整输入参数（中文字段说明）</summary>','','| 序号 / 主体 | 参考动作 | 参数及比较约定 |','|---|---|---|']
    for i,a in enumerate(actions,1):
        name,inner,desc,params,wrapped=action_info(a);action_count+=1
        if inner not in labels:unknown_tools.add(inner)
        unknown_keys.update(set(params)-set(keylabels))
        ps='；'.join(f'{keylabels.get(key,key)}（`{key}`）={val(v)}' for key,v in params.items()) or '无参数'
        if 'compare_args' in a:
            ps+='；原始compare_args='+val(a['compare_args'])
        route=f'`{name}`'+(f' → `{inner}`' if inner!=name else '')
        if wrapped:ps+='；内层参数按原始JSON字符串解码展示，原传输类型保持字符串'
        lines.append(f'| {i} / '+{'assistant':'Agent','user':'客户'}.get(a.get('requestor'),str(a.get('requestor')))+f' | {desc}<br>{route} | {ps} |')
    lines+=['','</details>','']
    src=BASE/f'{k}.json';lines += [f'**来源：** [原始用例JSON]({src.relative_to(ROOT).as_posix()})；SHA-256：`{hashes[k]}`。','']
lines+=['## 汇报引用建议','',
'本题库覆盖从单一咨询到多目标、跨账户、长交互的银行任务。复杂性主要来自条件逐步披露、客户陈述与系统事实冲突、产品规则交叉、操作前置依赖、全局配额、金额计算及用户侧工具协同。', '',
'可以选择003说明多条件产品筛选，041说明四卡十六笔争议和全局额度，054/062说明依赖排序与状态变化，080/092说明多卡生命周期及风险分类，097说明多账户核算，102说明事实纠正与约束优化。它们是场景代表，不是已验证的框架能力证明。','',
'此用例册只说明“测什么”。测试装配、Skill/MCP接入、模型版本、实际结果与耗时应在汇报的其他部分单独说明。']
assert not unknown_keys,unknown_keys
assert not unknown_tools,unknown_tools
OUT.write_text('\n'.join(lines)+'\n')
audit={'source_count':len(cases),'chinese_case_count':len(notes),'same_as_p07':True,'missing_numbers_in_001_102':missing,'reference_action_count':action_count,'source_sha256':hashes,'output_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'scope':'Chinese report-oriented case descriptions, all reference actions and input parameters; not full simulator dialogue/database translation','unknown_parameter_keys':sorted(unknown_keys),'unknown_tools':sorted(unknown_tools)}
Path(__file__).with_name('catalog-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
assert hashes=={p.stem:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
print(json.dumps({k:v for k,v in audit.items() if k not in ['source_sha256']},ensure_ascii=False,indent=2))
print('characters',len(OUT.read_text()))
