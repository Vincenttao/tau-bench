'use strict';
const $ = id => document.getElementById(id);
const state = {runs: [], run: null, episode: null, bundle: null, stream: 'official', page: 0, version: 0, detailVersion: 0};
const names = {conversation:'对话',tool:'工具',skill:'Skill',mcp:'MCP',todo:'Todo',model:'模型',system:'系统'};
const icons = {conversation:'聊',tool:'↗',skill:'SK',mcp:'M',todo:'✓',model:'AI',system:'·'};
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const outcome = e => e.reward === null || e.reward === undefined ? 'unscored' : Number(e.reward) === 1 ? 'pass' : 'fail';
const label = e => ({pass:'官方通过',fail:'官方失败',unscored:'未评分'}[outcome(e)]);
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
  $('summary').innerHTML = metric('官方评分结果',label(e)) + metric('用例耗时',typeof e.duration === 'number' ? e.duration.toFixed(1) : '—','秒') + metric('Skill 事件',b.counts.skill || 0,'条') + metric('MCP 事件',b.events.filter(x => x.stream === 'mcp').length,'条');
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
  const version = ++state.version; state.page = 0; state.bundle = null; $('summary').innerHTML = ''; $('warnings').textContent = ''; $('warnings').className = ''; $('events').innerHTML = '<div class="empty">正在读取轨迹…</div>';
  $('title').textContent = state.episode.task_id;
  $('subtitle').textContent = `${state.run.name} · ${state.episode.status} · 终止原因 ${state.episode.termination_reason || '未记录'}`;
  drawCases();
  const hash = new URLSearchParams({run:state.run.id,episode:id}); history.replaceState(null,'',`#${hash}`);
  try {
    const data = await api(`/api/episode?${params()}`); if (version !== state.version) return;
    state.bundle = data;
    $('warnings').textContent = data.warnings.slice(0,6).join('；'); $('warnings').className = data.warnings.length?'warning':'';
    drawSummary(); drawEvents();
  } catch(e) {if (version === state.version) {showError(e.message); $('events').innerHTML='';}}
}
async function selectRun(id, episode) {
  state.run = state.runs.find(r => r.id === id); if (!state.run) return;
  $('run').value = id;
  $('run-meta').textContent = `${state.run.implementation || '未标注装配'} · ${state.run.model || '未记录模型'}`;
  $('case-search').value = ''; $('outcome').value = 'all';
  const selected = state.run.episodes.some(e => e.id === episode) ? episode : state.run.episodes[0]?.id;
  if (selected === undefined) {state.episode=null; state.bundle=null; $('title').textContent='此批次没有用例'; $('subtitle').textContent=''; $('summary').innerHTML=''; drawCases(); drawEvents(); return;}
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
refresh();
