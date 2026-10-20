import { Fragment, useEffect, useMemo, useState } from "react";
import { classify, visibleTasks } from "../classify.js";
import { isoWeek, pausedSlugs, projectSlug } from "../focusSlots.js";
import { applySelection, assignDays, canSend, deleteDate, keepDate, occupancy, overwriteDate, sortQueue } from "../spread.js";
import { closingPreview, kanbanPatch, offerKeep, resolveCloser, rowPatch } from "../writes.js";
import {
  btnGhost,
  btnNav,
  btnPrimary,
  buildMapGroups,
  fieldClass,
  labelClass,
  PageHeader,
  panelClass,
  ParentSuggest,
  projectLabel,
  StatusPill,
} from "./chrome.jsx";

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
  ["due_soon", "Due soon · 7 d"],
  ["to_decide", "K rozhodnutí"],
  ["focus", "Focus"],
  ["waiting_overdue", "Waiting po termínu"],
  ["errors", "Chybně zadané"],
  ["doing", "Doing"],
  ["stale", "Stale"],
  ["no_date", "Bez termínu"],
];

function idsForTile(classified, key) {
  if (key === "errors") {
    return [...new Set(classified.issues.filter((item) => item.severity === "error" && item.rule !== "no_date").map((item) => item.id))];
  }
  if (key === "stale") {
    return [...new Set(classified.issues.filter((item) => item.rule === "stale").map((item) => item.id))];
  }
  if (key === "focus") return classified.radar.focus_week;
  return classified.radar[key] || [];
}

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
  const [radarTile, setRadarTile] = useState("overdue");
  const [showPaused, setShowPaused] = useState(false);
  const [query, setQuery] = useState("");
  const [project, setProject] = useState("");
  const [board, setBoard] = useState(false);
  const [detailId, setDetailId] = useState("");
  const [returnView, setReturnView] = useState("radar");
  const [draft, setDraft] = useState({
    title: "",
    status: "Next",
    deadline: "",
    review: "",
    waitUntil: "",
    parent: "",
  });
  const [newDraft, setNewDraft] = useState({ title: "", level: "task", status: "Next", deadline: "", review: "", parent: "", waitUntil: "" });
  const [checked, setChecked] = useState({});
  const [actions, setActions] = useState({});
  const [mapOpen, setMapOpen] = useState(() => new Set());
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
  const mapGroups = useMemo(() => buildMapGroups(listed), [listed]);
  const projectEpics = projectTasks.filter((task) => task.type === "epic");
  const [epicFilter, setEpicFilter] = useState("");
  const filteredProjectTasks = projectTasks.filter((task) => {
    if (!epicFilter) return true;
    if (task.id === epicFilter) return true;
    const parent = parentId(task.parent);
    if (parent === epicFilter) return true;
    const story = byId.get(parent);
    return story && parentId(story.parent) === epicFilter;
  });

  // #region agent log
  useEffect(() => {
    const tables = document.querySelectorAll("table").length;
    const panels = document.querySelectorAll("[data-layout-panel]").length;
    fetch("http://127.0.0.1:7873/ingest/cff9df26-114e-4021-9c74-b251cb269805", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7e3b98" },
      body: JSON.stringify({
        sessionId: "7e3b98",
        runId: "post-fix",
        hypothesisId: "D",
        location: "App.jsx:view",
        message: "view layout metrics",
        data: { view, tables, panels, radarTile },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
  }, [view, radarTile, board, preview]);
  // #endregion

  function oidOf(task) {
    return oids[task.id] || task.expect_oid || "";
  }

  function openDetail(task) {
    setReturnView(view);
    setDetailId(task.id);
    setDraft({
      title: task.title || "",
      status: task.status || "Next",
      deadline: task.deadline || "",
      review: task.review_deadline || "",
      waitUntil: task.waitUntil || "",
      parent: parentId(task.parent),
    });
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
    if (draft.status && draft.status !== detail.status) patch.status = draft.status;
    if (draft.deadline !== (detail.deadline || "")) {
      patch.deadline = draft.deadline;
    } else if (draft.review !== (detail.review_deadline || "")) {
      patch.review_deadline = draft.review;
    }
    if (draft.waitUntil !== (detail.waitUntil || "")) patch.waitUntil = draft.waitUntil;
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

  function TaskLink({ task }) {
    return (
      <button type="button" className="text-left font-bold" onClick={() => openDetail(task)}>
        {labelOf(task)}
      </button>
    );
  }

  async function patchDate(task, field, value) {
    if (!api?.patch) return;
    const patch =
      field === "deadline"
        ? { deadline: value, ...(value ? { review_deadline: "" } : {}) }
        : { review_deadline: value };
    // #region agent log
    fetch("http://127.0.0.1:7873/ingest/cff9df26-114e-4021-9c74-b251cb269805", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7e3b98" },
      body: JSON.stringify({
        sessionId: "7e3b98",
        runId: "inline-edit",
        hypothesisId: "H2",
        location: "App.jsx:patchDate",
        message: "inline date patch",
        data: { id: task.id, field, value },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    const result = await api.patch({ path: task.path, patch, expect_oid: oidOf(task) });
    await openConflict(result, patch, task.path, task.id);
  }

  function InlineStatus({ task }) {
    return (
      <select
        className="rounded border border-[#444] bg-white px-2 py-0.5 text-xs"
        aria-label={`Status ${task.id}`}
        value={task.status || "Next"}
        onChange={(event) => {
          const status = event.target.value;
          // #region agent log
          fetch("http://127.0.0.1:7873/ingest/cff9df26-114e-4021-9c74-b251cb269805", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7e3b98" },
            body: JSON.stringify({
              sessionId: "7e3b98",
              runId: "inline-edit",
              hypothesisId: "H2",
              location: "App.jsx:InlineStatus",
              message: "inline status change",
              data: { id: task.id, from: task.status, to: status },
              timestamp: Date.now(),
            }),
          }).catch(() => {});
          // #endregion
          move(task, status);
        }}
      >
        {[...COLUMNS, "Done", "Cancelled"].map((status) => (
          <option key={status} value={status}>
            {status}
          </option>
        ))}
      </select>
    );
  }

  function InlineDate({ task, field }) {
    const value = field === "deadline" ? task.deadline || "" : task.review_deadline || "";
    const overdue = field === "deadline" && value && value < today;
    return (
      <input
        type="date"
        className={`w-[9.5rem] rounded border border-[#b0b2b6] bg-transparent px-1 py-0.5 text-sm ${
          overdue ? "font-bold text-[#b8002e]" : "text-[#5c5c5c]"
        }`}
        aria-label={`${field === "deadline" ? "Deadline" : "Review"} ${task.id}`}
        value={value}
        disabled={field === "review_deadline" && Boolean(task.deadline)}
        onChange={(event) => patchDate(task, field, event.target.value)}
      />
    );
  }

  function TaskTable({ rows, groupLabel, groupByProject = false }) {
    const groups = groupByProject
      ? [...rows.reduce((map, task) => {
          const key = task.project || "(bez projektu)";
          if (!map.has(key)) map.set(key, []);
          map.get(key).push(task);
          return map;
        }, new Map())]
      : [[null, rows]];
    // #region agent log
    if (groupByProject && groups.length) {
      const labels = groups
        .filter(([key]) => key)
        .map(([key, items]) => ({ raw: key, shown: `${projectLabel(key)} · ${items.length}` }));
      fetch("http://127.0.0.1:7873/ingest/cff9df26-114e-4021-9c74-b251cb269805", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7e3b98" },
        body: JSON.stringify({
          sessionId: "7e3b98",
          runId: "project-label-uppercase",
          hypothesisId: "H1",
          location: "App.jsx:TaskTable",
          message: "project group labels rendered",
          data: { labels, allUpper: labels.every((row) => row.shown === row.shown.toUpperCase()) },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
    }
    // #endregion
    return (
      <div data-layout-panel className={`${panelClass} overflow-x-auto`} aria-label="Seznam">
        <div className="flex flex-wrap items-center gap-2 border-b border-[#e2e2e2] px-4 py-3">
          {groupLabel && <span className="text-sm font-extrabold uppercase">{groupLabel}</span>}
          {groupByProject && <span className="text-sm text-[#5c5c5c]">· seskupeno podle projektu</span>}
          <span className="flex-1" />
          <span className="text-sm text-[#5c5c5c]">{rows.length} řádků</span>
        </div>
        <table className="w-full min-w-[820px] text-left text-sm">
          <thead>
            <tr className="text-xs uppercase text-[#5c5c5c]">
              <th className="p-3 font-bold">Task</th>
              <th className="p-2 font-bold">Parent</th>
              <th className="p-2 font-bold">Status</th>
              <th className="p-2 font-bold">Deadline</th>
              <th className="p-2 font-bold">Review</th>
              <th className="p-3 font-bold">Agent</th>
            </tr>
          </thead>
          <tbody>
            {groups.map(([projectKey, items]) => (
              <Fragment key={projectKey || "all"}>
                {projectKey && (
                  <tr className="bg-[#f3f3f3]">
                    <td
                      colSpan={6}
                      className="px-4 py-2 text-sm font-bold uppercase"
                      data-project-label={projectLabel(projectKey)}
                    >
                      {projectLabel(projectKey)} · {items.length}
                    </td>
                  </tr>
                )}
                {items.map((task) => (
                  <tr key={task.id} className="border-t border-[#eeeeee]">
                    <td className="p-3">
                      <TaskLink task={task} />
                    </td>
                    <td className="p-2 text-[#5c5c5c]">{parentId(task.parent) || "—"}</td>
                    <td className="p-2">
                      <InlineStatus task={task} />
                    </td>
                    <td className="p-2">
                      <InlineDate task={task} field="deadline" />
                    </td>
                    <td className="p-2">
                      <InlineDate task={task} field="review_deadline" />
                    </td>
                    <td className="p-3 text-xs text-[#5c5c5c]">{task.agent || "—"}</td>
                  </tr>
                ))}
              </Fragment>
            ))}
          </tbody>
        </table>
        <div className="border-t border-[#eeeeee] px-4 py-2.5 text-xs text-[#5c5c5c]">
          Klik na datum nebo status = inline úprava · klik na název = detail panel
        </div>
      </div>
    );
  }

  const issueRows = [
    ...new Map(
      classified.issues
        .filter((item) => item.rule !== "no_date")
        .map((item) => [item.id, item]),
    ).values(),
  ];

  const projectStories = filteredProjectTasks.filter((task) => task.type === "story");
  const projectStoryIds = new Set(projectStories.map((task) => task.id));
  const childrenOf = (id) => filteredProjectTasks.filter((task) => parentId(task.parent) === id);
  const projectOrphans = filteredProjectTasks.filter(
    (task) => task.type !== "story" && task.type !== "epic" && !projectStoryIds.has(parentId(task.parent)),
  );

  return (
    <div className="flex min-h-screen flex-col bg-[#fafafa] font-[Rubik,system-ui,sans-serif] text-[#444]">
      <nav className="flex flex-wrap items-center gap-2 bg-[#444444] px-8 py-2 text-[#fafafa]">
        <span className="mr-4 text-base font-black uppercase tracking-wide">Second Brain</span>
        {[
          ["map", "Mapa"],
          ["radar", "Radar"],
          ["project", "Projekt"],
          ["cleanup", "Úklid"],
        ].map(([id, name]) => (
          <button key={id} type="button" className={btnNav(view === id)} onClick={() => setView(id)}>
            {name}
          </button>
        ))}
        <span aria-hidden="true" className="mx-2 h-6 w-px bg-[#6b6b6b]" />
        <button type="button" className={btnNav(view === "issues")} onClick={() => setView("issues")}>
          Chybně zadané
        </button>
        <button type="button" className={btnNav(view === "new")} onClick={() => setView("new")}>
          Nový task
        </button>
        <label className="ml-auto flex items-center gap-2 text-sm">
          <input type="checkbox" checked={showPaused} onChange={(event) => setShowPaused(event.target.checked)} /> Zobrazit pauznuté
        </label>
        <input
          className={`${fieldClass} max-w-xs text-[#444]`}
          aria-label="Hledat"
          placeholder="ID, název, projekt…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </nav>

      <main className="mx-auto flex w-full max-w-[1360px] flex-1 flex-col gap-5 px-8 py-6">
        {view === "radar" && (
          <section aria-label="Radar" className="flex flex-col gap-6">
            <PageHeader title="Radar">
              <button type="button" className={btnPrimary} onClick={() => setView("new")}>
                + Nový
              </button>
            </PageHeader>
            <p className="w-full text-xs text-[#5c5c5c]">
              Snapshot z Brain · focus týden {isoWeek(today)} · {listed.length} otevřených · prošlý focus:{" "}
              {classified.radar.focus_stale.length}
            </p>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4" aria-label="Kategorie">
              {TILES.map(([key, name]) => {
                const count = key === "focus" ? `${classified.tiles.focus} / 10` : classified.tiles[key];
                const srCount = classified.tiles[key];
                return (
                  <button
                    key={key}
                    type="button"
                    className={
                      radarTile === key
                        ? "rounded-md border-2 border-[#e4003a] bg-white p-3.5 text-left"
                        : key === "errors"
                          ? "rounded-md border border-[#a11834] bg-white p-3.5 text-left"
                          : "rounded-md border border-[#b0b2b6] bg-white p-3.5 text-left"
                    }
                    onClick={() => setRadarTile(key)}
                  >
                    <span
                      className={`block text-xs font-bold uppercase ${
                        key === "errors" || key === "overdue" ? "text-[#b8002e]" : "text-[#5c5c5c]"
                      }`}
                    >
                      {key === "focus" ? `Focus ${isoWeek(today)}` : name}
                    </span>
                    <span className="block text-4xl font-black">{count}</span>
                    <span className="sr-only">
                      {key === "overdue" ? "Overdue" : name} {srCount}
                    </span>
                  </button>
                );
              })}
            </div>
            <TaskTable
              groupLabel={TILES.find(([key]) => key === radarTile)?.[1]}
              groupByProject
              rows={idsForTile(classified, radarTile)
                .map((id) => byId.get(id))
                .filter(Boolean)}
            />
          </section>
        )}

        {view === "issues" && (
          <section aria-label="Chybně zadané" className="flex flex-col gap-5">
            <PageHeader title={`Chybně zadané ${classified.tiles.errors}`} />
            <div data-layout-panel className={`${panelClass} overflow-x-auto`}>
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead>
                  <tr className="text-xs uppercase text-[#5c5c5c]">
                    <th className="p-3 font-bold">Task</th>
                    <th className="p-2 font-bold">Pravidla</th>
                    <th className="p-2 font-bold">Projekt</th>
                  </tr>
                </thead>
                <tbody>
                  {issueRows.map((item) => {
                    const task = byId.get(item.id);
                    const rules = classified.issues
                      .filter((issue) => issue.id === item.id && issue.rule !== "no_date")
                      .map((issue) => issue.rule)
                      .join(", ");
                    return (
                      <tr key={item.id} className="border-t border-[#eeeeee]">
                        <td className="p-3">
                          {task ? (
                            <TaskLink task={task} />
                          ) : (
                            <p>
                              {item.id} — {item.title}
                            </p>
                          )}
                        </td>
                        <td className="p-2 font-bold text-[#b8002e]">{rules}</td>
                        <td className="p-2 uppercase text-[#5c5c5c]">
                          {projectLabel(item.project || task?.project || "")}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {view === "map" && (
          <section aria-label="Mapa" className="flex flex-col gap-5">
            <PageHeader title="Mapa">
              <div role="group" aria-label="Zobrazení" className="inline-flex overflow-hidden rounded-md border border-[#444]">
                <span className="bg-[#444] px-4 py-3 font-bold text-[#fafafa]">Strom</span>
                <span className="bg-white px-4 py-3 text-[#5c5c5c]">Mindmapa (fáze 2)</span>
              </div>
            </PageHeader>
            <div className="flex flex-wrap gap-4 text-xs text-[#5c5c5c]">
              <span>
                <span className="mr-1 inline-block h-2.5 w-2.5 rounded-sm bg-[#a11834]" /> Doing
              </span>
              <span>
                <span className="mr-1 inline-block h-2.5 w-2.5 rounded-sm bg-[#444]" /> Next
              </span>
              <span>
                <span className="mr-1 inline-block h-2.5 w-2.5 rounded-sm bg-[#b0b2b6]" /> Waiting / Backlog
              </span>
              <span className="font-bold text-[#b8002e]">❗ overdue</span>
              <span className="font-bold text-[#b8002e]">⚠️ chybně zadané</span>
            </div>
            <div data-layout-panel className={`${panelClass} py-2`} aria-label="Strom">
              {mapGroups.map((group, index) => {
                const open = mapOpen.size === 0 ? index === 0 : mapOpen.has(group.slug);
                return (
                  <div key={group.slug} className="border-b border-[#eeeeee] last:border-b-0">
                    <button
                      type="button"
                      className="flex w-full items-center gap-3 px-4 py-2.5 text-left"
                      onClick={() => {
                        setMapOpen((prev) => {
                          const next = new Set(prev);
                          if (next.size === 0) {
                            mapGroups.forEach((item, i) => {
                              if (i === 0) next.add(item.slug);
                            });
                          }
                          if (next.has(group.slug)) next.delete(group.slug);
                          else next.add(group.slug);
                          return next;
                        });
                      }}
                    >
                      <span aria-hidden="true" className="w-4">
                        {open ? "▾" : "▸"}
                      </span>
                      <span className="flex-1 font-extrabold uppercase" data-project-label={projectLabel(group.slug)}>
                        {projectLabel(group.slug)}
                      </span>
                      <span className="text-sm text-[#5c5c5c]">
                        {group.epics.length} epiců · {group.open} otevřených
                      </span>
                    </button>
                    {open &&
                      group.epics.map(({ epic, stories, loose }) => (
                        <div key={epic.id}>
                          <button
                            type="button"
                            className="flex w-full items-center gap-3 px-4 py-2 pl-11 text-left"
                            onClick={() => openDetail(epic)}
                          >
                            <span className="flex-1 font-bold">{labelOf(epic)}</span>
                            <span className="text-sm text-[#5c5c5c]">{stories.length + loose.length} otevřených</span>
                          </button>
                          {stories.map((story) => (
                            <button
                              key={story.id}
                              type="button"
                              className="flex w-full items-center gap-3 px-4 py-1.5 pl-[76px] text-left text-sm"
                              onClick={() => openDetail(story)}
                            >
                              <span
                                className={`inline-block h-2.5 w-2.5 rounded-sm ${
                                  story.status === "Doing"
                                    ? "bg-[#a11834]"
                                    : story.status === "Next"
                                      ? "bg-[#444]"
                                      : "bg-[#b0b2b6]"
                                }`}
                              />
                              <span className="flex-1 font-bold">{labelOf(story)}</span>
                              {story.deadline && story.deadline < today && (
                                <span className="font-bold text-[#b8002e]">❗ {story.deadline}</span>
                              )}
                            </button>
                          ))}
                          {loose.map((task) => (
                            <button
                              key={task.id}
                              type="button"
                              className="flex w-full items-center gap-3 px-4 py-1.5 pl-[76px] text-left text-sm"
                              onClick={() => openDetail(task)}
                            >
                              <span className="inline-block h-2.5 w-2.5 rounded-sm bg-[#b0b2b6]" />
                              <span>{labelOf(task)}</span>
                            </button>
                          ))}
                        </div>
                      ))}
                    {open &&
                      [...group.orphanStories, ...group.orphanTasks].map((task) => (
                        <button
                          key={task.id}
                          type="button"
                          className="flex w-full items-center gap-3 px-4 py-2 pl-11 text-left text-sm"
                          onClick={() => openDetail(task)}
                        >
                          <span className="font-bold text-[#b8002e]">⚠️ {labelOf(task)}</span>
                        </button>
                      ))}
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {view === "project" && (
          <section aria-label="Projekt" className="flex flex-col gap-5">
            <div role="tablist" aria-label="Výběr projektu" className="flex flex-wrap items-end gap-2 border-b border-[#e2e2e2] pb-2">
              <label className={labelClass}>
                Projekt
                <select
                  className={fieldClass}
                  aria-label="Projekt v přehledu"
                  value={projectSlugValue}
                  onChange={(event) => {
                    setProject(event.target.value);
                    setEpicFilter("");
                  }}
                >
                  {activeProjects.map((item) => (
                    <option key={item.slug} value={item.slug}>
                      {projectLabel(item.slug)}
                    </option>
                  ))}
                </select>
              </label>
              {activeProjects.map((item) => (
                <button
                  key={item.slug}
                  type="button"
                  role="tab"
                  aria-selected={item.slug === projectSlugValue}
                  className={
                    item.slug === projectSlugValue
                      ? "rounded-md bg-[#a11834] px-3.5 py-2.5 text-sm font-bold uppercase text-white"
                      : "rounded-md px-3.5 py-2.5 text-sm uppercase"
                  }
                  onClick={() => {
                    setProject(item.slug);
                    setEpicFilter("");
                  }}
                >
                  {projectLabel(item.slug)} {listed.filter((task) => task.project === item.slug).length}
                </button>
              ))}
            </div>
            <PageHeader title={projectLabel(projectSlugValue) || "Projekt"}>
              <button type="button" className={btnPrimary} onClick={() => setView("new")}>
                + Nový v projektu
              </button>
            </PageHeader>
            <p className="text-sm text-[#5c5c5c]">
              {projectTasks.length} otevřených · {projectEpics.length} epiců
            </p>
            {projectEpics.length > 0 && (
              <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
                <button
                  type="button"
                  className={!epicFilter ? "rounded-md border-2 border-[#a11834] bg-white p-3.5 text-left" : `${panelClass} p-3.5 text-left`}
                  onClick={() => setEpicFilter("")}
                >
                  <div className="text-xs text-[#5c5c5c]">Vše</div>
                  <div className="font-extrabold">Celý projekt</div>
                </button>
                {projectEpics.map((epic) => (
                  <button
                    key={epic.id}
                    type="button"
                    className={
                      epicFilter === epic.id
                        ? "rounded-md border-2 border-[#a11834] bg-white p-3.5 text-left"
                        : `${panelClass} p-3.5 text-left`
                    }
                    onClick={() => setEpicFilter(epic.id)}
                  >
                    <div className="text-xs text-[#5c5c5c]">{epic.id}</div>
                    <div className="font-extrabold">{epic.title || epic.id}</div>
                  </button>
                ))}
              </div>
            )}
            <div className="flex flex-wrap items-center gap-3">
              <div role="group" aria-label="Zobrazení" className="inline-flex overflow-hidden rounded-md border border-[#444]">
                <button
                  type="button"
                  className={!board ? "bg-[#444] px-3.5 py-3 font-bold text-[#fafafa]" : "bg-white px-3.5 py-3"}
                  onClick={() => setBoard(false)}
                >
                  Seznam
                </button>
                <button
                  type="button"
                  className={board ? "bg-[#444] px-3.5 py-3 font-bold text-[#fafafa]" : "bg-white px-3.5 py-3"}
                  onClick={() => setBoard(true)}
                >
                  Kanban
                </button>
              </div>
            </div>
            {board ? (
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                {COLUMNS.map((status) => (
                  <div key={status} className="min-h-80 rounded-md bg-[#f1f1f1] p-2.5">
                    <div className="mb-2 flex items-center justify-between border-b-4 border-[#444] px-1 pb-2 text-xs font-extrabold uppercase">
                      <span role="columnheader">{status}</span>
                      <span className="text-[#5c5c5c]">
                        {filteredProjectTasks.filter((task) => task.status === status).length}
                      </span>
                    </div>
                    <div className="flex flex-col gap-2">
                      {filteredProjectTasks
                        .filter((task) => task.status === status)
                        .map((task) => (
                          <div key={task.id} className="rounded-md border border-[#e2e2e2] bg-white p-2.5">
                            <TaskLink task={task} />
                            <div className="mt-1 text-xs text-[#5c5c5c]">{task.deadline || task.review_deadline || "—"}</div>
                          </div>
                        ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div data-layout-panel className={panelClass} aria-label="Stories projektu">
                {filteredProjectTasks
                  .filter((task) => task.type === "epic")
                  .map((epic) => (
                    <div key={epic.id} className="flex flex-wrap items-center gap-3 border-b border-[#eeeeee] bg-[#faf3f4] px-4 py-3">
                      <span className="flex-1">
                        <TaskLink task={epic} />
                      </span>
                      <InlineStatus task={epic} />
                      <span className="text-sm text-[#5c5c5c]">{childrenOf(epic.id).length} otevřených pod epicem</span>
                    </div>
                  ))}
                {projectStories.map((story) => {
                  const kids = childrenOf(story.id);
                  return (
                    <div key={story.id} className="border-b border-[#eeeeee]">
                      <div className="flex flex-wrap items-center gap-3 px-4 py-3">
                        <span className="flex-1">
                          <TaskLink task={story} />
                        </span>
                        <InlineStatus task={story} />
                        <InlineDate task={story} field="deadline" />
                        <InlineDate task={story} field="review_deadline" />
                        <span className="text-sm text-[#5c5c5c]">{kids.length} tasků</span>
                      </div>
                      {kids.map((child) => (
                        <div
                          key={child.id}
                          className="flex flex-wrap items-center gap-3 border-t border-[#f3f3f3] py-2 pl-11 pr-4 text-sm"
                        >
                          <span className="flex-1">
                            <TaskLink task={child} />
                          </span>
                          <InlineStatus task={child} />
                          <InlineDate task={child} field="deadline" />
                          <InlineDate task={child} field="review_deadline" />
                        </div>
                      ))}
                    </div>
                  );
                })}
                {projectOrphans.map((task) => (
                  <div key={task.id} className="flex flex-wrap items-center gap-3 border-b border-[#eeeeee] px-4 py-3">
                    <span className="flex-1">
                      <TaskLink task={task} />
                    </span>
                      <InlineStatus task={task} />
                    <InlineDate task={task} field="deadline" />
                    <InlineDate task={task} field="review_deadline" />
                  </div>
                ))}
                {projectStories.length === 0 && projectOrphans.length === 0 && (
                  <TaskTable rows={filteredProjectTasks} />
                )}
              </div>
            )}
          </section>
        )}

        {view === "detail" && detail && (
          <section aria-label="Detail" data-layout-panel className={`${panelClass} mx-auto flex w-full max-w-xl flex-col gap-4 p-6`}>
            <div className="flex items-center justify-between gap-3 text-xs font-bold uppercase text-[#5c5c5c]">
              <span>
                {detail.type || "task"} · {projectLabel(detail.project || "")} · detail panel
              </span>
              <button type="button" className="min-h-11 min-w-11 text-xl" onClick={() => setView(returnView)} aria-label="Zavřít">
                ×
              </button>
            </div>
            <div className="text-sm font-bold">{detail.id}</div>
            <label className={labelClass}>
              Název
              <input className={fieldClass} aria-label="Název" value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className={labelClass}>
                Status
                <select
                  className={fieldClass}
                  aria-label="Status úkolu"
                  value={draft.status}
                  onChange={(event) => setDraft({ ...draft, status: event.target.value })}
                >
                  {[...COLUMNS, "Done", "Cancelled"].map((status) => (
                    <option key={status}>{status}</option>
                  ))}
                </select>
              </label>
              <label className={labelClass}>
                Wait until
                <input
                  type="date"
                  className={fieldClass}
                  aria-label="WaitUntil úkolu"
                  data-date-picker="waitUntil"
                  value={draft.waitUntil}
                  disabled={draft.status !== "Waiting"}
                  onChange={(event) => setDraft({ ...draft, waitUntil: event.target.value })}
                />
              </label>
              <label className={labelClass}>
                Deadline
                <input
                  type="date"
                  className={`${fieldClass} ${draft.deadline ? "border-2 border-[#a11834]" : ""}`}
                  aria-label="Deadline úkolu"
                  data-date-picker="deadline"
                  value={draft.deadline}
                  onChange={(event) => setDraft({ ...draft, deadline: event.target.value, review: event.target.value ? "" : draft.review })}
                />
              </label>
              <label className={labelClass}>
                Review date
                <input
                  type="date"
                  className={fieldClass}
                  aria-label="Review úkolu"
                  data-date-picker="review"
                  value={draft.review}
                  disabled={Boolean(draft.deadline)}
                  onChange={(event) => setDraft({ ...draft, review: event.target.value })}
                />
              </label>
            </div>
            {detail.type !== "epic" && (
              <label className={labelClass}>
                Parent
                <ParentSuggest
                  ariaLabel="Parent úkolu"
                  value={draft.parent}
                  onChange={(parent) => setDraft({ ...draft, parent })}
                  options={openTasks
                    .filter(
                      (task) =>
                        (showPaused || !paused.has(projectSlug(task))) &&
                        task.type === (detail.type === "story" ? "epic" : "story"),
                    )
                    .map((task) => ({ id: task.id, title: task.title || "", label: labelOf(task) }))}
                />
              </label>
            )}
            <div className="rounded-md bg-[#f3f3f3] p-3.5 text-sm">
              <div className="mb-1 text-xs font-extrabold uppercase">Náhled změn</div>
              {draft.title !== (detail.title || "") && (
                <div>
                  <b>title:</b> {detail.title || "—"} → {draft.title || "—"}
                </div>
              )}
              {draft.status !== detail.status && (
                <div>
                  <b>status:</b> {detail.status} → {draft.status}
                </div>
              )}
              {draft.deadline !== (detail.deadline || "") && (
                <div>
                  <b>deadline:</b> {detail.deadline || "—"} → {draft.deadline || "—"}
                </div>
              )}
              {draft.review !== (detail.review_deadline || "") && (
                <div>
                  <b>review_deadline:</b> {detail.review_deadline || "—"} → {draft.review || "—"}
                </div>
              )}
              {draft.parent !== parentId(detail.parent) && (
                <div>
                  <b>parent:</b> {parentId(detail.parent) || "—"} → {draft.parent || "—"}
                </div>
              )}
              {draft.title === (detail.title || "") &&
                draft.status === detail.status &&
                draft.deadline === (detail.deadline || "") &&
                draft.review === (detail.review_deadline || "") &&
                draft.parent === parentId(detail.parent) && <div className="text-[#5c5c5c]">Beze změny</div>}
            </div>
            <div className="flex flex-wrap gap-3">
              <button type="button" className={btnPrimary} onClick={saveDetail}>
                Uložit
              </button>
              <button type="button" className={btnGhost} onClick={() => setView(returnView)}>
                Zahodit
              </button>
              <button
                type="button"
                className={btnGhost}
                aria-label={`Focus ${detail.id}`}
                onClick={() => proposeFocus(detail)}
              >
                Focus
              </button>
            </div>
          </section>
        )}

        {view === "new" && (
          <section aria-label="Nový task" data-layout-panel className={`${panelClass} mx-auto flex w-full max-w-lg flex-col gap-4 p-6`}>
            <h2 className="text-2xl font-black uppercase">+ Nový</h2>
            <div role="radiogroup" aria-label="Úroveň nového tasku" className="inline-flex overflow-hidden rounded-md border border-[#444] self-start">
              {[
                ["epic", "Epic"],
                ["story", "Story"],
                ["task", "Task"],
              ].map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  role="radio"
                  aria-checked={newDraft.level === value}
                  className={
                    newDraft.level === value
                      ? "min-h-11 bg-[#444] px-4 font-bold text-[#fafafa]"
                      : "min-h-11 bg-white px-4 text-[#444]"
                  }
                  onClick={() => setNewDraft({ ...newDraft, level: value, parent: "" })}
                >
                  {label}
                </button>
              ))}
            </div>
            <label className="sr-only">
              Úroveň
              <select
                aria-label="Úroveň nového tasku select"
                value={newDraft.level}
                onChange={(event) => setNewDraft({ ...newDraft, level: event.target.value, parent: "" })}
              >
                <option value="epic">Epic</option>
                <option value="story">Story</option>
                <option value="task">Task</option>
              </select>
            </label>
            <label className={labelClass}>
              Projekt
              <select
                className={fieldClass}
                aria-label="Projekt nového tasku"
                value={projectSlugValue}
                onChange={(event) => setProject(event.target.value)}
              >
                {activeProjects.map((item) => (
                  <option key={item.slug} value={item.slug}>
                    {projectLabel(item.slug)}
                  </option>
                ))}
              </select>
            </label>
            <label className={labelClass}>
              Název nového
              <input
                className={fieldClass}
                aria-label="Název nového tasku"
                value={newDraft.title}
                onChange={(event) => setNewDraft({ ...newDraft, title: event.target.value })}
              />
            </label>
            <label className={labelClass}>
              Stav
              <select
                className={fieldClass}
                aria-label="Stav nového tasku"
                value={newDraft.status}
                onChange={(event) => setNewDraft({ ...newDraft, status: event.target.value })}
              >
                {COLUMNS.map((status) => (
                  <option key={status}>{status}</option>
                ))}
              </select>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className={labelClass}>
                Deadline nového
                <input
                  type="date"
                  className={fieldClass}
                  aria-label="Deadline nového tasku"
                  value={newDraft.deadline}
                  onChange={(event) =>
                    setNewDraft({
                      ...newDraft,
                      deadline: event.target.value,
                      review: event.target.value ? "" : newDraft.review,
                    })
                  }
                />
              </label>
              <label className={labelClass}>
                Review nového
                <input
                  type="date"
                  className={fieldClass}
                  aria-label="Review nového tasku"
                  value={newDraft.review}
                  disabled={Boolean(newDraft.deadline)}
                  onChange={(event) => setNewDraft({ ...newDraft, review: event.target.value })}
                />
              </label>
            </div>
            <label className={labelClass}>
              WaitUntil
              <input
                type="date"
                className={fieldClass}
                aria-label="WaitUntil nového tasku"
                value={newDraft.waitUntil}
                disabled={newDraft.status !== "Waiting"}
                onChange={(event) => setNewDraft({ ...newDraft, waitUntil: event.target.value })}
              />
            </label>
            {newDraft.level !== "epic" && (
              <label className={labelClass}>
                Parent
                <ParentSuggest
                  ariaLabel="Parent nového tasku"
                  value={newDraft.parent}
                  onChange={(parent) => setNewDraft({ ...newDraft, parent })}
                  options={openTasks
                    .filter(
                      (task) =>
                        (showPaused || !paused.has(projectSlug(task))) &&
                        task.type === (newDraft.level === "story" ? "epic" : "story"),
                    )
                    .map((task) => ({ id: task.id, title: task.title || "", label: labelOf(task) }))}
                />
              </label>
            )}
            <button type="button" className={btnPrimary} onClick={createTask}>
              Založit
            </button>
          </section>
        )}

        {view === "cleanup" && (
          <section aria-label="Úklid" className="flex flex-col gap-5 pb-24">
            <PageHeader title="Úklid vaultu" />
            <p className="max-w-3xl text-[#5c5c5c]">
              Projdi tasky bez termínu po projektech. U každého rozhodni: zrušit, hotovo, nebo ponechat. Nic se nezapíše bez
              náhledu.
            </p>
            <div className="flex flex-wrap gap-2" aria-label="Postup">
              <div className="rounded-md border-2 border-[#a11834] bg-white px-3 py-2 text-sm font-bold">
                Rozhodnout · {listed.length} bez filtru
              </div>
              <div className="rounded-md border border-[#e2e2e2] bg-white px-3 py-2 text-sm">Náhled změn</div>
              <div className="rounded-md border border-[#e2e2e2] bg-white px-3 py-2 text-sm">Zápis po dávkách</div>
            </div>
            <div className="flex flex-wrap items-start gap-5">
              <aside data-layout-panel className={`${panelClass} flex w-full max-w-[300px] flex-col gap-3 p-4`}>
                <h2 className="text-xs font-bold uppercase tracking-wide">Filtr</h2>
                <p className="text-xs font-normal text-[#5c5c5c]">
                  Hledání nahoře v liště filtruje i tento seznam. Signály k rozhodnutí jsou jen nápověda.
                </p>
              </aside>
              <div role="region" aria-label="Seznam úklidu" data-layout-panel className={`${panelClass} min-w-0 flex-1 overflow-x-auto`}>
                <div className="flex flex-wrap items-center gap-3 border-b border-[#e2e2e2] px-4 py-3">
                  <strong className="flex-1 text-sm">Tasky k rozhodnutí · {listed.length}</strong>
                  <span className="text-sm text-[#5c5c5c]">
                    {Object.values(checked).filter(Boolean).length} vybráno
                  </span>
                </div>
                <table className="w-full min-w-[760px] text-left text-sm">
                  <thead>
                    <tr className="text-[11px] uppercase tracking-wide text-[#5c5c5c]">
                      <th className="p-2.5 font-bold">✓</th>
                      <th className="p-2.5 font-bold">ID</th>
                      <th className="p-2.5 font-bold">Název</th>
                      <th className="p-2.5 font-bold">Status</th>
                      <th className="p-2.5 font-bold">Rozhodnutí</th>
                    </tr>
                  </thead>
                  <tbody>
                    {listed.map((task) => (
                      <tr key={task.id} className={`border-t border-[#e2e2e2] ${checked[task.id] ? "bg-[#faf3f4]" : ""}`}>
                        <td className="p-2.5">
                          <input
                            type="checkbox"
                            aria-label={`Vybrat ${labelOf(task)}`}
                            checked={Boolean(checked[task.id])}
                            onChange={(event) => setChecked({ ...checked, [task.id]: event.target.checked })}
                          />
                        </td>
                        <td className="p-2.5 font-bold whitespace-nowrap tabular-nums">{task.id}</td>
                        <td className="p-2.5">{task.title || task.id}</td>
                        <td className="p-2.5">
                          <StatusPill status={task.status} />
                        </td>
                        <td className="p-2.5">
                          <div className="flex flex-wrap gap-1" role="group" aria-label={`Akce ${task.id}`}>
                            {(offerKeep(task)
                              ? [
                                  ["cancelled", "Zrušit"],
                                  ["done", "Hotovo"],
                                  ["keep", "Ponechat"],
                                ]
                              : [
                                  ["cancelled", "Zrušit"],
                                  ["done", "Hotovo"],
                                ]
                            ).map(([value, label]) => {
                              const current = actions[task.id] || (offerKeep(task) ? "keep" : "done");
                              const on = checked[task.id] && current === value;
                              return (
                                <button
                                  key={value}
                                  type="button"
                                  className={
                                    on
                                      ? "min-h-8 rounded border border-[#a11834] bg-[#a11834] px-2 text-xs font-bold text-white"
                                      : "min-h-8 rounded border border-[#e2e2e2] bg-white px-2 text-xs text-[#444]"
                                  }
                                  onClick={() => {
                                    setChecked({ ...checked, [task.id]: true });
                                    setActions({ ...actions, [task.id]: value });
                                  }}
                                >
                                  {label}
                                </button>
                              );
                            })}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="sticky bottom-0 z-20 flex flex-wrap items-center gap-3 rounded-md bg-[#444444] px-4 py-3 text-[#fafafa]">
              <span className="min-w-[220px] flex-1 text-sm">
                {Object.values(checked).filter(Boolean).length} vybráno · nic se nezapíše bez náhledu
              </span>
              <button type="button" className={btnPrimary} onClick={openPreview}>
                Náhled
              </button>
            </div>
            {preview && (
              <div role="region" aria-label="Náhled úklidu" data-layout-panel className={`${panelClass} flex flex-col gap-3 p-4`}>
                <h2 className="font-extrabold">Náhled změn</h2>
                <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                  <label className={labelClass}>
                    Termín pro výběr
                    <input type="date" className={fieldClass} aria-label="Termín pro výběr" value={selectionDate} onChange={(event) => applySharedDate(event.target.value)} />
                  </label>
                  <label className={labelClass}>
                    Od
                    <input type="date" className={fieldClass} aria-label="Od" value={from} onChange={(event) => setFrom(event.target.value)} />
                  </label>
                  <label className={labelClass}>
                    Do
                    <input type="date" className={fieldClass} aria-label="Do" value={to} onChange={(event) => setTo(event.target.value)} />
                  </label>
                  <label className={labelClass}>
                    Max
                    <input className={fieldClass} aria-label="Max za den" value={maxPerDay} onChange={(event) => setMaxPerDay(event.target.value)} />
                  </label>
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" aria-label="Přeskočit nepracovní dny" checked={skipNonWork} onChange={(event) => setSkipNonWork(event.target.checked)} />
                  Přeskočit nepracovní dny
                </label>
                <label className={labelClass}>
                  Pořadí
                  <select className={fieldClass} aria-label="Pořadí rozprostření" value={sortMode} onChange={(event) => setSortMode(event.target.value)}>
                    <option value="project_epic">projekt a epic</option>
                    <option value="priority">priorita</option>
                    <option value="age">stáří</option>
                  </select>
                </label>
                {preview
                  .filter((row) => !dropped.has(row.id))
                  .map((row) => (
                    <div key={row.id} className="flex flex-wrap items-center gap-2 border-t border-[#eeeeee] py-2">
                      <label className="flex items-center gap-2">
                        <input type="checkbox" aria-label={`Náhled ${row.id} — ${row.title}`} checked disabled={row.locked} readOnly />
                        {row.id} — {row.title}
                      </label>
                      <span>{row.resulting === "cancelled" ? "Zrušeno" : row.resulting === "done" ? "Hotovo" : "Ponechat"}</span>
                      {row.locked && (
                        <select
                          className={fieldClass}
                          aria-label={`Náhled akce ${row.id}`}
                          value={row.resulting === "cancelled" ? "cancelled" : "done"}
                          onChange={(event) => setPreviewAction(row.id, event.target.value)}
                        >
                          <option value="done">Hotovo</option>
                          <option value="cancelled">Zrušit</option>
                        </select>
                      )}
                      {row.resulting === "keep" && (
                        <input
                          className={fieldClass}
                          aria-label={`Termín ${row.id}`}
                          value={rowDate(row) || ""}
                          onChange={(event) => setRowDate(row.id, event.target.value)}
                        />
                      )}
                    </div>
                  ))}
                {counts &&
                  [...counts.entries()].sort().map(([day, count]) => (
                    <p key={day}>
                      Obsazenost {day}: {count}
                    </p>
                  ))}
                {preview.length > 80 && <p>Rodina je nad 80. Odeber předka.</p>}
                <div className="flex flex-wrap gap-3">
                  <button type="button" className={btnPrimary} disabled={!sendAllowed || preview.length > 80} onClick={submitCleanup}>
                    Uložit
                  </button>
                  <button type="button" className={btnGhost} onClick={() => setPreview(null)}>
                    Zavřít náhled
                  </button>
                </div>
                {cleanupResult?.written && (
                  <p>
                    Uloženo {cleanupResult.written.count}: {cleanupResult.written.ids.join(", ")}
                  </p>
                )}
                {cleanupResult?.lines?.map((line) => (
                  <p key={line}>{line}</p>
                ))}
              </div>
            )}
          </section>
        )}
      </main>

      {dialog?.kind === "q9" && (
        <div role="dialog" aria-label="Neshoda verze" className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div data-layout-panel className={`${panelClass} flex max-w-lg flex-col gap-2 p-5`}>
            <p>U tebe: {dialog.yours.title}</p>
            <p>Ve vaultu: {dialog.vault.title}</p>
            <p>status: {dialog.yours.status} / {dialog.vault.status}</p>
            <p>deadline: {dialog.yours.deadline} / {dialog.vault.deadline}</p>
            <p>review: {dialog.yours.review_deadline} / {dialog.vault.review_deadline}</p>
            <p>waitUntil: {dialog.yours.waitUntil} / {dialog.vault.waitUntil}</p>
            <p>parent: {dialog.yours.parent} / {dialog.vault.parent}</p>
            <div className="mt-2 flex gap-2">
              <button
                type="button"
                className={btnPrimary}
                onClick={() => {
                  api.patch({ path: dialog.path, patch: dialog.patch, expect_oid: dialog.oid });
                  setDialog(null);
                }}
              >
                Přesto uložit
              </button>
              <button type="button" className={btnGhost} onClick={() => setDialog(null)}>
                Upravit
              </button>
            </div>
          </div>
        </div>
      )}

      {dialog?.kind === "deadline_order" && (
        <div role="dialog" aria-label="Pořadí termínů" className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div data-layout-panel className={`${panelClass} max-w-lg p-5`}>
            <p>{dialog.text}</p>
            <button type="button" className={`${btnGhost} mt-3`} onClick={() => setDialog(null)}>
              Zavřít
            </button>
          </div>
        </div>
      )}

      {dialog?.kind === "doing" && (
        <div role="dialog" aria-label="Doplň deadline" className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div data-layout-panel className={`${panelClass} flex flex-col gap-3 p-5`}>
            <input type="date" className={fieldClass} aria-label="Datum deadline" value={doingDate} onChange={(event) => setDoingDate(event.target.value)} />
            <button type="button" className={btnPrimary} onClick={confirmDoing}>
              Potvrdit
            </button>
          </div>
        </div>
      )}

      {dialog?.kind === "waiting" && (
        <div role="dialog" aria-label="Doplň waitUntil" className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div data-layout-panel className={`${panelClass} flex flex-col gap-3 p-5`}>
            <input type="date" className={fieldClass} aria-label="Datum waitUntil" value={waitDate} onChange={(event) => setWaitDate(event.target.value)} />
            <button type="button" className={btnPrimary} onClick={confirmWaiting}>
              Potvrdit
            </button>
          </div>
        </div>
      )}

      {dialog?.kind === "focus" && (
        <div role="dialog" aria-label="Focus" className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div data-layout-panel className={`${panelClass} flex flex-col gap-3 p-5`}>
            {dialog.text && <p>{dialog.text}</p>}
            {dialog.proposalId && (
              <button type="button" className={btnPrimary} onClick={applyFocus}>
                Použít focus
              </button>
            )}
            <button type="button" className={btnGhost} onClick={() => setDialog(null)}>
              Zavřít
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
