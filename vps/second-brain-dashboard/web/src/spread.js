const FIXED = ["01-01", "05-01", "05-08", "07-05", "07-06", "09-28", "10-28", "11-17", "12-24", "12-25", "12-26"];

export function addDays(iso, days) {
  const date = new Date(`${iso.slice(0, 10)}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

function easterSunday(year) {
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31);
  const day = ((h + l - 7 * m + 114) % 31) + 1;
  return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

export function isNonWorkDay(iso) {
  const date = new Date(`${iso.slice(0, 10)}T00:00:00Z`);
  const weekday = date.getUTCDay();
  if (weekday === 0 || weekday === 6) return true;
  const monthDay = iso.slice(5, 10);
  if (FIXED.includes(monthDay)) return true;
  const year = Number(iso.slice(0, 4));
  const sunday = easterSunday(year);
  return iso.slice(0, 10) === addDays(sunday, -2) || iso.slice(0, 10) === addDays(sunday, 1);
}

function parentId(value) {
  if (!value) return "";
  const text = String(value).trim();
  const linked = /\[\[([^\]|]+)/.exec(text);
  return (linked ? linked[1] : text).split(/\s+[—–-]/)[0].trim();
}

function epicId(task, byId) {
  if (task.type === "epic") return task.id || "";
  const seen = new Set();
  let current = task;
  while (current && !seen.has(current.id)) {
    seen.add(current.id);
    const parent = parentId(current.parent);
    if (!parent) return "";
    const next = byId.get(parent);
    if (!next) return "";
    if (next.type === "epic") return next.id;
    current = next;
  }
  return "";
}

function updatedKey(task) {
  return task.updated ? String(task.updated).slice(0, 10) : "9999-99-99";
}

function compareText(left, right) {
  if (left < right) return -1;
  if (left > right) return 1;
  return 0;
}

export function sortQueue(queue, mode, tasks) {
  const byId = new Map((tasks || queue).map((task) => [task.id, task]));
  const rows = [...queue];
  rows.sort((left, right) => {
    if (mode === "priority") {
      const leftEmpty = left.priority_score === "" || left.priority_score == null;
      const rightEmpty = right.priority_score === "" || right.priority_score == null;
      if (leftEmpty !== rightEmpty) return leftEmpty ? 1 : -1;
      if (!leftEmpty && Number(left.priority_score) !== Number(right.priority_score)) {
        return Number(right.priority_score) - Number(left.priority_score);
      }
    } else if (mode === "project_epic") {
      const byProject = compareText(left.project || "", right.project || "");
      if (byProject) return byProject;
      const byEpic = compareText(epicId(left, byId), epicId(right, byId));
      if (byEpic) return byEpic;
    }
    const byUpdated = compareText(updatedKey(left), updatedKey(right));
    if (byUpdated) return byUpdated;
    return compareText(left.id || "", right.id || "");
  });
  return rows;
}

export function baseDay(task) {
  if (!task || task.status === "Done" || task.status === "Cancelled") return null;
  if (String(task.path || "").startsWith("07-ARCHIV/")) return null;
  if (task.deadline) return String(task.deadline).slice(0, 10);
  if (task.review_deadline) return String(task.review_deadline).slice(0, 10);
  return null;
}

export function occupancy(tasks, preview = new Map()) {
  const counts = new Map();
  for (const task of tasks || []) {
    const row = preview.get(task.id);
    let day = baseDay(task);
    if (row) {
      if (row.resulting === "done" || row.resulting === "cancelled") day = null;
      else if (row.date) day = row.date;
      else if (row.dateDeleted) day = null;
    }
    if (!day) continue;
    counts.set(day, (counts.get(day) || 0) + 1);
  }
  return counts;
}

export function assignDays(queue, { from, to, maxPerDay = 8, skipNonWork = false, taken = new Map() } = {}) {
  const used = new Map(taken);
  let cursor = from;
  return queue.map((row) => {
    if (!from || !to || from > to || maxPerDay < 1) return { id: row.id, date: null };
    while (cursor && cursor <= to) {
      const full = (used.get(cursor) || 0) >= maxPerDay;
      if ((!skipNonWork || !isNonWorkDay(cursor)) && !full) break;
      cursor = addDays(cursor, 1);
    }
    if (!cursor || cursor > to) return { id: row.id, date: null };
    used.set(cursor, (used.get(cursor) || 0) + 1);
    const date = cursor;
    if ((used.get(cursor) || 0) >= maxPerDay) cursor = addDays(cursor, 1);
    return { id: row.id, date };
  });
}

export function canSend({ queue = [], from, to, maxPerDay = 8, pending = 0 } = {}) {
  if (pending > 0) return false;
  if (queue.length === 0) return true;
  if (!from || !to || from > to || maxPerDay < 1) return false;
  return queue.every((row) => row.date);
}

export function keepDate(review) {
  return review ? { date: review, own: true, dateDeleted: false } : { date: null, own: false, dateDeleted: false };
}

export function overwriteDate(date) {
  return { date, own: true, dateDeleted: false, manual: true };
}

export function deleteDate() {
  return { date: null, own: false, dateDeleted: true };
}

export function applySelection(state, selection) {
  if (state.own && state.date) return state;
  if (!selection) return state;
  return { ...state, date: selection, fromSelection: true };
}
