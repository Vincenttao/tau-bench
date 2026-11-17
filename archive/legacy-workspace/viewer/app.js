'use strict';
const $ = id => document.getElementById(id);
const state = {runs: [], run: null, episode: null, bundle: null, stream: 'official', page: 0, version: 0, detailVersion: 0, inspectTab: 'grading'};
const names = {conversation:'对话',tool:'工具',skill:'Skill',mcp:'MCP',todo:'Todo',model:'模型',system:'系统'};
const icons = {conversation:'聊',tool:'↗',skill:'SK',mcp:'M',todo:'✓',model:'AI',system:'·'};
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const outcome = e => e.verdict || 'unscored';
const label = e => ({pass:'官方通过',fail:'官方失败',unscored:'未评分',review:'待核查'}[outcome(e)]);
async function api(path) {const r = await fetch(path); const data = await r.json(); if (!r.ok) throw new Error(data.error || '读取失败'); return data;}
function params() {return new URLSearchParams({run:state.run.id,episode:state.episode.id});}
function showError(message) {$('warnings').textContent = message; $('warnings').className = 'warning';}
function drawCases() {
  if (!state.run) return;
  const q = $('case-search').value.toLowerCase(), result = $('outcome').value;
  const items = state.run.episodes.filter(e => e.task_id.toLowerCase().includes(q) && (result === 'all' || outcome(e) === result));
  $('case-count').textContent = `${items.length} / ${state.run.episodes.length}`;
  $('cases').innerHTML = items.map(e => `<button class="case ${state.episode?.id === e.id ? 'selected' : ''}" data-episode="${esc(e.id)}"><span><b>${esc(e.task_id)}</b><small>Trial ${esc(e.trial ?? '—')} · ${esc(e.status)}</small></span><span class="badge ${outcome(e)}">${label(e)}</span></button>`).join('') || '<div class="muted">没有匹配用例</div>';
}
function metric(title,value,unit='') {return `<div class="metric"><span class="label">${title}</span><strong>${esc(value)}<small>${unit}</small></strong></div>`;}
function drawSummary() {
  const e = state.episode, b = state.bundle;
  if (!e || !b) return;
  $('summary').innerHTML = metric('官方评分结果',({pass:'官方通过',fail:'官方失败',unscored:'未评分',review:'待核查'}[b.inspection?.grading.verdict]) || label(e)) + metric('用例耗时',typeof e.duration === 'number' ? e.duration.toFixed(1) : '—','秒') + metric('Skill 事件',b.counts.skill || 0,'条') + metric('MCP 事件',b.events.filter(x => x.stream === 'mcp').length,'条');
}
function drawEvents() {
  const query = $('event-search').value.toLowerCase(), category = $('category').value;
  const all = (state.bundle?.events || []).filter(e => e.stream === state.stream && (category === 'all' || category === e.category) && (!$('errors').checked || e.error) && `${e.title} ${e.preview} ${e.call_id || ''} ${e.source}`.toLowerCase().includes(query));
  const pages = Math.max(1,Math.ceil(all.length/40)); state.page = Math.min(state.page,pages-1);
  $('event-count').textContent = `${all.length} 条匹配记录 · 搜索标题及内容摘要`;
  $('events').innerHTML = all.slice(state.page*40,(state.page+1)*40).map(e => `<article class="event ${e.error?'error':''}" data-kind="${esc(e.category)}"><div class="avatar">${icons[e.category] || '·'}</div><div><div class="event-head"><strong>${esc(e.title)}</strong><span class="badge">${names[e.category]}</span>${e.error?'<span class="badge fail">错误标记</span>':''}<time>${esc(e.time || '未记录时间')}</time></div><p>${esc(e.preview)}</p><div class="event-bottom"><span class="source">${esc(e.source)} · ${esc(e.locator)}${e.call_id?' · ID '+esc(e.call_id):''}</span><button data-detail="${esc(e.id)}">查看完整记录 ↗</button></div></div></article>`).join('') || '<div class="empty">暂无匹配记录<br>可以切换来源、类别或清除筛选条件。未记录不代表未执行。</div>';
  $('page').textContent = `${state.page+1} / ${pages}`; $('previous').disabled = state.page===0; $('next').disabled = state.page===pages-1;
}
async function selectEpisode(id) {
  state.episode = state.run.episodes.find(e => e.id === id); if (!state.episode) return;
  const version = ++state.version; state.page = 0; state.bundle = null; $('summary').innerHTML = ''; $('inspection-body').textContent='正在读取说明…'; $('round-verdict').textContent=''; $('warnings').textContent = ''; $('warnings').className = ''; $('events').innerHTML = '<div class="empty">正在读取轨迹…</div>';
  $('title').textContent = state.episode.task_id;
  $('subtitle').textContent = `${state.run.name} · ${state.episode.status} · 终止原因 ${state.episode.termination_reason || '未记录'}`;
  drawCases();
  const hash = new URLSearchParams({run:state.run.id,episode:id}); history.replaceState(null,'',`#${hash}`);
  try {
    const data = await api(`/api/episode?${params()}`); if (version !== state.version) return;
    state.bundle = data;
    $('warnings').textContent = data.warnings.slice(0,6).join('；'); $('warnings').className = data.warnings.length?'warning':'';
    drawSummary(); drawInspection(); drawEvents();
  } catch(e) {if (version === state.version) {showError(e.message); $('events').innerHTML='';}}
}
async function selectRun(id, episode) {
  state.run = state.runs.find(r => r.id === id); if (!state.run) return;
  $('run').value = id;
  $('run-meta').textContent = `${state.run.implementation || '未标注装配'} · ${state.run.model || '未记录模型'}`;
  $('case-search').value = ''; $('outcome').value = 'all';
  const selected = state.run.episodes.some(e => e.id === episode) ? episode : state.run.episodes[0]?.id;
  if (selected === undefined) {state.episode=null; state.bundle=null; $('title').textContent='此批次没有用例'; $('subtitle').textContent=''; $('summary').innerHTML=''; $('inspection-body').textContent='没有用例记录'; $('round-verdict').textContent=''; drawCases(); drawEvents(); return;}
  await selectEpisode(selected);
}
async function refresh() {
  $('refresh').disabled=true;
  try {
    const data = await api('/api/runs'); state.runs = data.runs;
    $('run').innerHTML = data.runs.map(r=>`<option value="${esc(r.id)}">${esc(r.name)} (${r.episodes.length})</option>`).join('');
    if (!data.runs.length) {showError('未找到本地实验 manifest。请确认 experiments/*/runs/*/manifest.json 存在。'); return;}
    const hash = new URLSearchParams(location.hash.slice(1));
    const preferred = state.run?.id || hash.get('run');
    const run = data.runs.find(r=>r.id === preferred) || data.runs.find(r=>r.name === 'round-01-20261115-a00') || data.runs.at(-1);
    await selectRun(run.id,state.episode?.id || hash.get('episode') || undefined);
  } catch(e) {showError(e.message);} finally {$('refresh').disabled=false;}
}
$('run').onchange = () => selectRun($('run').value);
$('cases').onclick = e => {const b=e.target.closest('[data-episode]');if(b)selectEpisode(b.dataset.episode);};
for (const id of ['case-search','outcome']) $(id).addEventListener('input',drawCases);
for (const id of ['event-search','category','errors']) $(id).addEventListener('input',()=>{state.page=0;drawEvents();});
document.querySelectorAll('[data-stream]').forEach(button=>button.onclick=()=>{state.stream=button.dataset.stream;state.page=0;$('category').value='all';document.querySelectorAll('[data-stream]').forEach(b=>b.classList.toggle('active',b===button));drawEvents();});
$('previous').onclick=()=>{state.page--;drawEvents();};$('next').onclick=()=>{state.page++;drawEvents();};$('refresh').onclick=refresh;
$('events').onclick=async e=>{const button=e.target.closest('[data-detail]');if(!button)return;const item=state.bundle.events.find(x=>x.id===button.dataset.detail);const version=++state.detailVersion;const q=params();q.set('event',item.id);$('detail-title').textContent=item.title;$('detail-source').textContent=`${item.source} · ${item.locator}`;$('detail-body').textContent='正在读取完整记录…';$('copy-status').textContent='';$('copy').disabled=true;$('detail').showModal();try {const raw=await api(`/api/event?${q}`);if(version!==state.detailVersion)return;$('detail-body').textContent=JSON.stringify(raw,null,2);$('copy').disabled=false;}catch(error){if(version===state.detailVersion)$('detail-body').textContent=error.message;}};
$('close').onclick=()=>{$('detail').close();state.detailVersion++;};
$('copy').onclick=async()=>{try{await navigator.clipboard.writeText($('detail-body').textContent);$('copy-status').textContent='已复制';}catch{$('copy-status').textContent='复制失败，请选择文本手动复制';}};
document.querySelectorAll('[data-inspect]').forEach(button=>button.onclick=()=>{
  state.inspectTab=button.dataset.inspect;
  document.querySelectorAll('[data-inspect]').forEach(b=>b.classList.toggle('active',b===button));
  drawInspection();
});
$('inspection-body').addEventListener('input',e=>{
  if(e.target.id!=='capability-search')return;
  const query=e.target.value.toLowerCase();
  document.querySelectorAll('.capability').forEach(row=>row.hidden=!row.textContent.toLowerCase().includes(query));
});
refresh();

function jsonBlock(value) {return `<pre>${esc(JSON.stringify(value,null,2))}</pre>`;}
function sourceLine(value) {return `<p class="source">来源：${esc(value || '未记录')}</p>`;}
function drawInspection() {
  const info=state.bundle?.inspection;
  if(!info)return;
  const round=state.run.assessment, g=info.grading;
  const decision={pass:'本轮全部通过',fail:'本轮存在失败',pending:'本轮待完成 / 待核查'};
  $('round-verdict').innerHTML=`<div class="round-line"><strong>${esc(decision[round.decision])}</strong><span>计划 ${round.total} · 通过 ${round.pass} · 失败 ${round.fail} · 未评分 ${round.unscored} · 待核查 ${round.review}</span><span>已评分通过率 ${round.pass_rate_scored===null?'—':(round.pass_rate_scored*100).toFixed(1)+'%'}</span></div><p class="muted">${esc(round.rule)}</p>`;
  if(state.inspectTab==='grading') {
    const current={pass:'官方通过',fail:'官方失败',unscored:'未评分',review:'待核查'}[g.verdict];
    const rules=`<div class="rule-grid"><div><b>什么时候成功？</b><p>单题状态为 scored，且官方 reward = 1。</p></div><div><b>什么时候失败？</b><p>单题状态为 scored，且 0 ≤ reward &lt; 1。具体以本题参与计分的检查为准。</p></div><div><b>什么时候不能下结论？</b><p>没有有效评分则未评分；状态、分数冲突或分数无效则待核查。异常未评分不补记为 0。</p></div></div>`;
    const basis=g.basis.map(b=>`<div class="basis"><b>${esc(b.name)}</b><span>${esc(b.description)}</span></div>`).join('') || '<p class="muted">未读取到本题 reward_basis，不能推断检查项。</p>';
    const checks=g.checks.length?`<div class="table-wrap"><table><thead><tr><th>评分分项</th><th>实际得分</th><th>是否参与本题计分</th></tr></thead><tbody>${g.checks.map(c=>`<tr><td>${esc(c.name)}</td><td>${esc(c.value)}</td><td>${c.participates?'参与':'仅诊断 / 未声明'}</td></tr>`).join('')}</tbody></table></div>`:'<p class="muted">没有分项评分记录；页面不执行重新评分。</p>';
    $('inspection-body').innerHTML=rules+`<div class="case-verdict"><strong>当前用例：${current}</strong><span>reward ${esc(g.reward ?? '未记录')} · 状态 ${esc(g.status)} · 终止原因 ${esc(g.termination_reason || '未记录')}</span></div>`+
      g.conflicts.map(c=>`<p class="warning">${esc(c)}</p>`).join('')+`<h3>本题计分依据</h3>${basis}${checks}<p class="muted">${esc(info.rules.components)}</p><p class="muted">${esc(info.rules.errors)}</p>`+
      `<details><summary>查看实际检查结果（数据库、动作、交流与断言）</summary>${sourceLine(g.reward_source)}${jsonBlock(g.reward_info)}</details>`+
      `<details><summary>查看预期动作与判定条件 · 裁判侧信息</summary><p class="muted">${esc(g.note)}</p>${sourceLine(g.criteria_source)}${jsonBlock(g.criteria)}</details>`+
      `<details><summary>查看用户模拟器剧本及用户侧工具</summary><p class="muted">以下是模拟器配置，不代表 Agent 收到的开场消息；对话请查看下方轨迹。</p>${sourceLine(g.criteria_source)}${jsonBlock({scenario:g.scenario,user_tools:g.user_tools})}</details>`+sourceLine(g.status_source);
  } else if(state.inspectTab==='skills') {
    $('inspection-body').innerHTML=(info.skill_releases?.length ? info.skill_releases.map(v=>`<p class="release-info"><b>Skill 版本 ${esc(v.identity.version)}</b> · 发布清单 SHA-256 <span class="source">${esc(v.identity.release_sha256)}</span></p>${sourceLine(v.source.path+' · '+v.source.locator)}`).join('') : '<p class="muted">历史记录未声明显式版本；以下按部署原件展示。</p>')+`<p class="muted">说明来自当前用例的部署快照，保留会话来源。部署、请求读取和读取成功是不同证据；下面的读取计数为请求事件数。</p>`+
      (info.skills.map(s=>`<details class="skill-card"><summary><b>${esc(s.name)}</b><span class="muted">部署快照 · 展开完整文档</span><span class="skill-description">${esc(s.description || '文档未提供 description')}</span></summary>${sourceLine(s.source)}<p class="source">SHA-256 ${esc(s.sha256)}</p><pre>${esc(s.content)}</pre>${(s.guides || []).map(g=>`<details><summary>业务指南：${esc(g.name)}</summary>${sourceLine(g.source)}<p class="source">SHA-256 ${esc(g.sha256)}</p><pre>${esc(g.content)}</pre></details>`).join('')}</details>`).join('') || '<p class="muted">未找到该用例的部署 Skill 快照。不使用当前源码文档代替历史快照。</p>')+
      `<h3>实际 Skill 文档读取请求 · ${info.skill_reads.length} 条</h3>`+
      (info.skill_reads.map(r=>`<details><summary>${esc(r.arguments.skill_name || r.arguments.skill_id || '未指定 Skill')} / ${esc(r.arguments.relative_path || 'SKILL.md')}<span class="muted">${esc(r.source.locator)}</span></summary>${jsonBlock(r.arguments)}${sourceLine(r.source.path+' · '+r.source.locator)}<p class="muted">读取结果请在“Agent 内部事件”查看对应返回记录；此请求本身不证明读取成功。</p></details>`).join('') || '<p class="muted">没有观测到 skill_tool 开始事件；这不证明文档未通过其他方式注入。</p>');
  } else {
    const rows=(items,type)=>items.map(t=>`<details class="capability"><summary><b>${esc(t.name)}</b><span class="muted">${type==='agent'?'原生 tool_start 事件 '+t.tool_start_events+' 条':'部署于 '+esc(t.skill)+' · 已观测 MCP 记录 '+t.observed_mcp_records+' 条'}</span></summary><p>${esc(t.description || '未提供描述')}</p><h4>调用参数 Schema</h4>${jsonBlock(t.parameters)}${sourceLine(typeof t.source==='string'?t.source:t.source.path+' · '+t.source.locator)}</details>`).join('');
    $('inspection-body').innerHTML=`<div class="cap-search"><label for="capability-search">搜索工具名称、说明或参数</label><input id="capability-search" type="search" placeholder="例如 KB_search、invoke_skill、query…"></div><p class="muted">${esc(info.mcp.note)} 相同工具有多份定义时，分别保留来源。</p><h3>MCP 实际方法记录</h3>${jsonBlock(info.mcp.methods)}${info.mcp.sources.map(sourceLine).join('')}<h3>Agent 可调用原生工具 · ${info.agent_tools.length} 份定义</h3><p class="muted">来自 model_request.tools，表示模型请求中实际提供的工具。事件次数包含恢复回调，不代表独立业务调用次数。</p>${rows(info.agent_tools,'agent') || '<p class="muted">没有记录模型请求工具定义。</p>'}<h3>Skill 可调用业务操作 · ${info.operations.length} 份定义</h3><p class="muted">来自部署 operations.json。0 条已观测 MCP 记录表示未记录调用，不代表该工具不可用。</p>${rows(info.operations,'operation') || '<p class="muted">没有部署操作目录。</p>'}<details><summary>查看 MCP 已调用工具及记录数</summary>${jsonBlock(info.mcp.tools)}</details>`;
  }
}
