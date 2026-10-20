import { useMemo, useState } from "react";
import { classify, visibleTasks } from "../classify.js";
import { pausedSlugs, projectSlug } from "../focusSlots.js";
import { applySelection, canSend, deleteDate, keepDate, occupancy, overwriteDate } from "../spread.js";
import { closingPreview, kanbanPatch, offerKeep, rowPatch } from "../writes.js";

const COLUMNS = ["Doing", "Next", "Waiting", "Backlog"];
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
  const [draft, setDraft] = useState({ title: "", deadline: "" });
  const [checked, setChecked] = useState({});
  const [actions, setActions] = useState({});
  const [preview, setPreview] = useState(null);
  const [selectionDate, setSelectionDate] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [maxPerDay, setMaxPerDay] = useState("8");
  const [skipNonWork, setSkipNonWork] = useState(false);
  const [dialog, setDialog] = useState(null);
  const [doingDate, setDoingDate] = useState("");
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
    setDetailId(task.id);
    setDraft({ title: task.title || "", deadline: task.deadline || "" });
    setView("detail");
  }

  async function saveDetail() {
    if (!detail || !api?.patch) return;
    const patch = { title: draft.title };
    if (draft.deadline) patch.deadline = draft.deadline;
    const result = await api.patch({ path: detail.path, patch, expect_oid: oidOf(detail) });
    if (result?.ok) {
      onRefresh?.();
      return;
    }
    if (result?.error_reason === "oid_mismatch") {
      setDialog({
        kind: "q9",
        path: detail.path,
        draftTitle: draft.title,
        currentTitle: result.current?.title || "",
        oid: result.oid,
      });
      return;
    }
    if (result?.error_reason === "deadline_order") {
      setDialog({ kind: "deadline_order", text: result.detail?.message || "" });
    }
  }

  async function move(task, status) {
    if (status === "Doing" && !task.deadline) {
      setDoingDate("");
      setDialog({ kind: "doing", task });
      return;
    }
    const patch = kanbanPatch(task, status, openTasks);
    if (!patch || !api?.patch) return;
    const result = await api.patch({ path: task.path, patch, expect_oid: oidOf(task) });
    if (result?.ok) onRefresh?.();
  }

  async function confirmDoing() {
    if (!doingDate || !dialog?.task || !api?.patch) return;
    const result = await api.patch({
      path: dialog.task.path,
      patch: { status: "Doing", deadline: doingDate },
      expect_oid: oidOf(dialog.task),
    });
    setDialog(null);
    if (result?.ok) onRefresh?.();
  }

  function openPreview() {
    const rows = [];
    const seen = new Set();
    for (const task of openTasks) {
      if (!checked[task.id]) continue;
      const action = actions[task.id] || (offerKeep(task) ? "keep" : "done");
      const produced =
        action === "keep"
          ? [
              {
                id: task.id,
                title: task.title || "",
                parent: task.parent || "",
                action,
                resulting: "keep",
                direct: true,
                locked: false,
                path: task.path,
                expect_oid: oidOf(task),
                dateState: keepDate(task.review_deadline || ""),
              },
            ]
          : closingPreview(task.id, action, openTasks).map((row) => {
              const source = byId.get(row.id);
              return {
                ...row,
                resulting: row.action,
                path: source?.path || "",
                expect_oid: source ? oidOf(source) : "",
                dateState: keepDate(""),
              };
            });
      for (const row of produced) {
        if (seen.has(row.id)) continue;
        seen.add(row.id);
        rows.push(row);
      }
    }
    setPreview(rows);
    setSelectionDate("");
    setCleanupResult(null);
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

  const unresolved = (preview || []).filter((row) => row.resulting === "keep" && !row.dateState?.date);
  const sendAllowed = canSend({
    queue: unresolved.map((row) => ({ id: row.id, date: from ? "pending" : null })),
    from,
    to,
    maxPerDay: Number(maxPerDay),
    pending: unresolved.length && !from ? unresolved.length : 0,
  });

  async function submitCleanup() {
    if (!preview || !sendAllowed || !api?.cleanup) return;
    const source = cleanupResult
      ? preview.filter((row) => cleanupResult.failed?.includes(row.id) || cleanupResult.pending?.includes(row.id))
      : preview;
    const result = await api.cleanup({
      items: source.map((row) => ({
        id: row.id,
        path: row.path,
        title: row.title,
        parent: row.parent,
        expect_oid: oids[row.id] || row.expect_oid,
        patch: rowPatch({ resulting: row.resulting, date: row.dateState?.date }),
      })),
    });
    setCleanupResult(result);
    setOids((current) => ({ ...current, ...(result?.expect_oid || {}) }));
    onRefresh?.();
    const stay = [...(result?.failed || []), ...(result?.pending || [])];
    setChecked(Object.fromEntries(stay.map((id) => [id, true])));
  }

  const counts =
    preview &&
    occupancy(
      openTasks,
      new Map(
        preview.map((row) => [
          row.id,
          { resulting: row.resulting, date: row.dateState?.date || null, dateDeleted: row.dateState?.dateDeleted },
        ]),
      ),
    );

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
          {[...new Map(classified.issues.filter((item) => item.severity === "error" && item.rule !== "no_date").map((item) => [item.id, item])).values()].map(
            (item) => (
              <article key={item.id}>
                <p>{item.id} — {item.title}</p>
                <p>{classified.issues.filter((issue) => issue.id === item.id && issue.severity === "error" && issue.rule !== "no_date").map((issue) => issue.rule).join(", ")}</p>
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
          <button type="button" onClick={saveDetail}>Uložit</button>
        </section>
      )}

      {view === "new" && (
        <section aria-label="Nový task">
          <label>
            Projekt
            <select aria-label="Projekt nového tasku">
              {activeProjects.map((item) => (
                <option key={item.slug}>{item.slug}</option>
              ))}
            </select>
          </label>
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
              {preview.filter((row) => !dropped.has(row.id)).map((row) => (
                <div key={row.id}>
                  <label>
                    <input type="checkbox" aria-label={`Náhled ${row.id} — ${row.title}`} checked disabled={row.locked} readOnly />
                    {row.id} — {row.title}
                  </label>
                  <span>{row.resulting === "cancelled" ? "Zrušeno" : row.resulting === "done" ? "Hotovo" : "Ponechat"}</span>
                  {row.resulting === "keep" && (
                    <input
                      aria-label={`Termín ${row.id}`}
                      value={row.dateState?.date || ""}
                      onChange={(event) => setRowDate(row.id, event.target.value)}
                    />
                  )}
                </div>
              ))}
              {counts && [...counts.entries()].sort().map(([day, count]) => (
                <p key={day}>Obsazenost {day}: {count}</p>
              ))}
              <button type="button" disabled={!sendAllowed} onClick={submitCleanup}>Uložit</button>
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
          <p>U tebe: {dialog.draftTitle}</p>
          <p>Ve vaultu: {dialog.currentTitle}</p>
          <button
            type="button"
            onClick={() => {
              api.patch({ path: dialog.path, patch: { title: dialog.draftTitle }, expect_oid: dialog.oid });
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
    </div>
  );
}
