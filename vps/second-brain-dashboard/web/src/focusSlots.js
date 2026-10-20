const OPEN = new Set(["Doing", "Next", "Backlog", "Waiting"]);
const INELIGIBLE = new Set(["Done", "Cancelled", "Waiting", "Backlog"]);

export function pragueToday(now) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Prague",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(now));
}

export function isoWeek(iso) {
  const [year, month, day] = iso.slice(0, 10).split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  const weekday = date.getUTCDay() || 7;
  date.setUTCDate(date.getUTCDate() + 4 - weekday);
  const start = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
  const week = Math.ceil(((date - start) / 86400000 + 1) / 7);
  return `${date.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
}

export function parseFocus(value) {
  const match = /^(\d{4})-W(\d{1,2})$/.exec(String(value || "").trim());
  if (!match) return null;
  const week = Number(match[2]);
  if (week < 1 || week > 53) return null;
  return `${match[1]}-W${String(week).padStart(2, "0")}`;
}

export function projectSlug(task) {
  return String(task.project || task.slug || "");
}

export function pausedSlugs(projects) {
  const out = new Set();
  for (const project of projects || []) {
    const status = String(project.status ?? "active").trim().toLowerCase();
    if (status !== "active" && status !== "") out.add(project.slug);
  }
  return out;
}

function parentId(value) {
  if (!value) return "";
  const text = String(value).trim();
  const linked = /\[\[([^\]|]+)/.exec(text);
  return (linked ? linked[1] : text).split(/\s+[—–-]/)[0].trim();
}

export function countFocusSlots(tasks, today, projects) {
  const paused = pausedSlugs(projects);
  const visible = (tasks || []).filter((task) => !paused.has(projectSlug(task)));
  const hiddenStories = new Set();
  for (const task of visible) {
    if (task.type !== "task" || !OPEN.has(task.status)) continue;
    const parent = parentId(task.parent);
    if (parent) hiddenStories.add(parent);
  }
  const week = isoWeek(today);
  let count = 0;
  for (const task of visible) {
    if (task.type === "epic") continue;
    if (INELIGIBLE.has(task.status)) continue;
    if (hiddenStories.has(task.id)) continue;
    if (parseFocus(task.focus) === week) count += 1;
  }
  return count;
}
