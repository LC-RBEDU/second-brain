/** One distinct color per slot in proj_order (~13 projects). */
const PROJECT_PALETTE = [
  '#e57373',
  '#64b5f6',
  '#4db6ac',
  '#81c784',
  '#ffb74d',
  '#ba68c8',
  '#f06292',
  '#4dd0e1',
  '#aed581',
  '#ff8a65',
  '#9575cd',
  '#dce775',
  '#90a4ae',
];

function projectColor(slug, index) {
  if (typeof index === 'number' && index >= 0 && index < PROJECT_PALETTE.length) {
    return PROJECT_PALETTE[index];
  }
  let h = 0;
  for (let i = 0; i < slug.length; i++) h = (h * 31 + slug.charCodeAt(i)) | 0;
  return PROJECT_PALETTE[Math.abs(h) % PROJECT_PALETTE.length];
}

/** Mirrors cron/build_dashboard.py project_prefix — fallback when displayId not in JSON. */
function projectPrefix(name) {
  const parts = [];
  for (const word of (name || '').split(/\s+/).slice(0, 3)) {
    const w = word.trim();
    if (w) parts.push(w[0].toUpperCase());
  }
  return parts.join('');
}

function taskIdSuffix(taskId) {
  if (!taskId) return '';
  const suffix = String(taskId).replace(/^[A-Za-z]+/, '');
  return suffix || String(taskId);
}

function taskDisplayId(t, data) {
  return t.displayId || t.id || '';
}

function resolveTaskColor(t, data) {
  if (t.projColor) return t.projColor;
  const order = data?.proj_order || [];
  const index = order.indexOf(t.proj);
  return projectColor(t.proj, index >= 0 ? index : undefined);
}

function taskProjectStyle(t, data) {
  return {
    displayId: taskDisplayId(t, data),
    projColor: resolveTaskColor(t, data),
  };
}

function applyTaskProjectEl(el, t, data) {
  const { projColor } = taskProjectStyle(t, data);
  if (projColor) {
    el.style.setProperty('--task-proj-color', projColor);
    el.style.borderLeftColor = projColor;
  }
}

async function loadData() {
  if (window.__DASHBOARD_DATA__) return window.__DASHBOARD_DATA__;
  const res = await fetch('dashboard-data.json?' + Date.now());
  if (!res.ok) throw new Error('dashboard-data.json missing — spusť build_dashboard.py');
  return res.json();
}

function esc(s) {
  const d = document.createElement('div');
  d.textContent = s ?? '';
  return d.innerHTML;
}

function iceScore(t) {
  const ice = t?.ice;
  if (!ice) return null;
  const i = ice.i ?? 5;
  const c = ice.c ?? 5;
  const e = Math.max(ice.e ?? 5, 1);
  return (i * c) / e;
}

function iceBadgeHtml(t) {
  const score = iceScore(t);
  if (score == null) return '';
  return `<span class="ice-badge" title="ICE">${score.toFixed(1)}</span>`;
}

function urgencyPillHtml(t) {
  const p = t?.p;
  if (!p) return '';
  const cls = { ASAP: 'asap', Next: 'next', Backlog: 'backlog', Waiting: 'waiting' }[p] || p.toLowerCase();
  return `<span class="urgency-pill ${cls}">${esc(p)}</span>`;
}

function formatWaitUntilBadge(iso) {
  if (!iso) return '';
  const d = new Date(String(iso).slice(0, 10) + 'T12:00:00');
  if (Number.isNaN(d.getTime())) return '';
  const label = d.toLocaleDateString('cs-CZ', { day: 'numeric', month: 'numeric' });
  return `<span class="wait-until-badge" title="Čekat do">${esc('do ' + label)}</span>`;
}

function taskTitleHtml(displayId, t) {
  return `<span class="task-title-meta">
    <strong class="task-id">${esc(displayId)}</strong>
  </span>
  <span class="task-name">${esc(t.name)}</span>`;
}

function taskSummaryBadgesHtml(t, progress) {
  const parts = [urgencyPillHtml(t), iceBadgeHtml(t)];
  if (t?.p === 'Waiting' && t.waitUntil) {
    parts.push(formatWaitUntilBadge(t.waitUntil));
  }
  if (progress) {
    parts.push(`<span class="ch-badge" title="hotovo / celkem">${esc(progress)}</span>`);
  }
  const inner = parts.filter(Boolean).join('');
  return inner ? `<span class="task-summary-badges">${inner}</span>` : '';
}

function subtaskProgress(ch) {
  if (!ch?.length) return null;
  const done = ch.filter((c) => c.d).length;
  return `${done}/${ch.length}`;
}

function isSafeHttpUrl(url) {
  try {
    const u = new URL(url);
    return u.protocol === 'http:' || u.protocol === 'https:';
  } catch {
    return false;
  }
}

function firstUrlInText(text) {
  const m = String(text || '').match(/https?:\/\/[^\s)>\]]+/);
  return m ? m[0] : null;
}

function subtaskLinkLabel(text, url) {
  let label = String(text || '')
    .replace(url, '')
    .replace(/^↗\s*/, '')
    .replace(/:\s*$/, '')
    .trim();
  if (!label) label = 'Odkaz';
  return label;
}

function subtaskBodyHtml(c) {
  const url = c.url || firstUrlInText(c.t);
  if (url && isSafeHttpUrl(url)) {
    const label = subtaskLinkLabel(c.t, url);
    return `<a class="subtask-link" href="${esc(url)}" target="_blank" rel="noopener">${esc(label)}</a>`;
  }
  return esc(c.t);
}

function renderTaskSourceLink(t) {
  const url = t.sourceUrl;
  if (!url || !isSafeHttpUrl(url)) return '';
  const label = t.sourceLabel || 'Sembly nahrávka';
  return `<p class="task-source"><a class="subtask-link" href="${esc(url)}" target="_blank" rel="noopener">${esc(label)}</a></p>`;
}

function isSourceOnlySubtask(c) {
  if (c.source) return true;
  const t = (c.t || '').trim();
  if (t.startsWith('↗')) return true;
  const url = c.url || firstUrlInText(t);
  if (url) {
    const bare = t.replace(url, '').replace(/^↗\s*/, '').replace(/:\s*$/, '').trim();
    if (bare.length < 4) return true;
  }
  return false;
}

function renderSubtasks(ch) {
  if (!ch?.length) return '';
  let n = 0;
  const items = ch
    .map((c) => {
      const isSource = isSourceOnlySubtask(c);
      const num = c.n != null && !isSource ? c.n : isSource ? null : ++n;
      const numHtml = num != null ? `<span class="subtask-num">${num}.</span>` : '';
      const cls = 'subtask' + (c.d ? ' done' : '') + (isSource ? ' subtask-source-line' : '');
      return `<li class="${cls}"><span class="chk">${c.d ? '✓' : '○'}</span>${numHtml}${subtaskBodyHtml(c)}</li>`;
    })
    .join('');
  return `<ul class="subtasks">${items}</ul>`;
}

function taskOpenKey(t) {
  const proj = t?.proj || '';
  const id = t?.id || '';
  return `task:${proj}:${id}`;
}

const OPEN_STATE_KEY = 'mrluc-dashboard-open';

function captureOpenState() {
  const keys = [];
  document.querySelectorAll('details[open]').forEach((el) => {
    const k = el.dataset.openKey || el.id;
    if (k) keys.push(k);
  });
  return keys;
}

function restoreOpenState(keys) {
  if (!keys?.length) return;
  const set = new Set(keys);
  document.querySelectorAll('details').forEach((el) => {
    const k = el.dataset.openKey || el.id;
    if (k && set.has(k)) el.open = true;
  });
}

function persistOpenState() {
  try {
    sessionStorage.setItem(OPEN_STATE_KEY, JSON.stringify(captureOpenState()));
  } catch {
    /* private mode / quota */
  }
}

function loadPersistedOpenState() {
  try {
    const raw = sessionStorage.getItem(OPEN_STATE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function bindOpenStatePersistence() {
  if (window.__DASHBOARD_OPEN_BOUND__) return;
  window.__DASHBOARD_OPEN_BOUND__ = true;
  document.addEventListener(
    'toggle',
    (e) => {
      if (e.target instanceof HTMLDetailsElement) persistOpenState();
    },
    true
  );
}

/** Task row: expandable when checklist (ch) exists */
function renderTaskRow(t, opts = {}) {
  const progress = subtaskProgress(t.ch);
  const hasCh = Boolean(t.ch?.length);
  const metaHtml = opts.showMeta && t.dl ? `<div class="task-meta">${esc(t.dl)}</div>` : '';
  const displayId = opts.displayId ?? t.displayId ?? t.id;
  const openKey = taskOpenKey(t);

  if (hasCh) {
    return `<details class="task-details" data-open-key="${esc(openKey)}">
      <summary class="task-summary">
        <span class="task-title">${taskTitleHtml(displayId, t)}</span>
        ${taskSummaryBadgesHtml(t, progress)}
      </summary>
      ${renderSubtasks(t.ch)}
      ${renderTaskSourceLink(t)}
      ${metaHtml}
    </details>`;
  }

  return `<div class="task-flat">
    <span class="task-title">${taskTitleHtml(displayId, t)}</span>
    ${taskSummaryBadgesHtml(t, null)}
    ${metaHtml}
  </div>`;
}

function renderTop(data) {
  const el = document.getElementById('top-priority-list');
  el.innerHTML = '';
  (data.topPriority || []).forEach((t) => {
    const div = document.createElement('div');
    div.className = 'card' + (t.p === 'ASAP' ? ' asap' : '');
    const proj = data.projects?.[t.proj]?.name || t.proj;
    const progress = subtaskProgress(t.ch);
    const { displayId } = taskProjectStyle(t, data);
    applyTaskProjectEl(div, t, data);
    const body = renderTaskRow(t, { showMeta: false, displayId });
    div.innerHTML = `${body}
      <div class="proj">${esc(proj)} · ${esc(t.p)}${t.dl ? ' · ' + esc(t.dl) : ''}${
      progress ? ' · checklist ' + esc(progress) : ''
    }</div>`;
    el.appendChild(div);
  });
}

function renderColumnBlock(root, key, list, data, extraClass = '') {
  const col = document.createElement('details');
  col.className = 'col-details col ' + key.toLowerCase() + (extraClass ? ' ' + extraClass : '');
  col.dataset.openKey = 'col:' + key;
  const summary = document.createElement('summary');
  summary.className = 'col-summary';
  summary.textContent = `${key} (${list.length})`;
  col.appendChild(summary);
  const wrap = document.createElement('div');
  wrap.className = 'task-list';
  list.forEach((t) => {
    const item = document.createElement('div');
    item.className = 'task-item';
    const { displayId } = taskProjectStyle(t, data);
    applyTaskProjectEl(item, t, data);
    item.innerHTML = renderTaskRow(t, { showMeta: true, displayId });
    wrap.appendChild(item);
  });
  col.appendChild(wrap);
  root.appendChild(col);
}

function renderColumns(data) {
  const root = document.getElementById('task-columns');
  const cols = { ASAP: [], Next: [], Backlog: [] };
  (data.tasks || []).forEach((t) => {
    if (t.st === 'dn') return;
    const p = t.p || 'Backlog';
    if (p === 'Waiting') return;
    if (!cols[p]) cols[p] = [];
    cols[p].push(t);
  });
  root.innerHTML = '';
  const waitingList = data.waiting || [];
  if (waitingList.length) {
    renderColumnBlock(root, 'Waiting', waitingList, data, 'waiting-col');
  }
  for (const [key, list] of Object.entries(cols)) {
    renderColumnBlock(root, key, list, data);
  }
}

function renderByProject(data) {
  const root = document.getElementById('by-project');
  const order = data.proj_order || [];
  const waitingIds = new Set((data.waiting || []).map((t) => `${t.proj}:${t.id}`));
  root.innerHTML = '';
  order.forEach((slug, index) => {
    const tasks = (data.tasks || []).filter((t) => {
      if (t.proj !== slug || t.st === 'dn') return false;
      if (t.p === 'Waiting' && !waitingIds.has(`${t.proj}:${t.id}`)) return false;
      return true;
    });
    if (!tasks.length) return;
    const name = data.projects?.[slug]?.name || slug;
    const color = projectColor(slug, index);
    const withCh = tasks.filter((t) => t.ch?.length).length;

    const block = document.createElement('details');
    block.className = 'proj-details';
    block.dataset.openKey = 'proj:' + slug;
    block.innerHTML = `<summary class="proj-summary" style="--proj-color:${color}">
      <span class="proj-name">${esc(name)}</span>
      <span class="proj-count">${tasks.length} úkolů${withCh ? ` · ${withCh} s checklistem` : ''}</span>
    </summary>`;

    const inner = document.createElement('div');
    inner.className = 'proj-tasks';
    tasks.forEach((t) => {
      const row = document.createElement('div');
      row.className = 'task-item';
      const { displayId } = taskProjectStyle(t, data);
      applyTaskProjectEl(row, t, data);
      row.innerHTML = renderTaskRow(t, { showMeta: true, displayId });
      inner.appendChild(row);
    });
    block.appendChild(inner);
    root.appendChild(block);
  });
}

function pragueYmd(d = new Date()) {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Europe/Prague',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(d);
}

function pragueTomorrowYmd() {
  const today = pragueYmd();
  for (let h = 1; h <= 48; h += 1) {
    const ymd = pragueYmd(new Date(Date.now() + h * 3600000));
    if (ymd > today) return ymd;
  }
  return today;
}

function isCalendarDayAllowed(ymd) {
  if (!ymd || ymd.length < 10) return false;
  const day = ymd.slice(0, 10);
  return day === pragueYmd() || day === pragueTomorrowYmd();
}

function formatEventTime(ev) {
  if (ev.allDay) {
    const d = (ev.start || '').slice(0, 10);
    return d ? new Date(d + 'T12:00:00').toLocaleDateString('cs-CZ', { weekday: 'short', day: 'numeric', month: 'numeric' }) + ' (celý den)' : '';
  }
  const start = ev.start ? new Date(ev.start) : null;
  const end = ev.end ? new Date(ev.end) : null;
  if (!start || Number.isNaN(start.getTime())) return '';
  const t0 = start.toLocaleTimeString('cs-CZ', { hour: '2-digit', minute: '2-digit' });
  if (!end || Number.isNaN(end.getTime())) return t0;
  const t1 = end.toLocaleTimeString('cs-CZ', { hour: '2-digit', minute: '2-digit' });
  return `${t0}–${t1}`;
}

function renderCalendar(data) {
  const el = document.getElementById('calendar-root');
  if (!el) return;
  const cal = data.calendar || {};
  const events = (cal.events || []).filter((ev) => isCalendarDayAllowed((ev.start || '').slice(0, 10)));
  if (!events.length) {
    const err = cal.fetchError ? ` (${cal.fetchError})` : '';
    el.innerHTML = `<p class="hint">Kalendář prázdný nebo není nastaven SA${esc(err)}. Viz config.example.env.</p>`;
    return;
  }
  const byDay = {};
  events.forEach((ev) => {
    const key = (ev.start || '').slice(0, 10) || '?';
    if (!byDay[key]) byDay[key] = [];
    byDay[key].push(ev);
  });
  const days = Object.keys(byDay).filter(isCalendarDayAllowed).sort();
  let html = '';
  if (cal.source && cal.source !== 'google_api') {
    html += `<p class="hint cal-meta">Zdroj: ${esc(cal.source)}${cal.fetchError ? ' — ' + esc(cal.fetchError) : ''}</p>`;
  }
  days.forEach((day) => {
    const label = new Date(day + 'T12:00:00').toLocaleDateString('cs-CZ', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
    });
    html += `<div class="cal-day"><h4 class="cal-day-title">${esc(label)}</h4><ul class="cal-events">`;
    byDay[day].forEach((ev) => {
      const time = formatEventTime(ev);
      const loc = ev.location ? `<span class="cal-loc">${esc(ev.location)}</span>` : '';
      const link = ev.htmlLink
        ? ` <a class="cal-link" href="${esc(ev.htmlLink)}" target="_blank" rel="noopener">↗</a>`
        : '';
      html += `<li class="cal-event"><span class="cal-time">${esc(time)}</span> <span class="cal-title">${esc(ev.title)}</span>${loc}${link}</li>`;
    });
    html += '</ul></div>';
  });
  el.innerHTML = html;
}

function renderInboxBadge(data) {
  const count = data.inboxCount ?? 0;
  const label = `INBOX: ${count}`;
  if (count <= 0) {
    const span = document.createElement('span');
    span.className = 'badge';
    span.id = 'badge-inbox';
    span.textContent = label;
    return span;
  }
  const details = document.createElement('details');
  details.className = 'badge-details';
  details.id = 'badge-inbox';
  const summary = document.createElement('summary');
  summary.className = 'badge';
  summary.textContent = label;
  details.appendChild(summary);
  const list = document.createElement('ul');
  list.className = 'badge-list';
  (data.inboxItems || []).forEach((item) => {
    const li = document.createElement('li');
    const title = item.title || item.filename;
    li.innerHTML = `<span class="badge-item-title">${esc(title)}</span><span class="badge-item-path">${esc(item.path)}</span>`;
    list.appendChild(li);
  });
  details.appendChild(list);
  return details;
}

function renderPendingBadge(data) {
  const count = data.pendingCount ?? 0;
  const label = `Ke schválení: ${count}`;
  if (count <= 0) {
    const span = document.createElement('span');
    span.className = 'badge badge-warn';
    span.id = 'badge-pending';
    span.textContent = label;
    return span;
  }
  const details = document.createElement('details');
  details.className = 'badge-details badge-details-warn';
  details.id = 'badge-pending';
  const summary = document.createElement('summary');
  summary.className = 'badge badge-warn';
  summary.textContent = label;
  details.appendChild(summary);
  const list = document.createElement('ul');
  list.className = 'badge-list';
  (data.pendingItems || []).forEach((item) => {
    const li = document.createElement('li');
    const parts = [item.batchId || item.filename];
    if (item.label) parts.push(item.label);
    else if (item.proposalCount) parts.push(`${item.proposalCount} návrhů`);
    li.innerHTML = `<span class="badge-item-title">${esc(parts.join(' — '))}</span><span class="badge-item-path">${esc(item.filename)}</span>`;
    list.appendChild(li);
  });
  details.appendChild(list);
  return details;
}

function renderBadges(data) {
  const root = document.querySelector('.badges');
  if (!root) return;
  root.replaceChildren(renderInboxBadge(data), renderPendingBadge(data));
}

function formatEduItem(item) {
  if (typeof item === 'string') return `<li>${esc(item)}</li>`;
  const title = esc(item.title || '—');
  const one = item.oneLiner ? `<span class="edu-oneliner">${esc(item.oneLiner)}</span>` : '';
  const metaParts = [];
  if (item.proj) metaParts.push(esc(item.proj));
  if (item.taskId) metaParts.push(esc(item.taskId));
  const meta = metaParts.length ? `<span class="edu-meta">${metaParts.join(' · ')}</span>` : '';
  return `<li class="edu-item"><strong>${title}</strong>${one ? ' — ' + one : ''}${meta}</li>`;
}

function renderEdu(data) {
  const el = document.getElementById('edu-news');
  const items = data.eduNews || [];
  if (!items.length) {
    el.innerHTML = '<p class="hint">OPS2 — žádná témata. Cron <code>edu_news_refresh.py</code> nebo po natočení videa <code>--clear</code>.</p>';
    return;
  }
  const updated = data.eduNewsUpdated ? `<p class="hint edu-updated">Témata: ${esc(data.eduNewsUpdated)}</p>` : '';
  el.innerHTML = updated + '<ul class="edu-list">' + items.map(formatEduItem).join('') + '</ul>';
}

const LIVE_POLL_MS = (() => {
  const sec = parseInt(window.DASHBOARD_POLL_SEC || '10', 10);
  return Number.isFinite(sec) && sec > 0 ? sec * 1000 : 10000;
})();

let lastSeenGenerated = null;

function renderAll(data, opts = {}) {
  const openKeys = opts.preserveOpen ? captureOpenState() : [];
  const meta = document.getElementById('meta-updated');
  if (meta) {
    let text = 'Aktualizováno: ' + (data.generated || data.updated || '—');
    if (data.waitingExpiredCount > 0) {
      text += ` · čekání vypršelo: ${data.waitingExpiredCount}`;
    }
    meta.textContent = text;
  }
  renderBadges(data);
  renderTop(data);
  renderCalendar(data);
  renderColumns(data);
  renderByProject(data);
  renderEdu(data);
  restoreOpenState(openKeys.length ? openKeys : loadPersistedOpenState());
  if (opts.preserveOpen) persistOpenState();
}

function startLiveRefresh(initialData) {
  const proto = location.protocol;
  if (proto === 'file:') return;
  if (proto !== 'http:' && proto !== 'https:') return;

  lastSeenGenerated = initialData?.generated || initialData?.updated || null;

  const poll = async () => {
    try {
      const stampRes = await fetch('./dashboard-build-stamp.json?t=' + Date.now(), {
        cache: 'no-store',
      });
      if (!stampRes.ok) return;
      const stamp = await stampRes.json();
      const gen = stamp.generated;
      if (!gen || gen === lastSeenGenerated) return;
      const dataRes = await fetch('./dashboard-data.json?t=' + Date.now(), { cache: 'no-store' });
      if (!dataRes.ok) return;
      const data = await dataRes.json();
      lastSeenGenerated = data.generated || gen;
      window.__DASHBOARD_DATA__ = data;
      renderAll(data, { preserveOpen: true });
    } catch {
      /* ignore transient network errors */
    }
  };

  setInterval(poll, LIVE_POLL_MS);
}

async function main() {
  try {
    bindOpenStatePersistence();
    const calPanel = document.querySelector('.cal-panel-details');
    if (calPanel && !calPanel.dataset.openKey) calPanel.dataset.openKey = 'cal';
    const data = await loadData();
    renderAll(data);
    startLiveRefresh(data);
  } catch (e) {
    document.body.insertAdjacentHTML(
      'beforeend',
      `<p class="panel hint">Chyba: ${esc(e.message)}. Spusť build_dashboard.py.</p>`
    );
  }
}

main();
