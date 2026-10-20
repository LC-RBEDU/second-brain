const OPEN = new Set(["Doing", "Next", "Backlog", "Waiting"]);
const TERMINAL = { done: "Done", cancelled: "Cancelled" };

function parentId(value) {
  if (!value) return "";
  const text = String(value).trim();
  const linked = /\[\[([^\]|]+)/.exec(text);
  return (linked ? linked[1] : text).split(/\s+[—–-]/)[0].trim();
}

function index(tasks) {
  return new Map((tasks || []).filter((task) => task.id).map((task) => [task.id, task]));
}

function childrenByParent(tasks) {
  const out = new Map();
  for (const task of tasks || []) {
    if (!OPEN.has(task.status)) continue;
    const parent = parentId(task.parent);
    if (!parent) continue;
    const list = out.get(parent) || [];
    list.push(task);
    out.set(parent, list);
  }
  return out;
}

export function hasOpenDescendant(id, tasks) {
  const children = childrenByParent(tasks);
  const stack = [...(children.get(id) || [])];
  const seen = new Set();
  while (stack.length) {
    const task = stack.pop();
    if (seen.has(task.id)) continue;
    seen.add(task.id);
    if (OPEN.has(task.status)) return true;
  }
  return false;
}

export function kanbanPatch(task, nextStatus, tasks) {
  if (hasOpenDescendant(task.id, tasks)) return null;
  return { status: nextStatus };
}

export function offerKeep(task) {
  if (!task || task.deadline) return false;
  if (task.status === "Doing") return false;
  if (task.status === "Waiting" && !task.waitUntil) return false;
  return OPEN.has(task.status);
}

export function closingPreview(rootId, action, tasks) {
  const byId = index(tasks);
  const children = childrenByParent(tasks);
  const root = byId.get(rootId);
  if (!root || !OPEN.has(root.status)) return [];
  const rows = [];
  const stack = [rootId];
  const seen = new Set();
  while (stack.length) {
    const id = stack.pop();
    if (seen.has(id)) continue;
    seen.add(id);
    const node = byId.get(id);
    if (!node || !OPEN.has(node.status)) continue;
    rows.push({
      id,
      title: node.title || "",
      parent: parentId(node.parent),
      project: node.project,
      action: id === rootId ? action : action,
      direct: id === rootId,
      locked: id !== rootId,
      needsDay: false,
      review_deadline: node.review_deadline || "",
    });
    for (const child of children.get(id) || []) stack.push(child.id);
  }
  return rows;
}

export function resolveCloser(rows) {
  const byId = new Map(rows.map((row) => [row.id, row]));
  function nearestClose(id) {
    const seen = new Set([id]);
    let parent = byId.get(id)?.parent;
    while (parent && !seen.has(parent)) {
      seen.add(parent);
      const ancestor = byId.get(parent);
      if (!ancestor) return null;
      if (ancestor.action === "done" || ancestor.action === "cancelled") return ancestor.action;
      parent = ancestor.parent;
    }
    return null;
  }
  return rows.map((row) => {
    if (row.direct && (row.action === "done" || row.action === "cancelled")) {
      return { ...row, resulting: row.action, needsDay: false };
    }
    if (row.action === "keep") {
      const closer = nearestClose(row.id);
      if (closer) {
        return { ...row, resulting: closer, locked: true, needsDay: false, yielded: true };
      }
    }
    return { ...row, resulting: row.action, needsDay: row.action === "keep" };
  });
}

export function rowPatch(row) {
  if (row.resulting === "done" || row.resulting === "cancelled") {
    return { status: TERMINAL[row.resulting] };
  }
  if (row.resulting === "keep") {
    return { review_deadline: row.date };
  }
  return null;
}
