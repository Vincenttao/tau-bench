"""Retain a reviewed Core lookup error while running other independent P07 cases."""
import json,time
from pathlib import Path
from retry_resolution import status,sha,one,interruption_evidence,review_file,retry_path

def eligible(primary):
 p=Path(primary);st=status(p)
 if not (p.name.startswith('P07-') and p.name.endswith('-r00-a00') and st
         and st.get('status')=='execution_error' and st.get('error_type')=='RuntimeError'
         and not list(p.glob('episodes/*/result.json')) and review_file(p) is None
         and not retry_path(p).exists()):return False
 try:detail=one(p,'exception.txt').read_text()
 except ValueError:return False
 logs=list(p.glob('episodes/*/java/*.stderr.log'))
 return ('Core execution error: Ability not found in resource_mgr: unlock_discoverable_agent_tool' in detail
         and len(logs)==1 and '[LLM]   tool_call: unlock_discoverable_agent_tool' in logs[0].read_text()
         and 'tool_name=unlock_discoverable_agent_tool outcome=not_found' in logs[0].read_text())

def create_review(primary,process_evidence):
 p=Path(primary).resolve();proof_path=Path(process_evidence).resolve();target=p/'retain-core-error-review.json'
 if target.exists() or not eligible(p):raise ValueError('Unreviewed specific Core lookup failure required')
 proof=json.loads(proof_path.read_text());m=json.loads((p/'manifest.json').read_text())
 if (proof.get('original_attempt')!=str(p) or proof.get('remaining_matching_processes')!=[]
     or proof.get('controller_terminal_exit')!=1 or proof.get('recorded_at',0)<one(p,'status.json').stat().st_mtime):raise ValueError('Fresh terminated-process evidence required')
 if len(m.get('episodes',[]))!=1 or m['episodes'][0]['task_id']!=status(p).get('task_id'):raise ValueError('Case identity mismatch')
 r={'classification':'retain_core_ability_lookup_error','original_attempt':str(p),'recorded_at':time.time(),
    'original_evidence':interruption_evidence(p),'process_evidence':str(proof_path),'process_evidence_sha256':sha(proof_path),
    'continue_unstarted_only':True,'technical_gate_resolved':False,'additional_attempts_allowed':0,
    'reviewer':'Codex source and execution log review','score_policy':'Original Core execution error unscored. No retry, score substitution, business code change or P08 release.'}
 target.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');return r

def retained_core_error(primary):
 p=Path(primary).resolve();file=p/'retain-core-error-review.json'
 if not file.exists():return False
 r=json.loads(file.read_text())
 if (not eligible(p) or r.get('classification')!='retain_core_ability_lookup_error'
     or r.get('original_attempt')!=str(p) or r.get('continue_unstarted_only') is not True
     or r.get('technical_gate_resolved') is not False or r.get('additional_attempts_allowed')!=0
     or r.get('original_evidence')!=interruption_evidence(p)
     or r.get('process_evidence_sha256')!=sha(Path(r['process_evidence']))):raise ValueError('Invalid or changed Core error retention evidence')
 return True
