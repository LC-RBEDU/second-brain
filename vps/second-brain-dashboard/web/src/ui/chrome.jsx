import { useEffect, useRef, useState } from "react";

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

/** Custom parent picker — native <datalist> mispositions under centered panels in Chromium. */
export function ParentSuggest({ value, onChange, options, ariaLabel }) {
  const [open, setOpen] = useState(false);
  const inputRef = useRef(null);
  const listRef = useRef(null);
  const query = String(value || "").trim().toLowerCase();
  const filtered = (options || [])
    .filter((opt) => {
      if (!query) return true;
      const id = String(opt.id || "").toLowerCase();
      const label = String(opt.label || "").toLowerCase();
      return id.includes(query) || label.includes(query);
    })
    .slice(0, 40);

  useEffect(() => {
    if (!open || !inputRef.current || !listRef.current) return;
    const input = inputRef.current.getBoundingClientRect();
    const list = listRef.current.getBoundingClientRect();
  }, [open, filtered.length, value]);

  return (
    <div className="relative">
      <input
        ref={inputRef}
        className={fieldClass}
        aria-label={ariaLabel}
        aria-expanded={open}
        aria-autocomplete="list"
        autoComplete="off"
        value={value}
        onChange={(event) => {
          onChange(event.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => {
          window.setTimeout(() => setOpen(false), 120);
        }}
      />
      {open && filtered.length > 0 && (
        <ul
          ref={listRef}
          role="listbox"
          data-parent-suggest="1"
          className="absolute left-0 right-0 z-30 mt-1 max-h-56 overflow-auto rounded-md border border-[#444] bg-white text-[#444] shadow-md"
        >
          {filtered.map((opt) => (
            <li key={opt.id} role="presentation">
              <button
                type="button"
                role="option"
                className="block w-full px-3 py-2 text-left text-sm hover:bg-[#f3f3f3]"
                onMouseDown={(event) => {
                  event.preventDefault();
                  onChange(opt.id);
                  setOpen(false);
                }}
              >
                <span className="font-bold">{opt.id}</span>
                <span className="text-[#5c5c5c]"> — {opt.title || opt.label || ""}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
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
