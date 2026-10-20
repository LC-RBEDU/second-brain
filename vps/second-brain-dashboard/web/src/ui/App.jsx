import { useMemo, useState } from "react";
import { classify, visibleTasks } from "../classify.js";
import { isoWeek, pausedSlugs, projectSlug } from "../focusSlots.js";
import { applySelection, assignDays, canSend, deleteDate, keepDate, occupancy, overwriteDate, sortQueue } from "../spread.js";
import { closingPreview, kanbanPatch, offerKeep, resolveCloser, rowPatch } from "../writes.js";

const COLUMNS = ["Doing", "Next", "Waiting", "Backlog"];
const FOCUS_TEXT = {
  focus_story_has_open_child: "Story s otevřeným taskem do focusu nepatří",
  focus_limit_exceeded: "Focus už má 10 tasků",
  focus_task_limit_exceeded: "Focus už má 10 tasků",
  focus_epic_limit_exceeded: "Focus už má 5 epiců",
  cas_conflict: "Neshoda verze",
};
const COMPARE_FIELDS = ["title", "status", "deadline", "review_deadline", "waitUntil", "parent"];

function parentId(value) {
  if (!value) return "";
  const text = String(value).trim();
  const linked = /\[\[([^\]|]+)/.exec(text);
  return (linked ? linked[1] : text).split(/\s+[—–-]/)[0].trim();
}

function conflictText(detail) {
  const rows = detail?.conflicts || [];
  if (rows.length) {
    return rows
      .map((row) => `${row.child_id} ${row.child_deadline} > ${row.parent_id} ${row.parent_deadline}`)
      .join("; ");
  }
  return detail?.message || "";
}
const TILES = [
  ["overdue", "Overdue"],
  ["to_decide", "K rozhodnutí"],
  ["due_soon", "Blízký termín"],
  ["waiting_overdue", "Waiting po termínu"],
  ["doing", "Doing"],
  ["focus", "Focus"],
  ["no_date", "Bez termínu"],
  ["errors", "Chybně zadané"],
  ["stale", "Bez změny"],
];

export function labelOf(task) {
  return `${task.id} — ${task.title || task.id}`;
}

function hiddenWrittenIds(result) {
  if (!result?.written) return new Set();
  const saved = new Set(result.saved || []);
  return new Set(result.written.ids.filter((id) => !saved.has(id)));
}

export function App({ exportData, api, today = "2026-10-20", onRefresh }) {
  const tasks = exportData?.tasks || [];
  const projects = exportData?.projects || [];
  const paused = useMemo(() => pausedSlugs(projects), [projects]);
  const [view, setView] = useState("radar");
  const [showPaused, setShowPaused] = useState(false);
  const [query, setQuery] = useState("");
  const [project, setProject] = useState("");
  const [board, setBoard] = useState(false);
  const [detailId, setDetailId] = useState("");
  const [returnView, setReturnView] = useState("radar");
  const [draft, setDraft] = useState({ title: "", deadline: "", parent: "" });
  const [newDraft, setNewDraft] = useState({ title: "", level: "task", status: "Next", deadline: "", review: "", parent: "", waitUntil: "" });
  const [checked, setChecked] = useState({});
  const [actions, setActions] = useState({});
  const [preview, setPreview] = useState(null);
  const [selectionDate, setSelectionDate] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [maxPerDay, setMaxPerDay] = useState("8");
  const [skipNonWork, setSkipNonWork] = useState(false);
  const [sortMode, setSortMode] = useState("project_epic");
  const [dialog, setDialog] = useState(null);
  const [doingDate, setDoingDate] = useState("");
  const [waitDate, setWaitDate] = useState("");
  const [oids, setOids] = useState({});
  const [cleanupResult, setCleanupResult] = useState(null);

  const byId = useMemo(() => new Map(tasks.map((task) => [task.id, task])), [tasks]);
  const openTasks = useMemo(() => visibleTasks(tasks), [tasks]);
  const dropped = hiddenWrittenIds(cleanupResult);
  const listed = openTasks.filter((task) => {
    if (dropped.has(task.id)) return false;
    if (!showPaused && paused.has(projectSlug(task))) return false;
    if (!query.trim()) return true;
    const hay = `${task.id} ${task.title || ""} ${task.project || ""} ${task.parent || ""}`.toLowerCase();
    return hay.includes(query.trim().toLowerCase());
  });
  const classified = classify({ tasks: listed }, { today, projects });
  const activeProjects = projects.filter((item) => showPaused || !paused.has(item.slug));
  const projectSlugValue = project || activeProjects[0]?.slug || "";
  const projectTasks = listed.filter((task) => task.project === projectSlugValue);
  const detail = byId.get(detailId);

  function oidOf(task) {
    return oids[task.id] || task.expect_oid || "";
  }

  function openDetail(task) {
    setReturnView(view);
    setDetailId(task.id);
    setDraft({ title: task.title || "", deadline: task.deadline || "", parent: parentId(task.parent) });
    setView("detail");
  }

  async function openConflict(result, patch, path, taskId) {
    if (result?.ok) {
      onRefresh?.();
      return true;
    }
    if (result?.error_reason === "oid_mismatch") {
      let current = result.current || {};
      if (api?.item && taskId) {
        const item = await api.item(taskId);
        if (item?.frontmatter) current = item.frontmatter;
      }
      const yours = {};
      const vault = {};
      for (const key of COMPARE_FIELDS) {
        vault[key] = current[key] == null ? "" : String(current[key]);
        yours[key] = Object.prototype.hasOwnProperty.call(patch, key) ? String(patch[key] ?? "") : vault[key];
      }
      setDialog({
        kind: "q9",
        path,
        patch,
        yours,
        vault,
        oid: result.oid,
      });
      return false;
    }
    if (result?.error_reason === "deadline_order") {
      setDialog({ kind: "deadline_order", text: conflictText(result.detail) });
      return false;
    }
    return false;
  }

  async function saveDetail() {
    if (!detail || !api?.patch) return;
    const patch = { title: draft.title };
    if (draft.deadline) patch.deadline = draft.deadline;
    if (detail.type !== "epic" && draft.parent !== parentId(detail.parent)) patch.parent = draft.parent;
    const result = await api.patch({ path: detail.path, patch, expect_oid: oidOf(detail) });
    if (await openConflict(result, patch, detail.path, detail.id)) return;
    if (result?.error_reason === "oid_mismatch" || result?.error_reason === "deadline_order") return;
  }

  async function move(task, status) {
    if (status === "Doing" && !task.deadline) {
      setDoingDate("");
      setDialog({ kind: "doing", task });
      return;
    }
    if (status === "Waiting" && !task.waitUntil) {
      setWaitDate("");
      setDialog({ kind: "waiting", task });
      return;
    }
    const patch = kanbanPatch(task, status, openTasks);
    if (!patch || !api?.patch) return;
    const result = await api.patch({ path: task.path, patch, expect_oid: oidOf(task) });
    await openConflict(result, patch, task.path, task.id);
  }

  async function confirmDoing() {
    if (!doingDate || !dialog?.task || !api?.patch) return;
    const patch = { status: "Doing", deadline: doingDate };
    const result = await api.patch({
      path: dialog.task.path,
      patch,
      expect_oid: oidOf(dialog.task),
    });
    if (result?.ok) {
      setDialog(null);
      onRefresh?.();
      return;
    }
    if (result?.error_reason === "oid_mismatch" || result?.error_reason === "deadline_order") {
      await openConflict(result, patch, dialog.task.path, dialog.task.id);
      return;
    }
    setDialog(null);
  }

  async function confirmWaiting() {
    if (!waitDate || !dialog?.task || !api?.patch) return;
    const patch = { status: "Waiting", waitUntil: waitDate };
    const result = await api.patch({
      path: dialog.task.path,
      patch,
      expect_oid: oidOf(dialog.task),
    });
    if (result?.ok) {
      setDialog(null);
      onRefresh?.();
      return;
    }
    if (result?.error_reason === "oid_mismatch" || result?.error_reason === "deadline_order") {
      await openConflict(result, patch, dialog.task.path, dialog.task.id);
      return;
    }
    setDialog(null);
  }

  function rowFrom(task, action, extra = {}) {
    return {
      id: task.id,
      title: task.title || "",
      parent: task.parent || "",
      project: task.project || "",
      action,
      direct: true,
      locked: false,
      path: task.path,
      expect_oid: oidOf(task),
      dateState: keepDate(action === "keep" ? task.review_deadline || "" : ""),
      ...extra,
    };
  }

  function openPreview() {
    const raw = [];
    for (const task of openTasks) {
      if (!checked[task.id]) continue;
      const action = actions[task.id] || (offerKeep(task) ? "keep" : "done");
      if (action === "keep") {
        raw.push(rowFrom(task, "keep"));
        continue;
      }
      for (const row of closingPreview(task.id, action, openTasks)) {
        const source = byId.get(row.id) || task;
        raw.push(rowFrom(source, row.action, { parent: row.parent, direct: row.direct, locked: row.locked, title: row.title || source.title || "" }));
      }
    }
    const merged = new Map();
    for (const row of raw) {
      const prev = merged.get(row.id);
      const directClose = row.direct && (row.action === "done" || row.action === "cancelled");
      const prevDirect = prev?.direct && (prev.action === "done" || prev.action === "cancelled");
      if (!prev || directClose || (!prevDirect && row.action !== "keep")) merged.set(row.id, row);
    }
    setPreview(resolveCloser([...merged.values()]));
    setSelectionDate("");
    setCleanupResult(null);
  }

  function setPreviewAction(id, action) {
    setPreview((rows) => resolveCloser(rows.map((row) => (row.id === id ? { ...row, action, direct: true, dateState: keepDate("") } : row))));
  }

  function setRowDate(id, value) {
    setPreview((rows) =>
      rows.map((row) =>
        row.id === id ? { ...row, dateState: value ? overwriteDate(value) : deleteDate() } : row,
      ),
    );
  }

  function applySharedDate(value) {
    setSelectionDate(value);
    setPreview((rows) =>
      rows.map((row) =>
        row.resulting === "keep" ? { ...row, dateState: applySelection(row.dateState, value) } : row,
      ),
    );
  }

  const needsSpread = (preview || []).filter((row) => row.resulting === "keep" && !row.dateState?.date);
  const assignedById = new Map();
  if (preview) {
    const sorted = sortQueue(
      needsSpread.map((row) => {
        const source = byId.get(row.id) || {};
        return { ...source, id: row.id, project: row.project || source.project || "", parent: row.parent || source.parent || "" };
      }),
      sortMode,
      openTasks,
    );
    const baseline = occupancy(
      openTasks,
      new Map(preview.map((row) => [row.id, { resulting: row.resulting, date: row.dateState?.date || null, dateDeleted: !row.dateState?.date }])),
    );
    for (const item of assignDays(sorted, { from, to, maxPerDay: Number(maxPerDay), skipNonWork, taken: baseline })) {
      if (item.date) assignedById.set(item.id, item.date);
    }
  }
  const pendingSpread = needsSpread.filter((row) => !assignedById.get(row.id)).length;
  const sendAllowed = canSend({
    queue: needsSpread.map((row) => ({ id: row.id, date: assignedById.get(row.id) || null })),
    from,
    to,
    maxPerDay: Number(maxPerDay),
    pending: pendingSpread,
  });

  function rowDate(row) {
    return row.dateState?.date || assignedById.get(row.id) || null;
  }

  async function submitCleanup() {
    if (!preview || !sendAllowed || !api?.cleanup || preview.length > 80) return;
    const source = cleanupResult
      ? preview.filter((row) => cleanupResult.failed?.includes(row.id) || cleanupResult.pending?.includes(row.id))
      : preview;
    if (!source.length) return;
    const result = await api.cleanup({
      items: source.map((row) => ({
        id: row.id,
        path: row.path,
        title: row.title,
        parent: row.parent,
        expect_oid: oids[row.id] || row.expect_oid,
        patch: rowPatch({ resulting: row.resulting, date: rowDate(row) }),
      })),
    });
    const rejected = result?.ok === false && !(result?.failed?.length || result?.pending?.length);
    if (!rejected) setCleanupResult(result);
    if (result?.ok === false) return;
    setOids((current) => ({ ...current, ...(result?.expect_oid || {}) }));
    onRefresh?.();
    const stay = [...(result?.failed || []), ...(result?.pending || [])];
    setChecked(Object.fromEntries(stay.map((id) => [id, true])));
    if (!stay.length) setPreview(null);
    if (detailId && (result?.written?.ids || []).includes(detailId) && !(result?.saved || []).includes(detailId)) {
      setDetailId("");
      setView(returnView);
    }
  }

  const counts =
    preview &&
    occupancy(
      openTasks,
      new Map(
        preview.map((row) => [
          row.id,
          { resulting: row.resulting, date: rowDate(row), dateDeleted: !rowDate(row) },
        ]),
      ),
    );

  async function proposeFocus(task) {
    if (!api?.propose) return;
    const result = await api.propose({ task_path: task.path, expect_oid: oidOf(task), focus_week: isoWeek(today) });
    if (result?.ok && result.proposal_id) {
      setDialog({ kind: "focus", proposalId: result.proposal_id, text: "" });
      return;
    }
    const reason = result?.error_reason || "";
    setDialog({ kind: "focus", proposalId: "", text: FOCUS_TEXT[reason] || reason });
  }

  async function applyFocus() {
    if (!dialog?.proposalId || !api?.apply) return;
    const result = await api.apply({ proposal_id: dialog.proposalId });
    if (result?.ok) {
      setDialog(null);
      onRefresh?.();
      return;
    }
    const reason = result?.error_reason || "";
    setDialog({ kind: "focus", proposalId: "", text: FOCUS_TEXT[reason] || reason });
  }

  async function createTask() {
    if (!api?.create) return;
    if (newDraft.status === "Doing" && !newDraft.deadline) return;
    if (newDraft.status === "Waiting" && !newDraft.waitUntil) return;
    const result = await api.create({
      slug: projectSlugValue,
      title: newDraft.title,
      level: newDraft.level,
      status: newDraft.status,
      parent: newDraft.level === "epic" ? "" : newDraft.parent,
      deadline: newDraft.deadline,
      review_deadline: newDraft.deadline ? "" : newDraft.review,
      waitUntil: newDraft.waitUntil,
    });
    if (result?.error_reason === "deadline_order") {
      setDialog({ kind: "deadline_order", text: conflictText(result.detail) });
      return;
    }
    if (result?.ok) onRefresh?.();
  }

  function TaskButton({ task }) {
    return (
      <article className="flex items-center gap-2 py-1">
        <button type="button" onClick={() => openDetail(task)}>
          {labelOf(task)}
        </button>
        {COLUMNS.map((status) => (
          <button key={status} type="button" aria-label={`Přesunout na ${status}`} onClick={() => move(task, status)}>
            {status}
          </button>
        ))}
        <button type="button" aria-label="Označit hotovo" onClick={() => move(task, "Done")}>
          Hotovo
        </button>
        <button type="button" aria-label={`Focus ${task.id}`} onClick={() => proposeFocus(task)}>
          Focus
        </button>
      </article>
    );
  }

  return (
    <div className="min-h-screen bg-[#fafafa] font-[Rubik,system-ui,sans-serif] text-[#444]">
      <nav className="flex flex-wrap gap-2 p-3">
        {[
          ["radar", "Radar"],
          ["issues", "Chybně zadané"],
          ["map", "Mapa"],
          ["project", "Projekt"],
          ["new", "Nový task"],
          ["cleanup", "Úklid"],
        ].map(([id, name]) => (
          <button key={id} type="button" onClick={() => setView(id)}>
            {name}
          </button>
        ))}
        <label>
          <input type="checkbox" checked={showPaused} onChange={(event) => setShowPaused(event.target.checked)} /> Zobrazit pauznuté
        </label>
        <input aria-label="Hledat" value={query} onChange={(event) => setQuery(event.target.value)} />
      </nav>

      {view === "radar" && (
        <section aria-label="Radar">
          <div className="grid grid-cols-3 gap-2 p-3">
            {TILES.map(([key, name]) => (
              <p key={key}>
                {name} {classified.tiles[key]}
              </p>
            ))}
          </div>
          <p>Prošlý focus: {classified.radar.focus_stale.length}</p>
          {listed.map((task) => (
            <TaskButton key={task.id} task={task} />
          ))}
        </section>
      )}

      {view === "issues" && (
        <section aria-label="Chybně zadané">
          <h1>Chybně zadané {classified.tiles.errors}</h1>
          {[...new Map(classified.issues.filter((item) => item.rule !== "no_date").map((item) => [item.id, item])).values()].map(
            (item) => (
              <article key={item.id}>
                <p>{item.id} — {item.title}</p>
                <p>{classified.issues.filter((issue) => issue.id === item.id && issue.rule !== "no_date").map((issue) => issue.rule).join(", ")}</p>
              </article>
            ),
          )}
        </section>
      )}

      {view === "map" && (
        <section aria-label="Mapa">
          {listed.filter((task) => !listed.some((other) => other.id === task.parent)).map((task) => (
            <p key={task.id}>{labelOf(task)}</p>
          ))}
          {listed.filter((task) => task.parent).map((task) => (
            <p key={task.id}>{labelOf(task)}</p>
          ))}
        </section>
      )}

      {view === "project" && (
        <section aria-label="Projekt">
          <select aria-label="Projekt v přehledu" value={projectSlugValue} onChange={(event) => setProject(event.target.value)}>
            {activeProjects.map((item) => (
              <option key={item.slug} value={item.slug}>{item.slug}</option>
            ))}
          </select>
          <button type="button" onClick={() => setBoard(false)}>Seznam</button>
          <button type="button" onClick={() => setBoard(true)}>Kanban</button>
          {board ? (
            <div className="grid grid-cols-4 gap-2">
              {COLUMNS.map((status) => (
                <div key={status}>
                  <div role="columnheader">{status}</div>
                  {projectTasks.filter((task) => task.status === status).map((task) => (
                    <TaskButton key={task.id} task={task} />
                  ))}
                </div>
              ))}
            </div>
          ) : (
            projectTasks.map((task) => <TaskButton key={task.id} task={task} />)
          )}
        </section>
      )}

      {view === "detail" && detail && (
        <section aria-label="Detail">
          <h1>{labelOf(detail)}</h1>
          <label>
            Název <input aria-label="Název" value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} />
          </label>
          <label>
            Deadline <input aria-label="Deadline úkolu" value={draft.deadline} onChange={(event) => setDraft({ ...draft, deadline: event.target.value })} />
          </label>
          {detail.type !== "epic" && (
            <label>
              Parent
              <input
                aria-label="Parent úkolu"
                list="detail-parents"
                value={draft.parent}
                onChange={(event) => setDraft({ ...draft, parent: event.target.value })}
              />
              <datalist id="detail-parents">
                {openTasks
                  .filter((task) => (showPaused || !paused.has(projectSlug(task))) && task.type === (detail.type === "story" ? "epic" : "story"))
                  .map((task) => (
                    <option key={task.id} value={task.id}>{labelOf(task)}</option>
                  ))}
              </datalist>
            </label>
          )}
          <button type="button" onClick={saveDetail}>Uložit</button>
        </section>
      )}

      {view === "new" && (
        <section aria-label="Nový task">
          <label>
            Projekt
            <select aria-label="Projekt nového tasku" value={projectSlugValue} onChange={(event) => setProject(event.target.value)}>
              {activeProjects.map((item) => (
                <option key={item.slug} value={item.slug}>{item.slug}</option>
              ))}
            </select>
          </label>
          <label>
            Název nového <input aria-label="Název nového tasku" value={newDraft.title} onChange={(event) => setNewDraft({ ...newDraft, title: event.target.value })} />
          </label>
          <label>
            Úroveň
            <select aria-label="Úroveň nového tasku" value={newDraft.level} onChange={(event) => setNewDraft({ ...newDraft, level: event.target.value, parent: "" })}>
              <option value="epic">Epic</option>
              <option value="story">Story</option>
              <option value="task">Task</option>
            </select>
          </label>
          <label>
            Stav
            <select aria-label="Stav nového tasku" value={newDraft.status} onChange={(event) => setNewDraft({ ...newDraft, status: event.target.value })}>
              {COLUMNS.map((status) => (
                <option key={status}>{status}</option>
              ))}
            </select>
          </label>
          <label>
            Deadline nového <input aria-label="Deadline nového tasku" value={newDraft.deadline} onChange={(event) => setNewDraft({ ...newDraft, deadline: event.target.value })} />
          </label>
          <label>
            Review nového <input aria-label="Review nového tasku" value={newDraft.review} onChange={(event) => setNewDraft({ ...newDraft, review: event.target.value })} />
          </label>
          <label>
            WaitUntil <input aria-label="WaitUntil nového tasku" value={newDraft.waitUntil} onChange={(event) => setNewDraft({ ...newDraft, waitUntil: event.target.value })} />
          </label>
          {newDraft.level !== "epic" && (
            <label>
              Parent
              <input
                aria-label="Parent nového tasku"
                list="parent-choices"
                value={newDraft.parent}
                onChange={(event) => setNewDraft({ ...newDraft, parent: event.target.value })}
              />
              <datalist id="parent-choices">
                {openTasks.filter((task) => (showPaused || !paused.has(projectSlug(task))) && task.type === (newDraft.level === "story" ? "epic" : "story")).map((task) => (
                  <option key={task.id} value={task.id}>{labelOf(task)}</option>
                ))}
              </datalist>
            </label>
          )}
          <button type="button" onClick={createTask}>Založit</button>
        </section>
      )}

      {view === "cleanup" && (
        <section aria-label="Úklid">
          <div role="region" aria-label="Seznam úklidu">
            {listed.map((task) => (
              <div key={task.id}>
                <label>
                  <input
                    type="checkbox"
                    aria-label={`Vybrat ${labelOf(task)}`}
                    checked={Boolean(checked[task.id])}
                    onChange={(event) => setChecked({ ...checked, [task.id]: event.target.checked })}
                  />
                  {labelOf(task)}
                </label>
                {checked[task.id] && (
                  <select
                    aria-label={`Akce ${task.id}`}
                    value={actions[task.id] || (offerKeep(task) ? "keep" : "done")}
                    onChange={(event) => setActions({ ...actions, [task.id]: event.target.value })}
                  >
                    {offerKeep(task) && <option value="keep">Ponechat</option>}
                    <option value="done">Hotovo</option>
                    <option value="cancelled">Zrušit</option>
                  </select>
                )}
              </div>
            ))}
          </div>
          <button type="button" onClick={openPreview}>Náhled</button>
          {preview && (
            <div role="region" aria-label="Náhled úklidu">
              <label>
                Termín pro výběr
                <input aria-label="Termín pro výběr" value={selectionDate} onChange={(event) => applySharedDate(event.target.value)} />
              </label>
              <label>
                Od <input aria-label="Od" value={from} onChange={(event) => setFrom(event.target.value)} />
              </label>
              <label>
                Do <input aria-label="Do" value={to} onChange={(event) => setTo(event.target.value)} />
              </label>
              <label>
                Max <input aria-label="Max za den" value={maxPerDay} onChange={(event) => setMaxPerDay(event.target.value)} />
              </label>
              <label>
                <input type="checkbox" aria-label="Přeskočit nepracovní dny" checked={skipNonWork} onChange={(event) => setSkipNonWork(event.target.checked)} />
                Přeskočit nepracovní dny
              </label>
              <label>
                Pořadí
                <select aria-label="Pořadí rozprostření" value={sortMode} onChange={(event) => setSortMode(event.target.value)}>
                  <option value="project_epic">projekt a epic</option>
                  <option value="priority">priorita</option>
                  <option value="age">stáří</option>
                </select>
              </label>
              {preview.filter((row) => !dropped.has(row.id)).map((row) => (
                <div key={row.id}>
                  <label>
                    <input type="checkbox" aria-label={`Náhled ${row.id} — ${row.title}`} checked disabled={row.locked} readOnly />
                    {row.id} — {row.title}
                  </label>
                  <span>{row.resulting === "cancelled" ? "Zrušeno" : row.resulting === "done" ? "Hotovo" : "Ponechat"}</span>
                  {row.locked && (
                    <select aria-label={`Náhled akce ${row.id}`} value={row.resulting === "cancelled" ? "cancelled" : "done"} onChange={(event) => setPreviewAction(row.id, event.target.value)}>
                      <option value="done">Hotovo</option>
                      <option value="cancelled">Zrušit</option>
                    </select>
                  )}
                  {row.resulting === "keep" && (
                    <input
                      aria-label={`Termín ${row.id}`}
                      value={rowDate(row) || ""}
                      onChange={(event) => setRowDate(row.id, event.target.value)}
                    />
                  )}
                </div>
              ))}
              {counts && [...counts.entries()].sort().map(([day, count]) => (
                <p key={day}>Obsazenost {day}: {count}</p>
              ))}
              {preview.length > 80 && <p>Rodina je nad 80. Odeber předka.</p>}
              <button type="button" disabled={!sendAllowed || preview.length > 80} onClick={submitCleanup}>Uložit</button>
              <button type="button" onClick={() => setPreview(null)}>Zavřít náhled</button>
              {cleanupResult?.written && (
                <p>Uloženo {cleanupResult.written.count}: {cleanupResult.written.ids.join(", ")}</p>
              )}
              {cleanupResult?.lines?.map((line) => (
                <p key={line}>{line}</p>
              ))}
            </div>
          )}
        </section>
      )}

      {dialog?.kind === "q9" && (
        <div role="dialog" aria-label="Neshoda verze">
          <p>U tebe: {dialog.yours.title}</p>
          <p>Ve vaultu: {dialog.vault.title}</p>
          <p>status: {dialog.yours.status} / {dialog.vault.status}</p>
          <p>deadline: {dialog.yours.deadline} / {dialog.vault.deadline}</p>
          <p>review: {dialog.yours.review_deadline} / {dialog.vault.review_deadline}</p>
          <p>waitUntil: {dialog.yours.waitUntil} / {dialog.vault.waitUntil}</p>
          <p>parent: {dialog.yours.parent} / {dialog.vault.parent}</p>
          <button
            type="button"
            onClick={() => {
              api.patch({ path: dialog.path, patch: dialog.patch, expect_oid: dialog.oid });
              setDialog(null);
            }}
          >
            Přesto uložit
          </button>
          <button type="button" onClick={() => setDialog(null)}>Upravit</button>
        </div>
      )}

      {dialog?.kind === "deadline_order" && (
        <div role="dialog" aria-label="Pořadí termínů">
          <p>{dialog.text}</p>
        </div>
      )}

      {dialog?.kind === "doing" && (
        <div role="dialog" aria-label="Doplň deadline">
          <input aria-label="Datum deadline" value={doingDate} onChange={(event) => setDoingDate(event.target.value)} />
          <button type="button" onClick={confirmDoing}>Potvrdit</button>
        </div>
      )}

      {dialog?.kind === "waiting" && (
        <div role="dialog" aria-label="Doplň waitUntil">
          <input aria-label="Datum waitUntil" value={waitDate} onChange={(event) => setWaitDate(event.target.value)} />
          <button type="button" onClick={confirmWaiting}>Potvrdit</button>
        </div>
      )}

      {dialog?.kind === "focus" && (
        <div role="dialog" aria-label="Focus">
          {dialog.text && <p>{dialog.text}</p>}
          {dialog.proposalId && <button type="button" onClick={applyFocus}>Použít focus</button>}
        </div>
      )}
    </div>
  );
}
