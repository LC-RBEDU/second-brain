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

function normalizeSearchQuery(q) {
  return (q || '')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/\p{M}/gu, '');
}

function taskSearchHaystack(t, data) {
  const parts = [];
  const projName = data?.projects?.[t.proj]?.name || '';
  parts.push(t.id, t.displayId, t.name, t.proj, projName, t.dl, t.p, t.sourceLabel);
  (t.ch || []).forEach((c) => {
    parts.push(c.t);
    if (c.n != null) parts.push(String(c.n));
  });
  return normalizeSearchQuery(parts.filter(Boolean).join(' '));
}

function tagSearchTarget(el, haystack) {
  el.classList.add('search-target');
  el.dataset.searchHaystack = haystack;
}

function applyTaskSearchTarget(el, t, data) {
  tagSearchTarget(el, taskSearchHaystack(t, data));
}

function tagAuxSearchTargets(root, selector) {
  if (!root) return;
  root.querySelectorAll(selector).forEach((el) => {
    tagSearchTarget(el, normalizeSearchQuery(el.textContent || ''));
  });
}

let dashboardSearchQuery = '';

function runDashboardSearch(raw) {
  dashboardSearchQuery = raw || '';
  persistSearchQuery();
  const q = normalizeSearchQuery(dashboardSearchQuery);
  const targets = document.querySelectorAll('.search-target');
  let matchCount = 0;

  targets.forEach((el) => {
    const hay = el.dataset.searchHaystack || '';
    const match = !q || hay.includes(q);
    el.classList.toggle('search-hidden', !match);
    el.classList.toggle('search-match', Boolean(q && match));
    if (match && q) matchCount += 1;
  });

  if (q) {
    document.querySelectorAll('details').forEach((d) => {
      if (d.querySelector('.search-target:not(.search-hidden)')) d.open = true;
    });
  }

  document.querySelectorAll('.col-details, .proj-details').forEach((panel) => {
    if (!q) {
      panel.classList.remove('search-panel-empty');
      return;
    }
    const has = panel.querySelector('.search-target:not(.search-hidden)');
    panel.classList.toggle('search-panel-empty', !has);
  });

  const sections = [
    document.getElementById('top-priority'),
    document.getElementById('task-columns')?.closest('.panel'),
    document.getElementById('by-project')?.closest('.panel'),
  ].filter(Boolean);
  sections.forEach((section) => {
    if (!q) {
      section.classList.remove('search-section-empty');
      return;
    }
    const has = section.querySelector('.search-target:not(.search-hidden)');
    section.classList.toggle('search-section-empty', !has);
  });

  const status = document.getElementById('search-status');
  if (status) {
    status.classList.remove('is-empty');
    if (!q) status.textContent = '';
    else if (matchCount === 0) {
      status.textContent = 'Žádné výsledky';
      status.classList.add('is-empty');
    } else {
      const n = matchCount === 1 ? 'výsledek' : matchCount < 5 ? 'výsledky' : 'výsledků';
      status.textContent = `${matchCount} ${n}`;
    }
  }
}

function persistSearchQuery() {
  try {
    sessionStorage.setItem(SEARCH_STATE_KEY, dashboardSearchQuery);
  } catch {
    /* ignore */
  }
}

function loadPersistedSearchQuery() {
  try {
    return sessionStorage.getItem(SEARCH_STATE_KEY) || '';
  } catch {
    return '';
  }
}

function restoreSearchFromStorage() {
  const input = document.getElementById('dashboard-search');
  if (!input) return;
  const saved = loadPersistedSearchQuery();
  if (saved && input.value !== saved) input.value = saved;
  if (input.value) runDashboardSearch(input.value);
}

function bindDashboardSearch() {
  if (window.__DASHBOARD_SEARCH_BOUND__) return;
  window.__DASHBOARD_SEARCH_BOUND__ = true;
  const input = document.getElementById('dashboard-search');
  if (!input) return;
  input.addEventListener('input', () => {
    runDashboardSearch(input.value);
    persistSearchQuery();
  });
  input.addEventListener('search', () => {
    if (!input.value) runDashboardSearch('');
    persistSearchQuery();
  });
  window.__DASHBOARD_SEARCH_INPUT__ = input;
}

function refreshDashboardSearch() {
  tagAuxSearchTargets(document.getElementById('calendar-root'), '.cal-event');
  tagAuxSearchTargets(document.getElementById('edu-news'), '.edu-item');
  const input = document.getElementById('dashboard-search');
  if (input?.value) runDashboardSearch(input.value);
}

async function loadData() {
  try {
    const res = await fetch('dashboard-data.json?' + Date.now(), { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      window.__DASHBOARD_DATA__ = data;
      const embedFp = window.__DASHBOARD_EMBED_FP__;
      const dataFp = data.fingerprint || data.generated;
      if (embedFp && dataFp && embedFp !== dataFp) {
        /* HTML starší než JSON — preferuj čerstvý build */
      }
      return data;
    }
  } catch {
    /* file:// bez fetch — fallback na embed v HTML */
  }
  if (window.__DASHBOARD_DATA__) return window.__DASHBOARD_DATA__;
  throw new Error('dashboard-data.json missing — spusť build_dashboard.py');
}

function esc(s) {
  const d = document.createElement('div');
  d.textContent = s ?? '';
  return d.innerHTML;
}

const CZ_TZ = 'Europe/Prague';

/** ISO / YYYY-MM-DD → český formát (např. 20. 5. 2026 18:09:53). */
function formatCzDateTime(isoOrDate) {
  if (!isoOrDate) return '—';
  const s = String(isoOrDate).trim();
  const dateOnly = /^\d{4}-\d{2}-\d{2}$/.test(s);
  const d = dateOnly ? new Date(`${s}T12:00:00`) : new Date(s);
  if (Number.isNaN(d.getTime())) return s;
  return new Intl.DateTimeFormat('cs-CZ', {
    day: 'numeric',
    month: 'numeric',
    year: 'numeric',
    ...(dateOnly
      ? {}
      : { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }),
    timeZone: CZ_TZ,
  }).format(d);
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
const SEARCH_STATE_KEY = 'mrluc-dashboard-search';

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
    applyTaskSearchTarget(div, t, data);
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
    applyTaskSearchTarget(item, t, data);
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

const PROJ_SORT_KEY = 'mrluc-dashboard-proj-sort';
const PROJ_SORT_MODES = ['name', 'tasks', 'ice'];

function loadProjectSortMode() {
  try {
    const v = localStorage.getItem(PROJ_SORT_KEY);
    return PROJ_SORT_MODES.includes(v) ? v : 'name';
  } catch {
    return 'name';
  }
}

function saveProjectSortMode(mode) {
  try {
    localStorage.setItem(PROJ_SORT_KEY, mode);
  } catch {
    /* private mode */
  }
}

function projectPanelTasks(data, slug, waitingIds) {
  return (data.tasks || []).filter((t) => {
    if (t.proj !== slug || t.st === 'dn') return false;
    if (t.p === 'Waiting' && !waitingIds.has(`${t.proj}:${t.id}`)) return false;
    return true;
  });
}

function projectHasBriefing(proj) {
  return !!(
    proj.contextSnippet ||
    proj.progress?.length ||
    proj.materials?.length ||
    proj.openQuestions?.length
  );
}

function projectIceSum(tasks) {
  return tasks.reduce((sum, t) => sum + (iceScore(t) ?? 0), 0);
}

function sortedProjectSlugs(data, sortMode) {
  const order = data.proj_order || [];
  const waitingIds = new Set((data.waiting || []).map((t) => `${t.proj}:${t.id}`));
  const slugs = order.filter((slug) => {
    const proj = data.projects?.[slug] || {};
    const tasks = projectPanelTasks(data, slug, waitingIds);
    return tasks.length > 0 || projectHasBriefing(proj);
  });

  const metrics = (slug) => {
    const proj = data.projects?.[slug] || {};
    const tasks = projectPanelTasks(data, slug, waitingIds);
    const name = (proj.name || slug).toLocaleLowerCase('cs');
    return { name, tasks: tasks.length, ice: projectIceSum(tasks) };
  };

  return slugs.slice().sort((a, b) => {
    const ma = metrics(a);
    const mb = metrics(b);
    if (sortMode === 'tasks') {
      if (mb.tasks !== ma.tasks) return mb.tasks - ma.tasks;
      return ma.name.localeCompare(mb.name, 'cs');
    }
    if (sortMode === 'ice') {
      if (mb.ice !== ma.ice) return mb.ice - ma.ice;
      return ma.name.localeCompare(mb.name, 'cs');
    }
    return ma.name.localeCompare(mb.name, 'cs');
  });
}

function syncProjectSortUi(mode) {
  document.querySelectorAll('.proj-sort-btn').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.sort === mode);
  });
}

function bindProjectSort(lastDataRef) {
  const bar = document.getElementById('proj-sort-bar');
  if (!bar || window.__DASHBOARD_PROJ_SORT_BOUND__) return;
  window.__DASHBOARD_PROJ_SORT_BOUND__ = true;
  const mode = loadProjectSortMode();
  syncProjectSortUi(mode);
  bar.addEventListener('click', (e) => {
    const btn = e.target.closest('.proj-sort-btn');
    if (!btn?.dataset.sort || !PROJ_SORT_MODES.includes(btn.dataset.sort)) return;
    const next = btn.dataset.sort;
    saveProjectSortMode(next);
    syncProjectSortUi(next);
    if (lastDataRef.current) renderByProject(lastDataRef.current);
  });
}

function renderProjectBriefing(proj, slug) {
  if (!proj) return '';
  const parts = [];
  const st = proj.stats || {};
  const statBits = [];
  if (st.open != null) statBits.push(`${st.open} otevřených`);
  if (st.asap) statBits.push(`${st.asap} ASAP`);
  if (st.waiting) statBits.push(`${st.waiting} čeká`);
  if (st.doneWeek) statBits.push(`${st.doneWeek} hotovo týden`);
  if (statBits.length) {
    parts.push(`<p class="proj-brief-stats">${esc(statBits.join(' · '))}</p>`);
  }
  if (proj.progress?.length) {
    const li = proj.progress
      .slice(0, 3)
      .map((p) => `<li>${esc(p)}</li>`)
      .join('');
    parts.push(`<ul class="proj-brief-progress">${li}</ul>`);
  } else if (proj.contextSnippet) {
    parts.push(`<p class="proj-brief-context">${esc(proj.contextSnippet)}</p>`);
  }
  if (proj.openQuestions?.length) {
    const li = proj.openQuestions
      .slice(0, 4)
      .map((q) => `<li>${esc(q)}</li>`)
      .join('');
    parts.push(`<p class="proj-brief-label">Otázky</p><ul class="proj-brief-questions">${li}</ul>`);
  }
  if (proj.materials?.length) {
    const links = proj.materials
      .slice(0, 6)
      .map((m) => {
        const url = m.url || '#';
        const label = m.label || url;
        return `<a class="proj-mat-link" href="${esc(url)}" target="_blank" rel="noopener">${esc(label)}</a>`;
      })
      .join('');
    parts.push(`<p class="proj-brief-label">Materiály</p><div class="proj-brief-materials">${links}</div>`);
  }
  if (proj.hubFile || proj.outputFolder) {
    const bits = [];
    if (proj.hubFile) bits.push(`Hub: ${proj.hubFile}`);
    if (proj.outputFolder) bits.push(`Výstupy: ${proj.outputFolder}`);
    parts.push(`<p class="proj-brief-folder hint">${esc(bits.join(' · '))}</p>`);
  }
  if (!parts.length) return '';
  return `<div class="proj-briefing">${parts.join('')}</div>`;
}

function renderByProject(data) {
  const root = document.getElementById('by-project');
  const order = data.proj_order || [];
  const orderIndex = new Map(order.map((slug, i) => [slug, i]));
  const waitingIds = new Set((data.waiting || []).map((t) => `${t.proj}:${t.id}`));
  const sortMode = loadProjectSortMode();
  syncProjectSortUi(sortMode);
  root.innerHTML = '';
  sortedProjectSlugs(data, sortMode).forEach((slug) => {
    const proj = data.projects?.[slug] || {};
    const tasks = projectPanelTasks(data, slug, waitingIds);
    const name = proj.name || slug;
    const color = projectColor(slug, orderIndex.get(slug) ?? 0);
    const withCh = tasks.filter((t) => t.ch?.length).length;
    const iceSum = projectIceSum(tasks);
    let countLabel = tasks.length
      ? `${tasks.length} úkolů${withCh ? ` · ${withCh} s checklistem` : ''}`
      : 'jen kontext';
    if (sortMode === 'ice' && tasks.length) {
      countLabel += ` · Σ ICE ${iceSum.toFixed(1)}`;
    }

    const block = document.createElement('details');
    block.className = 'proj-details';
    block.dataset.openKey = 'proj:' + slug;
    block.innerHTML = `<summary class="proj-summary" style="--proj-color:${color}">
      <span class="proj-name">${esc(name)}</span>
      <span class="proj-count">${esc(countLabel)}</span>
    </summary>`;

    const body = document.createElement('div');
    body.className = 'proj-body';
    const briefHtml = renderProjectBriefing(proj, slug);
    if (briefHtml) {
      const brief = document.createElement('div');
      brief.innerHTML = briefHtml;
      body.appendChild(brief.firstElementChild || brief);
    }

    const inner = document.createElement('div');
    inner.className = 'proj-tasks';
    tasks.forEach((t) => {
      const row = document.createElement('div');
      row.className = 'task-item';
      const { displayId } = taskProjectStyle(t, data);
      applyTaskProjectEl(row, t, data);
      applyTaskSearchTarget(row, t, data);
      row.innerHTML = renderTaskRow(t, { showMeta: true, displayId });
      inner.appendChild(row);
    });
    body.appendChild(inner);
    block.appendChild(body);
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

function eventStartMs(ev) {
  if (!ev.start) return 0;
  const d = new Date(ev.start);
  return Number.isNaN(d.getTime()) ? 0 : d.getTime();
}

/** Časové události dnešního dne po skončení (end < teď) — schovat v průběhu dne. Zítra + celodenní beze změny. */
function eventEndMs(ev) {
  if (ev.allDay) return null;
  const raw = ev.end || ev.start;
  if (!raw) return null;
  const d = new Date(raw);
  return Number.isNaN(d.getTime()) ? null : d.getTime();
}

function isCalendarEventOverdueToday(ev) {
  const day = (ev.start || '').slice(0, 10);
  if (day !== pragueYmd()) return false;
  if (ev.allDay) return false;
  const endMs = eventEndMs(ev);
  return endMs != null && endMs < Date.now();
}

/** Kalendářové „šumy“ — v dashboardu se nevykreslují. */
const CALENDAR_HIDDEN_TITLES = new Set(['🚌 Travel', '😎 Decompress & notes']);

function isCalendarEventHidden(ev) {
  return CALENDAR_HIDDEN_TITLES.has((ev.title || '').trim());
}

function filterCalendarEventsForDisplay(events) {
  return events.filter((ev) => {
    if (isCalendarEventHidden(ev)) return false;
    if (!isCalendarDayAllowed((ev.start || '').slice(0, 10))) return false;
    if (isCalendarEventOverdueToday(ev)) return false;
    return true;
  });
}

let calendarOverdueTimer = null;

function startCalendarOverdueSweep(dataRef) {
  if (calendarOverdueTimer) {
    clearInterval(calendarOverdueTimer);
    calendarOverdueTimer = null;
  }
  calendarOverdueTimer = setInterval(() => {
    if (dataRef.current) renderCalendar(dataRef.current);
  }, 60_000);
}

function renderCalendar(data) {
  const el = document.getElementById('calendar-root');
  if (!el) return;
  const cal = data.calendar || {};
  const events = filterCalendarEventsForDisplay(cal.events || []);
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
    const dayEvents = (byDay[day] || []).filter((ev) => !isCalendarEventOverdueToday(ev));
    if (!dayEvents.length) return;
    const label = new Date(day + 'T12:00:00').toLocaleDateString('cs-CZ', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
    });
    html += `<div class="cal-day"><h4 class="cal-day-title">${esc(label)}</h4><ul class="cal-events">`;
    dayEvents
      .sort((a, b) => eventStartMs(a) - eventStartMs(b))
      .forEach((ev) => {
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

function renderWeeklyReview(data) {
  const el = document.getElementById('weekly-review');
  if (!el) return;
  const w = data.weeklyReview || {};
  const week = w.week || '—';
  const lines = [];
  lines.push(`<p><strong>Týden ${esc(week)}</strong></p>`);
  if (w.draftFile) {
    lines.push(`<p>Weekly draft: <code>${esc(w.draftFile)}</code></p>`);
  } else {
    lines.push('<p class="hint">Weekly draft zatím ne — čeká na nedělní cron nebo spusť <code>weekly_summary_draft.py</code>.</p>');
  }
  if (w.finalFile) {
    lines.push(`<p>Weekly finální: <code>${esc(w.finalFile)}</code></p>`);
  }
  if (w.retroDraftFile) {
    lines.push(`<p>Retro draft: <code>${esc(w.retroDraftFile)}</code></p>`);
  }
  if (w.retroFinalFile) {
    lines.push(`<p>Retro finální: <code>${esc(w.retroFinalFile)}</code></p>`);
  }
  el.innerHTML = lines.join('');
}

function renderEdu(data) {
  const el = document.getElementById('edu-news');
  const items = data.eduNews || [];
  if (!items.length) {
    el.innerHTML = '<p class="hint">OPS2 — žádná témata. Cron <code>edu_news_refresh.py</code> nebo po natočení videa <code>--clear</code>.</p>';
    return;
  }
  const updated = data.eduNewsUpdated
    ? `<p class="hint edu-updated">Témata: ${esc(formatCzDateTime(data.eduNewsUpdated))}</p>`
    : '';
  el.innerHTML = updated + '<ul class="edu-list">' + items.map(formatEduItem).join('') + '</ul>';
}

const LIVE_POLL_MS = (() => {
  const sec = parseInt(window.DASHBOARD_POLL_SEC || '60', 10);
  return Number.isFinite(sec) && sec > 0 ? sec * 1000 : 60000;
})();

let lastSeenFingerprint = null;
let livePollPaused = false;
const dashboardDataRef = { current: null };

function renderAll(data, opts = {}) {
  dashboardDataRef.current = data;
  const openKeys = opts.preserveOpen ? captureOpenState() : [];
  const meta = document.getElementById('meta-updated');
  if (meta) {
    let text = 'Aktualizováno: ' + formatCzDateTime(data.generated || data.updated);
    if (data.waitingReactivated?.length) {
      const ids = data.waitingReactivated.map((t) => t.displayId || t.id).join(', ');
      text += ` · Waiting→ASAP: ${ids}`;
    } else if (data.waitingExpiredCount > 0) {
      text += ` · čekání vypršelo: ${data.waitingExpiredCount} (spusť build)`;
    }
    meta.textContent = text;
  }
  renderBadges(data);
  renderTop(data);
  renderCalendar(data);
  renderColumns(data);
  renderByProject(data);
  renderWeeklyReview(data);
  renderEdu(data);
  restoreSearchFromStorage();
  refreshDashboardSearch();
  restoreOpenState(openKeys.length ? openKeys : loadPersistedOpenState());
  if (opts.preserveOpen) persistOpenState();
}

function shouldPauseLivePoll() {
  if (livePollPaused) return true;
  if (document.hidden) return true;
  const input = window.__DASHBOARD_SEARCH_INPUT__;
  if (input && document.activeElement === input) return true;
  return false;
}

function bindLivePollPause() {
  if (window.__DASHBOARD_POLL_PAUSE_BOUND__) return;
  window.__DASHBOARD_POLL_PAUSE_BOUND__ = true;
  const input = document.getElementById('dashboard-search');
  if (input) {
    input.addEventListener('focus', () => {
      livePollPaused = true;
    });
    input.addEventListener('blur', () => {
      livePollPaused = false;
    });
  }
}

let livePollFileBlocked = false;

function showDashboardRefreshNotice(generated) {
  const meta = document.getElementById('meta-updated');
  if (!meta) return;
  const when = formatCzDateTime(generated);
  meta.textContent = `Aktualizováno: ${when} · právě načteno z buildu`;
  meta.classList.add('meta-just-refreshed');
  window.setTimeout(() => meta.classList.remove('meta-just-refreshed'), 4000);
}

function updateFilePollHint() {
  const meta = document.getElementById('meta-updated');
  if (!meta || location.protocol === 'http:' || location.protocol === 'https:') return;
  if (!livePollFileBlocked) return;
  const base = meta.textContent.replace(/\s*·\s*live refresh[^·]*$/i, '').trim();
  meta.textContent = `${base} · live refresh: spusť ./scripts/serve_dashboard.sh (file://)`;
}

async function pollDashboardData() {
  if (shouldPauseLivePoll()) return false;
  try {
    const stampRes = await fetch('./dashboard-build-stamp.json?t=' + Date.now(), {
      cache: 'no-store',
    });
    if (!stampRes.ok) {
      if (location.protocol === 'file:') livePollFileBlocked = true;
      updateFilePollHint();
      return false;
    }
    const stamp = await stampRes.json();
    const fp = stamp.fingerprint || stamp.generated;
    if (!fp || fp === lastSeenFingerprint) return false;
    const dataRes = await fetch('./dashboard-data.json?t=' + Date.now(), { cache: 'no-store' });
    if (!dataRes.ok) return false;
    const data = await dataRes.json();
    const nextFp = data.fingerprint || data.generated || fp;
    if (nextFp === lastSeenFingerprint) return false;
    lastSeenFingerprint = nextFp;
    window.__DASHBOARD_DATA__ = data;
    dashboardDataRef.current = data;
    renderAll(data, { preserveOpen: true });
    showDashboardRefreshNotice(data.generated || data.updated);
    livePollFileBlocked = false;
    return true;
  } catch {
    if (location.protocol === 'file:') {
      livePollFileBlocked = true;
      updateFilePollHint();
    }
    return false;
  }
}

function startLiveRefresh(initialData) {
  lastSeenFingerprint =
    initialData?.fingerprint || initialData?.generated || initialData?.updated || null;

  const embedFp = window.__DASHBOARD_EMBED_FP__;
  if (embedFp && embedFp !== lastSeenFingerprint) {
    pollDashboardData();
  }

  setInterval(() => {
    pollDashboardData();
  }, LIVE_POLL_MS);

  window.setTimeout(() => pollDashboardData(), 2500);
}

async function main() {
  try {
    bindOpenStatePersistence();
    bindDashboardSearch();
    bindLivePollPause();
    bindProjectSort(dashboardDataRef);
    const calPanel = document.querySelector('.cal-panel-details');
    if (calPanel && !calPanel.dataset.openKey) calPanel.dataset.openKey = 'cal';
    const data = await loadData();
    renderAll(data);
    startCalendarOverdueSweep(dashboardDataRef);
    startLiveRefresh(data);
  } catch (e) {
    document.body.insertAdjacentHTML(
      'beforeend',
      `<p class="panel hint">Chyba: ${esc(e.message)}. Spusť build_dashboard.py.</p>`
    );
  }
}

main();
