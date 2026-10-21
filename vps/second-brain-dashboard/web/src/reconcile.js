/** Local post-save reconcile — merge Brain PATCH results into export without re-export (F2). */

const TERMINAL = new Set(["Done", "Cancelled"]);

/**
 * @param {object|null|undefined} exportData
 * @param {Array<{ id: string, patch?: object, oid?: string, task?: object }>} updates
 * @returns {object}
 */
export function reconcileExport(exportData, updates) {
  const base = exportData && typeof exportData === "object" ? exportData : { tasks: [] };
  const tasks = Array.isArray(base.tasks) ? [...base.tasks] : [];
  const byId = new Map(tasks.map((t, i) => [String(t.id), i]));

  for (const upd of updates || []) {
    if (!upd || upd.id == null) continue;
    const id = String(upd.id);
    const idx = byId.get(id);
    const patch = upd.patch && typeof upd.patch === "object" ? upd.patch : {};

    if (upd.task && typeof upd.task === "object") {
      // create / full replace row
      const row = { ...upd.task, id };
      if (upd.oid) row.oid = upd.oid;
      if (TERMINAL.has(String(row.status || ""))) {
        if (idx != null) {
          tasks.splice(idx, 1);
          byId.delete(id);
          // rebuild indices after splice
          for (let i = 0; i < tasks.length; i++) byId.set(String(tasks[i].id), i);
        }
      } else if (idx != null) {
        tasks[idx] = { ...tasks[idx], ...row };
      } else {
        byId.set(id, tasks.length);
        tasks.push(row);
      }
      continue;
    }

    if (idx == null) continue;
    const next = { ...tasks[idx], ...patch };
    if (upd.oid) next.oid = upd.oid;
    if (TERMINAL.has(String(next.status || ""))) {
      tasks.splice(idx, 1);
      byId.delete(id);
      for (let i = 0; i < tasks.length; i++) byId.set(String(tasks[i].id), i);
    } else {
      tasks[idx] = next;
    }
  }

  return { ...base, tasks };
}
