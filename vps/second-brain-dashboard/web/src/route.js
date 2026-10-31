/** Top-level dashboard pages that survive refresh via `location.hash`. */
export const ROUTE_VIEWS = new Set(["radar", "map", "project", "cleanup", "issues", "new", "detail"]);

/**
 * Parse `#map`, `#project/finance`, `#detail/F-T175`.
 * @param {string} [hash]
 * @returns {{ view: string, project: string, detailId: string }}
 */
export function parseRoute(hash = "") {
  const raw = String(hash || "").replace(/^#/, "").trim();
  if (!raw) return { view: "radar", project: "", detailId: "" };
  const [head, ...rest] = raw.split("/");
  const view = ROUTE_VIEWS.has(head) ? head : "radar";
  const tail = rest.join("/").trim();
  if (view === "project") return { view, project: decodeURIComponent(tail), detailId: "" };
  if (view === "detail") return { view, project: "", detailId: decodeURIComponent(tail) };
  return { view, project: "", detailId: "" };
}

/**
 * @param {{ view: string, project?: string, detailId?: string }} state
 * @returns {string} hash without leading `#`
 */
export function serializeRoute(state) {
  const view = ROUTE_VIEWS.has(state?.view) ? state.view : "radar";
  if (view === "project" && state?.project) {
    return `project/${encodeURIComponent(String(state.project))}`;
  }
  if (view === "detail" && state?.detailId) {
    return `detail/${encodeURIComponent(String(state.detailId))}`;
  }
  return view;
}

/** @param {string} nextHash without `#` */
export function applyRouteHash(nextHash, { replace = true } = {}) {
  if (typeof window === "undefined" || !window.location) return;
  const target = `#${nextHash || "radar"}`;
  if (window.location.hash === target) return;
  if (replace && typeof window.history?.replaceState === "function") {
    window.history.replaceState(null, "", target);
  } else {
    window.location.hash = target;
  }
}
