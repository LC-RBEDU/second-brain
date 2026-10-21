import { countFocusSlots, isoWeek, pragueToday } from "./focusSlots.js";

const OPEN = new Set(["Doing", "Next", "Backlog", "Waiting"]);
const ALLOWED = new Set(["Doing", "Next", "Backlog", "Waiting", "Done", "Cancelled"]);
const ID_TYPE = { E: "epic", S: "story", T: "task" };
const SKIP_PARSE = new Set(["parent_closed", "parent_not_found"]);

function addDays(iso, days) {
  const date = new Date(`${iso.slice(0, 10)}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

function parentId(value) {
  if (!value) return "";
  const text = String(value).trim();
  const linked = /\[\[([^\]|]+)/.exec(text);
  return (linked ? linked[1] : text).split(/\s+[—–-]/)[0].trim();
}

export function visibleTasks(tasks) {
  return (tasks || []).filter((task) => {
    if (!task) return false;
    if (String(task.path || "").startsWith("07-ARCHIV/")) return false;
    return task.status !== "Done" && task.status !== "Cancelled";
  });
}

/** Lidské vysvětlivky kódu pravidel (Chybně zadané / Stale dlaždice). */
export const RULE_HELP = {
  stale: "Next nebo Doing — pole updated starší než 30 dní (nebo chybí pohyb).",
  stale_unknown: "Next nebo Doing bez data updated — stáří nejde spočítat.",
  title_markup: "Název obsahuje markup ([[, *, →) — do title to nepatří.",
  title_long: "Název delší než 100 znaků.",
  epic_empty: "Epic bez otevřeného potomka (prázdný kontejner).",
  doing_no_deadline: "Status Doing bez hard deadlinu.",
  no_date: "Next/Backlog bez deadline i review_deadline.",
  waiting_no_waituntil: "Waiting bez waitUntil.",
  parent_missing_or_closed: "Parent chybí, je zavřený, nebo není ve snapshotu.",
  parent_bad_type: "Špatný typ parentu (story→epic, task→story).",
  epic_with_parent: "Epic má parent — epic musí být kořen.",
  story_no_epic: "Story v hierarchickém projektu bez epic parentu.",
  id_type_mismatch: "Písmeno v ID (E/S/T) nesedí s type ve frontmatter.",
  focus_stale: "focus je na starší ISO týden než aktuální.",
  bad_status: "Status mimo Doing/Next/Backlog/Waiting/Done/Cancelled.",
};

export function ruleHelp(rule) {
  if (!rule) return "";
  if (RULE_HELP[rule]) return RULE_HELP[rule];
  if (String(rule).startsWith("parse_")) {
    return `Chyba parsování vault souboru (${String(rule).slice(6)}).`;
  }
  return "Kontrolní pravidlo klasifikace dashboardu.";
}

function hierarchySlugs(projects) {
  const slugs = new Set();
  for (const project of projects || []) {
    if (project.hierarchy === true) slugs.add(project.slug);
  }
  return slugs;
}

export function classify(exp, opts = {}) {
  const today = opts.today || pragueToday(opts.now || Date.now());
  const soonEnd = addDays(today, opts.dueSoonDays ?? 7);
  const staleBefore = addDays(today, -(opts.staleDays ?? 30));
  const titleMax = opts.titleMax ?? 100;
  const focusWeek = isoWeek(today);
  const hier = hierarchySlugs(opts.projects);
  const tasks = visibleTasks(exp?.tasks);
  const byId = new Map(tasks.filter((task) => task.id).map((task) => [task.id, task]));
  const openChildren = new Map();
  for (const task of tasks) {
    const parent = parentId(task.parent);
    if (parent && OPEN.has(task.status)) {
      openChildren.set(parent, (openChildren.get(parent) || 0) + 1);
    }
  }

  const radar = {
    overdue: [],
    to_decide: [],
    due_soon: [],
    waiting_overdue: [],
    doing: [],
    focus_week: [],
    focus_stale: [],
    no_date: [],
  };
  const issues = [];

  function issue(task, severity, rule, reason) {
    issues.push({
      id: task.id || "(bez ID)",
      title: task.title || "",
      path: task.path,
      project: task.project,
      severity,
      rule,
      reason,
    });
  }

  for (const task of tasks) {
    for (const reason of task.parse_errors || []) {
      if (SKIP_PARSE.has(reason)) continue;
      issue(task, "error", `parse_${reason}`, reason);
    }
    if (!ALLOWED.has(task.status)) {
      issue(task, "error", "bad_status", task.status || "");
    }
    if (!OPEN.has(task.status)) continue;

    const parent = parentId(task.parent);
    if (task.deadline && task.deadline < today) radar.overdue.push(task.id);
    else if (
      task.status !== "Waiting" &&
      !task.deadline &&
      task.review_deadline &&
      task.review_deadline < today
    ) {
      radar.to_decide.push(task.id);
    }
    if (task.deadline && task.deadline >= today && task.deadline <= soonEnd) {
      radar.due_soon.push(task.id);
    }
    if (task.status === "Waiting" && task.waitUntil && task.waitUntil < today) {
      radar.waiting_overdue.push(task.id);
    }
    if (task.status === "Doing") radar.doing.push(task.id);
    const focus = task.focus || "";
    if (focus && focus === (exp.focus_week || focusWeek)) radar.focus_week.push(task.id);
    if (focus && focus < (exp.focus_week || focusWeek)) radar.focus_stale.push(task.id);

    if (task.status === "Doing" && !task.deadline) {
      issue(task, "error", "doing_no_deadline", "Doing bez deadlinu");
    }
    if ((task.status === "Next" || task.status === "Backlog") && !task.deadline && !task.review_deadline) {
      issue(task, "error", "no_date", "Bez termínu");
      radar.no_date.push(task.id);
    }
    if (task.status === "Waiting" && !task.waitUntil) {
      issue(task, "error", "waiting_no_waituntil", "Waiting bez waitUntil");
    }
    if (parent) {
      const found = byId.get(parent);
      if (!found || !OPEN.has(found.status)) {
        issue(task, "error", "parent_missing_or_closed", parent);
      } else {
        const ok =
          (task.type === "story" && found.type === "epic") ||
          (task.type === "task" && found.type === "story");
        if (!ok) issue(task, "error", "parent_bad_type", found.id);
      }
    }
    if (task.type === "epic" && parent) issue(task, "error", "epic_with_parent", parent);
    if (task.type === "story" && !parent && hier.has(task.project)) {
      issue(task, "error", "story_no_epic", task.project);
    }
    const idMatch = /^[A-Z]+-([EST])\d/.exec(task.id || "");
    if (idMatch && ID_TYPE[idMatch[1]] !== task.type) {
      issue(task, "error", "id_type_mismatch", task.id);
    }
    if (focus && focus < focusWeek) issue(task, "error", "focus_stale", focus);

    if (task.type === "epic" && !openChildren.get(task.id)) {
      issue(task, "hygiene", "epic_empty", task.id);
    }
    if ((task.title || "").length > titleMax) issue(task, "hygiene", "title_long", task.title.length);
    if (/\[\[|\*|→/.test(task.title || "")) issue(task, "hygiene", "title_markup", task.id);
    if (task.status === "Next" || task.status === "Doing") {
      const updated = task.updated ? String(task.updated).slice(0, 10) : "";
      if (!updated) issue(task, "hygiene", "stale_unknown", task.id);
      else if (updated < staleBefore) issue(task, "hygiene", "stale", updated);
    }
  }

  const errorIds = new Set(
    issues.filter((item) => item.severity === "error" && item.rule !== "no_date").map((item) => item.id),
  );
  const staleIds = new Set(issues.filter((item) => item.rule === "stale").map((item) => item.id));
  const tiles = {
    overdue: radar.overdue.length,
    to_decide: radar.to_decide.length,
    due_soon: radar.due_soon.length,
    waiting_overdue: radar.waiting_overdue.length,
    doing: radar.doing.length,
    focus: countFocusSlots(tasks, today, opts.projects),
    no_date: radar.no_date.length,
    errors: errorIds.size,
    stale: staleIds.size,
  };
  return { today, focusWeek, radar, issues, tiles, tasks };
}
