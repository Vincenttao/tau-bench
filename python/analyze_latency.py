"""Offline latency diagnostics; never calls models or modifies benchmark evidence."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import statistics


def quantile(values, p):
    a=sorted(values)
    if not a:return None
    x=(len(a)-1)*p;i=int(x);j=min(i+1,len(a)-1)
    return a[i]+(a[j]-a[i])*(x-i)


def union_seconds(intervals):
    if not intervals:return 0.0
    ordered=sorted(intervals);a,b=ordered[0];total=0.0
    for c,d in ordered[1:]:
        if c<=b:b=max(b,d)
        else:total+=b-a;a,b=c,d
    return total+b-a


def description(values):
    return {'n':len(values),'sum':sum(values),'median':quantile(values,.5),
            'p95':quantile(values,.95),'max':max(values) if values else None}


def extract(folder):
    files=list(folder.glob('episodes/*/result.json'))
    if len(files)!=1:return None
    path=files[0];sim=json.loads(path.read_text())['simulations'][0]
    models=[];tools=[];responses=[];intervals=[];log_refs=[];stream_seconds=[]
    for log in folder.glob('episodes/*/java/*.stderr.log'):
        log_refs.append({'path':str(log),'sha256':hashlib.sha256(log.read_bytes()).hexdigest()})
        previous=None;offset=0
        for line_number,line in enumerate(log.read_text(errors='replace').splitlines(),1):
            t=re.match(r'(\d\d):(\d\d):(\d\d\.\d+)',line)
            if not t:continue
            seconds=int(t[1])*3600+int(t[2])*60+float(t[3])
            if previous is not None and previous-seconds>43200:offset+=86400
            previous=seconds;end=seconds+offset
            fields=dict(re.findall(r'\b([a-z_]+)=([^\s]+)',line))
            if fields.get('event')=='react_model_call_completed':
                ms=float(fields['model_duration_ms']);row={'duration_seconds':ms/1000,'line':line_number,
                    'log':str(log),'status':fields.get('status'),'end_clock_seconds':end}
                for key in ['prompt_tokens','completion_tokens','total_tokens']:
                    row[key]=int(fields[key]) if key in fields else None
                models.append(row);intervals.append((end-ms/1000,end))
            if fields.get('event')=='react_tool_call_completed' and 'duration_ms' in fields:
                tools.append({'name':fields.get('tool_name'),'duration_seconds':float(fields['duration_ms'])/1000,
                              'end_clock_seconds':end,'log':str(log),'line':line_number})
            if fields.get('event')=='react_model_response':
                responses.append({k:int(fields[k]) for k in ['content_length','reasoning_length','tool_call_count'] if k in fields})
            if 'OpenAI API stream end.' in line:
                m=re.search(r'durationMs=(\d+)',line)
                if m:stream_seconds.append(int(m[1])/1000)
    messages=sim['messages'];calls=[];kb_ids=[];kb_content_chars=0;queries=[];call_names={};kb_times=[]
    user_intervals=[];bridge=[];returned_models=Counter()
    for i,msg in enumerate(messages):
        for call in msg.get('tool_calls') or []:
            calls.append(call);call_names[call['id']]=call['name']
            if call['name']=='KB_search':queries.append(json.dumps(call.get('arguments'),sort_keys=True))
        if msg['role']=='tool' and (msg.get('name')=='KB_search' or call_names.get(msg.get('id'))=='KB_search'):
            c=str(msg.get('content') or '');kb_content_chars+=len(c)
            kb_ids.extend(re.findall(r'ID:\s*(doc_[^\s]+)',c))
            timing=re.search(r'\[Timing: retrieval=([\d.]+)ms, reranking=([\d.]+)ms, total=([\d.]+)ms\]',c)
            if timing:kb_times.append(float(timing[3]))
        if msg['role']=='assistant':
            latency=(msg.get('raw_data') or {}).get('latency_seconds')
            if latency is not None:bridge.append(latency)
        if msg['role']=='user':
            model=(msg.get('raw_data') or {}).get('model')
            if model:returned_models[model]+=1
            if i and msg.get('timestamp') and messages[i-1].get('timestamp'):
                gap=(datetime.fromisoformat(msg['timestamp'])-datetime.fromisoformat(messages[i-1]['timestamp'])).total_seconds()
                if gap>=0:user_intervals.append(gap)
    by_tool=defaultdict(list)
    for x in tools:by_tool[x['name']].append(x['duration_seconds'])
    durations=[x['duration_seconds'] for x in models];prompts=[x['prompt_tokens'] for x in models if x['prompt_tokens'] is not None]
    known_model_union=union_seconds(intervals)
    return {'attempt':folder.name,'task_id':sim['task_id'],'reward':(sim.get('reward_info') or {}).get('reward'),
            'duration_seconds':sim['duration'],'messages':len(messages),'termination_reason':sim.get('termination_reason'),
            'java_model_calls':len(models),'java_model_time':description(durations),'java_model_interval_union_seconds':known_model_union,
            'java_model_interval_union_fraction':known_model_union/sim['duration'] if sim['duration'] else None,
            'java_prompt_tokens':description(prompts),'first_java_prompt_tokens':prompts[0] if prompts else None,
            'last_java_prompt_tokens':prompts[-1] if prompts else None,
            'java_completion_tokens_sum':sum(x['completion_tokens'] or 0 for x in models),
            'tool_span_durations_by_name':{k:description(v) for k,v in by_tool.items()},
            'stream_iterator_seconds':description(stream_seconds),'java_bridge_yield_wait_seconds':description(bridge),
            'user_turn_interval_seconds':description(user_intervals),'user_returned_model_labels':dict(returned_models),
            'official_tool_counts':dict(Counter(c['name'] for c in calls)),
            'KB_query_count':len(queries),'KB_exact_repeated_query_count':len(queries)-len(set(queries)),
            'KB_document_occurrences':len(kb_ids),'KB_distinct_document_ids':len(set(kb_ids)),
            'KB_repeat_document_occurrences':len(kb_ids)-len(set(kb_ids)),
            'KB_response_characters':kb_content_chars,'model_calls':models,'response_length_metadata':responses,
            'KB_self_reported_total_ms':description(kb_times),
            'source_result':str(path),'source_result_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'log_evidence':log_refs}


def report(suite):
    rows=[x for f in sorted(suite.glob('P07-task_*-r00-a*')) if (x:=extract(f)) is not None]
    primary=[x for x in rows if x['attempt'].endswith('a00')]
    all_models=[m for x in primary for m in x['model_calls']]
    duration=sum(x['duration_seconds'] for x in primary)
    executions=[]
    for folder in sorted(suite.glob('P07-task_*-r00-a*')):
        journal=folder/'supervisor.jsonl'
        if not journal.exists():continue
        events=[]
        for line in journal.read_text().splitlines():
            try:events.append(json.loads(line))
            except json.JSONDecodeError:pass
        starts=[e['time'] for e in events if e.get('event')=='start']
        finishes=[e for e in events if e.get('event')=='finish']
        executions.append({'attempt':folder.name,'primary':folder.name.endswith('a00'),
            'start':starts[0] if starts else None,'finish':finishes[-1]['time'] if finishes else None,
            'supervised_elapsed_seconds':finishes[-1]['time']-starts[0] if starts and finishes else None,
            'terminal_status':finishes[-1].get('status') if finishes else None})
    primary_elapsed=[x['supervised_elapsed_seconds'] for x in executions if x['primary'] and x['supervised_elapsed_seconds'] is not None]
    result={'scope':'Completed scored P07 primary attempts; secondary attempts separate; missing/timeout/error trajectories excluded from scored timing denominator',
            'generated_at':datetime.now().isoformat(),'primary_completed_count':len(primary),
            'primary_duration':description([x['duration_seconds'] for x in primary]),
            'primary_java_model_call_count':len(all_models),
            'primary_java_model_time':description([m['duration_seconds'] for m in all_models]),
            'primary_java_model_union_seconds':sum(x['java_model_interval_union_seconds'] for x in primary),
            'primary_java_model_union_fraction':sum(x['java_model_interval_union_seconds'] for x in primary)/duration if duration else None,
            'primary_prompt_tokens':description([m['prompt_tokens'] for m in all_models if m['prompt_tokens'] is not None]),
            'primary_completion_tokens_sum':sum(x['java_completion_tokens_sum'] for x in primary),
            'primary_KB_count':sum(x['KB_query_count'] for x in primary),
            'primary_KB_document_occurrences':sum(x['KB_document_occurrences'] for x in primary),
            'primary_KB_repeat_document_occurrences_within_case':sum(x['KB_repeat_document_occurrences'] for x in primary),
            'primary_user_turn_interval_seconds':sum(x['user_turn_interval_seconds']['sum'] for x in primary),
            'primary_supervisor_elapsed':description(primary_elapsed),
            'execution_observations':executions,'rows':rows,
            'limitations':['Core model_duration includes model client/network/gateway/inference/stream consumption; not pure server compute.',
                'Tool spans may overlap each other or contain user waits; never add all span sums to claim wall time.',
                'User adjacent-message intervals include local orchestration and are not independently measured user-model request latency.',
                'No precise gateway queue time, server inference time, network RTT, TTFT or local CPU profile collected.',
                'Tokens are gateway-reported usage; repeated prompt volume is not unique text or billed uncached tokens.',
                'Latency/input correlations are observational; no A/B optimization or model-server benchmark was executed.']}
    out=suite/'single-round-latency-data.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--suite',type=Path,required=True);args=parser.parse_args()
    result=report(args.suite)
    print(json.dumps({k:v for k,v in result.items() if k not in ['rows','limitations','execution_observations']},ensure_ascii=False))
