export const fieldClass =
  "w-full rounded-md border border-[#b0b2b6] bg-white px-3 py-2 font-[Rubik,system-ui,sans-serif] text-[#444]";
export const labelClass = "flex flex-col gap-1 text-xs font-bold";
export const panelClass = "rounded-md border border-[#e2e2e2] bg-white";
export const btnPrimary =
  "min-h-11 rounded-md bg-[#e4003a] px-5 py-3 font-extrabold text-white";
export const btnGhost =
  "min-h-11 rounded-md border border-[#444] bg-white px-5 py-3 font-bold text-[#444]";
export const btnNav = (on) =>
  on ? "rounded-md bg-[#a11834] px-3.5 py-2.5 font-bold" : "rounded-md px-3.5 py-2.5 font-medium";

/** Display-only project name (slug stays kebab-case in data/value). */
export function projectLabel(slug) {
  if (!slug) return "";
  return String(slug).toUpperCase();
}

export function StatusPill({ status }) {
  return (
    <span className="inline-block rounded border border-[#444] px-2 py-0.5 text-xs">
      {status || "—"}
    </span>
  );
}

export function PageHeader({ title, children }) {
  return (
    <header className="flex flex-wrap items-center gap-3">
      <h1 className="flex-1 text-3xl font-black uppercase">{title}</h1>
      {children}
    </header>
  );
}

export function buildMapGroups(tasks) {
  const groups = new Map();
  for (const task of tasks) {
    const slug = task.project || "(bez projektu)";
    if (!groups.has(slug)) groups.set(slug, []);
    groups.get(slug).push(task);
  }
  return [...groups.entries()].map(([slug, items]) => {
    const byId = new Map(items.map((item) => [item.id, item]));
    const epics = items.filter((item) => item.type === "epic");
    const stories = items.filter((item) => item.type === "story");
    const rest = items.filter((item) => item.type !== "epic" && item.type !== "story");
    const childrenOf = (id) =>
      items.filter((item) => {
        const parent = String(item.parent || "").replace(/\[\[|\]\]/g, "").split(/\s+[—–-]/)[0].trim();
        return parent === id;
      });
    return {
      slug,
      open: items.length,
      epics: epics.map((epic) => ({
        epic,
        stories: childrenOf(epic.id).filter((item) => item.type === "story"),
        loose: childrenOf(epic.id).filter((item) => item.type !== "story"),
      })),
      orphanStories: stories.filter((story) => {
        const parent = String(story.parent || "").replace(/\[\[|\]\]/g, "").split(/\s+[—–-]/)[0].trim();
        return !parent || !byId.has(parent);
      }),
      orphanTasks: rest.filter((task) => {
        const parent = String(task.parent || "").replace(/\[\[|\]\]/g, "").split(/\s+[—–-]/)[0].trim();
        return !parent || !byId.has(parent);
      }),
    };
  });
}
