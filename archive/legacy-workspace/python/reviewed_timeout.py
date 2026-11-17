"""Continue unstarted P07 cases after a reviewed timeout; never resolve its gate."""
import json,time
from pathlib import Path
from retry_resolution import status,sha,interruption_evidence,review_file,retry_path

def eligible(primary):
 primary=Path(primary);st=status(primary)
 return (primary.name.startswith('P07-') and primary.name.endswith('-r00-a00')
         and st is not None and st.get('status')=='timeout'
         and not list(primary.glob('episodes/*/result.json'))
         and review_file(primary) is None and not retry_path(primary).exists())

def create_review(primary,process_evidence):
 primary=Path(primary).resolve();proof_path=Path(process_evidence).resolve()
 target=primary/'retain-timeout-review.json'
 if target.exists() or not eligible(primary):raise ValueError('Unreviewed original P07 timeout required')
 proof=json.loads(proof_path.read_text());st=status(primary)
 if (proof.get('original_attempt')!=str(primary) or proof.get('remaining_matching_processes')!=[]
     or proof.get('controller_terminal_exit')!=1 or proof.get('recorded_at',0)<next(primary.glob('episodes/*/status.json')).stat().st_mtime):raise ValueError('Fresh terminated-process evidence required')
 manifest=json.loads((primary/'manifest.json').read_text())
 if len(manifest.get('episodes',[]))!=1 or manifest['episodes'][0]['task_id']!=st.get('task_id'):raise ValueError('Case identity mismatch')
 review={'classification':'retain_original_episode_timeout','original_attempt':str(primary),
         'recorded_at':time.time(),'original_evidence':interruption_evidence(primary),
         'process_evidence':str(proof_path),'process_evidence_sha256':sha(proof_path),
         'continue_unstarted_only':True,'technical_gate_resolved':False,'additional_attempts_allowed':0,
         'reviewer':'Codex technical timeout review','score_policy':'Original timeout remains unscored; no substitution, retry, timeout extension or P08 release.'}
 target.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n');return review

def retained_timeout(primary):
 primary=Path(primary).resolve();path=primary/'retain-timeout-review.json'
 if not path.exists():return False
 r=json.loads(path.read_text())
 if (not eligible(primary) or r.get('classification')!='retain_original_episode_timeout'
     or r.get('original_attempt')!=str(primary) or r.get('continue_unstarted_only') is not True
     or r.get('technical_gate_resolved') is not False or r.get('additional_attempts_allowed')!=0
     or r.get('original_evidence')!=interruption_evidence(primary)
     or r.get('process_evidence_sha256')!=sha(Path(r['process_evidence']))):raise ValueError('Invalid or changed timeout retention evidence')
 return True
