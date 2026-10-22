import { useMemo, useRef, useState } from "react";
import { panelClass, projectLabel } from "./chrome.jsx";

const CANVAS_W = 1040;
const CANVAS_H = 720;

function parentId(value) {
  return String(value || "")
    .replace(/\[\[|\]\]/g, "")
    .split(/\s+[—–-]/)[0]
    .trim();
}

function allTasks(group) {
  if (Array.isArray(group.items) && group.items.length) return group.items;
  const rows = [];
  for (const { epic, stories, loose } of group.epics) {
    rows.push(epic, ...stories, ...loose);
  }
  rows.push(...group.orphanStories, ...group.orphanTasks);
  return rows;
}

function childrenOf(group, id) {
  return allTasks(group).filter((task) => parentId(task.parent) === id && task.id !== id);
}

function flagsForTasks(tasks, today, issueIds) {
  let overdue = false;
  let bad = false;
  for (const task of tasks) {
    if (issueIds.has(task.id)) bad = true;
    if (task.deadline && task.deadline < today) overdue = true;
  }
  return { overdue, bad };
}

function flagsForTask(task, today, issueIds) {
  return {
    overdue: Boolean(task.deadline && task.deadline < today),
    bad: issueIds.has(task.id),
  };
}

function polar(cx, cy, radius, angle) {
  return {
    x: cx + Math.cos(angle) * radius,
    y: cy + Math.sin(angle) * radius,
  };
}

function ringRadius(count) {
  return Math.max(240, 80 + count * 28);
}

/** @typedef {{ kind: 'project', slug: string } | { kind: 'epic' | 'story', slug: string, task: object }} NavFrame */

function ringItems(stack, groups) {
  if (stack.length === 0) {
    return (groups || []).map((group) => ({
      kind: "project",
      key: `project:${group.slug}`,
      group,
    }));
  }

  const top = stack[stack.length - 1];
  const group = (groups || []).find((item) => item.slug === top.slug);
  if (!group) return [];

  if (top.kind === "project") {
    if (group.epics.length > 0) {
      return [
        ...group.epics.map(({ epic, stories, loose }) => ({
          kind: "epic",
          key: `epic:${epic.id}`,
          task: epic,
          openCount: stories.length + loose.length,
          group,
        })),
        ...group.orphanStories.map((task) => ({
          kind: "story",
          key: `story:${task.id}`,
          task,
          openCount: childrenOf(group, task.id).length,
          group,
        })),
        ...group.orphanTasks.map((task) => ({
          kind: "task",
          key: `task:${task.id}`,
          task,
          group,
        })),
      ];
    }
    return [
      ...group.orphanStories.map((task) => ({
        kind: "story",
        key: `story:${task.id}`,
        task,
        openCount: childrenOf(group, task.id).length,
        group,
      })),
      ...group.orphanTasks.map((task) => ({
        kind: "task",
        key: `task:${task.id}`,
        task,
        group,
      })),
    ];
  }

  if (top.kind === "epic") {
    const entry = group.epics.find((item) => item.epic.id === top.task.id);
    if (!entry) return [];
    return [
      ...entry.stories.map((task) => ({
        kind: "story",
        key: `story:${task.id}`,
        task,
        openCount: childrenOf(group, task.id).length,
        group,
      })),
      ...entry.loose.map((task) => ({
        kind: "task",
        key: `task:${task.id}`,
        task,
        group,
      })),
    ];
  }

  if (top.kind === "story") {
    return childrenOf(group, top.task.id).map((task) => ({
      kind: "task",
      key: `task:${task.id}`,
      task,
      group,
    }));
  }

  return [];
}

function centerMeta(stack, groups, today, issueIds) {
  if (stack.length === 0) {
    return {
      kind: "vault",
      title: "VAULT",
      subtitle: "projekty",
      flags: { overdue: false, bad: false },
      canGoBack: false,
    };
  }
  const top = stack[stack.length - 1];
  const group = (groups || []).find((item) => item.slug === top.slug);
  if (top.kind === "project" && group) {
    const flags = flagsForTasks(allTasks(group), today, issueIds);
    return {
      kind: "project",
      title: projectLabel(group.slug),
      subtitle: `${group.epics.length} epiců · ${group.open}`,
      slug: group.slug,
      flags,
      canGoBack: true,
    };
  }
  if ((top.kind === "epic" || top.kind === "story") && top.task) {
    const flags = flagsForTask(top.task, today, issueIds);
    const kids = group ? childrenOf(group, top.task.id) : [];
    const openCount =
      top.kind === "epic" && group
        ? (group.epics.find((item) => item.epic.id === top.task.id)?.stories.length || 0) +
          (group.epics.find((item) => item.epic.id === top.task.id)?.loose.length || 0)
        : kids.length;
    return {
      kind: top.kind,
      title: top.task.title || top.task.id,
      subtitle: `${top.task.id} · ${openCount} otevřených`,
      flags,
      canGoBack: true,
    };
  }
  return {
    kind: "vault",
    title: "VAULT",
    subtitle: "projekty",
    flags: { overdue: false, bad: false },
    canGoBack: false,
  };
}

function NodeCard({ item, today, issueIds, style, onClick, dashed }) {
  const isProject = item.kind === "project";
  const task = item.task;
  const flags = isProject
    ? flagsForTasks(allTasks(item.group), today, issueIds)
    : flagsForTask(task, today, issueIds);
  const alert = flags.overdue || flags.bad;
  const title = isProject ? projectLabel(item.group.slug) : task.title || task.id;
  const eyebrow = isProject ? item.group.slug : task.id;
  const meta = isProject
    ? `${item.group.epics.length} epiců · ${item.group.open}`
    : item.kind === "task"
      ? task.status || "task"
      : `${item.openCount ?? 0} otevřených`;

  return (
    <button
      type="button"
      data-mind-node
      data-mind-kind={item.kind}
      className={`absolute w-[200px] -translate-x-1/2 -translate-y-1/2 rounded-md bg-white p-2.5 text-left text-sm shadow-sm ${
        alert ? "border-2 border-[#b8002e]" : "border border-[#e2e2e2]"
      } ${dashed ? "border-dashed" : ""}`}
      style={style}
      onClick={onClick}
    >
      <div className="flex gap-2">
        {(flags.overdue || flags.bad) && (
          <div className="flex flex-col text-lg leading-none">
            {flags.overdue && <span aria-label="overdue">❗</span>}
            {flags.bad && <span aria-label="chybně zadané">⚠️</span>}
          </div>
        )}
        <div className="min-w-0 flex-1">
          <div className="text-[11px] text-[#5c5c5c]">{eyebrow}</div>
          <div className={`font-bold ${isProject ? "uppercase" : ""}`}>{title}</div>
          <div className={`text-xs ${alert ? "font-bold text-[#b8002e]" : "text-[#5c5c5c]"}`}>{meta}</div>
        </div>
      </div>
    </button>
  );
}

export function MindMap({ groups, today, issueIds, onOpen }) {
  /** @type {[NavFrame[], function]} */
  const [stack, setStack] = useState([]);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const drag = useRef(null);
  const cx = CANVAS_W / 2;
  const cy = CANVAS_H / 2;

  const ring = useMemo(() => ringItems(stack, groups), [stack, groups]);
  const center = useMemo(
    () => centerMeta(stack, groups, today, issueIds),
    [stack, groups, today, issueIds],
  );

  const nodes = useMemo(() => {
    const n = Math.max(ring.length, 1);
    const radius = ringRadius(ring.length);
    return ring.map((item, index) => {
      const angle = (Math.PI * 2 * index) / n - Math.PI / 2;
      const pos = polar(cx, cy, radius, angle);
      return { ...item, ...pos, angle };
    });
  }, [ring, cx, cy]);

  function drillTo(item) {
    setPan({ x: 0, y: 0 });
    if (item.kind === "project") {
      setStack([{ kind: "project", slug: item.group.slug }]);
      return;
    }
    if (item.kind === "task") {
      onOpen?.(item.task);
      return;
    }
    const slug = item.group.slug;
    if (item.kind === "epic") {
      setStack([
        { kind: "project", slug },
        { kind: "epic", slug, task: item.task },
      ]);
      return;
    }
    if (item.kind === "story") {
      setStack((prev) => {
        const epicFrame = prev.find((frame) => frame.kind === "epic" && frame.slug === slug);
        if (epicFrame) {
          return [
            { kind: "project", slug },
            epicFrame,
            { kind: "story", slug, task: item.task },
          ];
        }
        return [
          { kind: "project", slug },
          { kind: "story", slug, task: item.task },
        ];
      });
    }
  }

  function goBack() {
    if (stack.length === 0) return;
    setPan({ x: 0, y: 0 });
    setStack((prev) => prev.slice(0, -1));
  }

  const transform = `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`;

  return (
    <div data-layout-panel className={`${panelClass} relative overflow-hidden`} aria-label="Mindmapa">
      <div className="flex flex-wrap items-center gap-3 border-b border-[#e2e2e2] px-4 py-2 text-xs text-[#5c5c5c]">
        <span>
          Zoom: kolečko · posun: tažení podkladu · klik na dlaždici = do středu · klik na střed = zpět
        </span>
        <span className="flex-1" />
        <button type="button" className="rounded border border-[#444] px-2 py-1" onClick={() => setZoom(1)}>
          100 %
        </button>
        <button
          type="button"
          className="rounded border border-[#444] px-2 py-1"
          onClick={() => {
            setPan({ x: 0, y: 0 });
            setZoom(1);
            setStack([]);
          }}
        >
          Reset
        </button>
      </div>
      <div
        className="relative h-[720px] cursor-grab overflow-hidden active:cursor-grabbing"
        onWheel={(event) => {
          event.preventDefault();
          setZoom((value) => Math.min(1.8, Math.max(0.55, value - event.deltaY * 0.001)));
        }}
        onPointerDown={(event) => {
          if (event.target.closest("[data-mind-node]")) return;
          drag.current = { x: event.clientX - pan.x, y: event.clientY - pan.y };
          event.currentTarget.setPointerCapture(event.pointerId);
        }}
        onPointerMove={(event) => {
          if (!drag.current) return;
          setPan({ x: event.clientX - drag.current.x, y: event.clientY - drag.current.y });
        }}
        onPointerUp={() => {
          drag.current = null;
        }}
      >
        {/* Jeden logický canvas — SVG i HTML v stejném px prostoru (oprava spojnic). */}
        <div
          className="absolute left-1/2 top-1/2"
          style={{
            width: CANVAS_W,
            height: CANVAS_H,
            marginLeft: -CANVAS_W / 2,
            marginTop: -CANVAS_H / 2,
            transform,
            transformOrigin: "center center",
          }}
        >
          <svg
            width={CANVAS_W}
            height={CANVAS_H}
            className="pointer-events-none absolute inset-0"
            aria-hidden="true"
          >
            {nodes.map((node) => (
              <line
                key={`line-${node.key}`}
                x1={cx}
                y1={cy}
                x2={node.x}
                y2={node.y}
                stroke="#b0b2b6"
                strokeWidth="2"
              />
            ))}
          </svg>
          <div className="absolute inset-0" style={{ width: CANVAS_W, height: CANVAS_H }}>
            <button
              type="button"
              data-mind-node
              data-mind-kind="center"
              aria-label={center.canGoBack ? `Zpět z ${center.title}` : center.title}
              className={`absolute flex h-[88px] w-[88px] -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center rounded-full px-2 text-center text-[11px] font-extrabold leading-tight text-[#fafafa] shadow-sm ${
                center.canGoBack ? "cursor-pointer bg-[#444] hover:bg-[#333]" : "cursor-default bg-[#444]"
              } ${center.flags.overdue || center.flags.bad ? "ring-2 ring-[#b8002e] ring-offset-2" : ""}`}
              style={{ left: cx, top: cy }}
              onClick={goBack}
              disabled={!center.canGoBack}
            >
              <span className="line-clamp-2 uppercase">{center.title}</span>
              {center.canGoBack && <span className="mt-0.5 text-[9px] font-normal opacity-80">zpět</span>}
            </button>
            {nodes.map((node) => (
              <NodeCard
                key={node.key}
                item={node}
                today={today}
                issueIds={issueIds}
                style={{ left: node.x, top: node.y }}
                onClick={() => drillTo(node)}
              />
            ))}
          </div>
        </div>
      </div>
      <div className="absolute bottom-3 left-3 rounded-md border border-[#e2e2e2] bg-white px-3.5 py-2.5 text-xs text-[#5c5c5c]">
        <div className="mb-1 font-bold uppercase text-[#444]">Legenda</div>
        <div>
          <b className="text-[#b8002e]">Červený rámeček</b> = něco k řešení
        </div>
        <div>❗ overdue · ⚠️ chybně zadané</div>
        <div>Klik na dlaždici → střed · klik na střed → o úroveň výš</div>
      </div>
    </div>
  );
}
