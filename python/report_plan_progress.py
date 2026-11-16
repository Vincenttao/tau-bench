"""Regenerate plan observations from original attempt records without changing scores."""
import json
from pathlib import Path
from summarize_plan import summarize,SUITE

def report():
 data=summarize();lines=['# 阶段性测试分析','','仅报告当前已执行样本。官方benchmark成绩、企业完整验收和运行诊断分别记录。','',
 '| 阶段 | 题号 | 官方评分 | 模拟耗时秒 | 已观测Token |','|---|---|---|---|---|']
 for row in data['attempts']:
  lines.append(f"| {row['plan_item']} | {row['case_id']} | {row['official_reward'] if row['official_reward'] is not None else '未知/在途'} | {row['duration']} | {row['observed_tokens']} |")
 lines+=['',f"有评分 {data['completed_scored']} 次，其中reward=1为 {data['official_reward_one_count']} 次；在途或未评分 {data['pending_or_unscored']} 次。这里只描述已启动尝试，不代表全量97题成功率。",'',
 '## 已发现问题与证据边界','',
 'P04最终通过，但有工具错误和Rail拒绝，不能据此报告执行故障率为0。',
 '官方NL裁判路由返回404，task_102后续保留未评分，禁止替换裁判混入主成绩。',
 'Runtime/MOA MAIN路径、完整安全验收和故障注入尚未完成，因此企业指标正式值仍按采集缺口报告。']
 for p in sorted(SUITE.glob('P*-*/replay-summary.json')):
  d=json.loads(p.read_text());lines+=['',f"严格离线回放证据：{p.relative_to(SUITE)}；模型调用={d['model_calls']}，字段差异={d.get('field_counts', '见原始诊断')}。实际业务状态差异已定位，模型/框架责任归因仍待核验。"]
 lines+=['','## 后续执行','',
 'P05三题及P06六次已完成。P06中task_001三次均reward=1，task_041三次均reward=0；两题各自的三条精确工具请求序列均不同。该结果未证明每次轨迹相同，也不直接定位模型或框架责任。',
 '原P07在task_018执行异常后停止：14题有官方评分、1题异常未评分、82题未开始。原始证据保留；独立timeout1200复验及新条件批次不补入原P07成绩。',
 'Token仅记录，无累计预算。各首尝试及错误保留，重试不能择优替换。P07—P16仍需按计划完成，当前目标未达成。']
 remediation=SUITE/'timeout-remediation.json'
 if remediation.exists():
  lines+=['','## 超时采集修复验证','',
   '真实Core专项使用本地挂起的流式模型，1秒整轮期限触发completion_timeout，桥接层识别成功；网关调用为0。此专项证明当前错误可观测，不追溯证明历史task_018的直接原因。',
   '12项离线回归通过。监督专项的4×10¹⁵ Token为本地模拟计量，只用于验证不按Token停止，不计入真实测试用量。',
   '新执行器在未设置--token-limit时关闭Token停止条件，记录null；旧执行器及其运行中尝试保留原始占位值。',
   '分层超时配置和修复证据见timeout-remediation.json；当前复验状态以对应status.json和进程为准。']
 (SUITE/'阶段性测试分析.md').write_text('\n'.join(lines)+'\n')
 return data
if __name__=='__main__':
 d=report();print(json.dumps({k:d[k] for k in ['completed_scored','official_reward_one_count','pending_or_unscored']}))
