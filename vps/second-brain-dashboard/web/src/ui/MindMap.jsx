import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { panelClass, projectLabel } from "./chrome.jsx";

const CANVAS_W = 1040;
const CANVAS_H = 720;
const CARD_HALF_W = 100;
const CARD_HALF_H = 48;
const CENTER_HALF = 90;
const CENTER_W = 180;
const CENTER_H = 168;
const FIT_LINE_HEIGHT = 1.15;
const FIT_MAX_LINES = 3;

/** @type {HTMLCanvasElement | false | null} */
let measureCanvas = null;

function measureTextWidth(text, fontSizePx) {
  const jsdom =
    typeof navigator !== "undefined" && /jsdom/i.test(navigator.userAgent || "");
  if (!jsdom && measureCanvas !== false && typeof document !== "undefined") {
    try {
      if (!measureCanvas) measureCanvas = document.createElement("canvas");
      const ctx = measureCanvas.getContext("2d");
      if (ctx && typeof ctx.measureText === "function") {
        ctx.font = `800 ${fontSizePx}px Rubik, system-ui, sans-serif`;
        const width = ctx.measureText(text).width;
        if (Number.isFinite(width) && width > 0) return width;
      }
      measureCanvas = false;
    } catch {
      measureCanvas = false;
    }
  }
  // jsdom / bez canvas — přibližná šířka bold
  return String(text).length * fontSizePx * 0.62;
}

/** Greedy word-wrap; null = nevejde se do maxLines / šířky. */
export function wrapLabelLines(text, fontSizePx, maxWidth, maxLines = FIT_MAX_LINES) {
  const words = String(text || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (!words.length) return [""];
  const lines = [];
  let current = "";
  for (const word of words) {
    const trial = current ? `${current} ${word}` : word;
    if (measureTextWidth(trial, fontSizePx) <= maxWidth) {
      current = trial;
      continue;
    }
    if (current) lines.push(current);
    if (lines.length >= maxLines) return null;
    if (measureTextWidth(word, fontSizePx) > maxWidth) return null;
    current = word;
  }
  if (current) lines.push(current);
  if (lines.length > maxLines) return null;
  return lines;
}

/** Největší font (px), který se vejde do boxu max. ve `maxLines` řádcích. */
export function fitLabelLayout(text, { maxWidth, maxHeight, maxLines = FIT_MAX_LINES, minPx = 11, maxPx = 42 } = {}) {
  const raw = String(text || "").trim() || " ";
  let lo = minPx;
  let hi = maxPx;
  let best = { fontSize: minPx, lines: wrapLabelLines(raw, minPx, maxWidth, maxLines) || [raw] };
  while (lo <= hi) {
    const mid = Math.floor((lo + hi) / 2);
    const lines = wrapLabelLines(raw, mid, maxWidth, maxLines);
    const heightOk = lines && lines.length * mid * FIT_LINE_HEIGHT <= maxHeight + 0.5;
    if (lines && heightOk) {
      best = { fontSize: mid, lines };
      lo = mid + 1;
    } else {
      hi = mid - 1;
    }
  }
  return best;
}

function FitCenterLabel({ text, uppercase }) {
  const ref = useRef(null);
  const display = uppercase ? String(text || "").toUpperCase() : String(text || "");
  const [layout, setLayout] = useState(() => ({ fontSize: 14, lines: [display] }));

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const width = Math.max(el.clientWidth, 40);
    const height = Math.max(el.clientHeight, 24);
    setLayout(fitLabelLayout(display, { maxWidth: width, maxHeight: height }));
  }, [display]);

  return (
    <span
      ref={ref}
      data-fit-label
      className="flex min-h-0 w-full flex-1 flex-col items-center justify-center overflow-hidden px-0.5"
      style={{
        fontSize: layout.fontSize,
        fontWeight: 800,
        lineHeight: FIT_LINE_HEIGHT,
      }}
    >
      {layout.lines.map((line, index) => (
        <span key={`${index}-${line}`} className="block max-w-full text-center">
          {line}
        </span>
      ))}
    </span>
  );
}

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

function findTaskInGroup(group, taskId) {
  if (!group || !taskId) return null;
  return allTasks(group).find((task) => task.id === taskId) || null;
}

/** Resolve stored frames (taskId) against current groups. */
export function resolveNavStack(stack, groups) {
  const list = groups || [];
  const out = [];
  for (const frame of stack || []) {
    if (frame.kind === "project") {
      if (list.some((group) => group.slug === frame.slug)) out.push({ kind: "project", slug: frame.slug });
      continue;
    }
    const group = list.find((item) => item.slug === frame.slug);
    const task = findTaskInGroup(group, frame.taskId || frame.task?.id);
    if (!group || !task) break;
    out.push({ kind: frame.kind, slug: frame.slug, taskId: task.id, task });
  }
  return out;
}

export function fitZoomForNodes(nodes, vpW, vpH, cx, cy) {
  let minX = cx - CENTER_HALF;
  let maxX = cx + CENTER_HALF;
  let minY = cy - CENTER_HALF;
  let maxY = cy + CENTER_HALF;
  for (const node of nodes || []) {
    minX = Math.min(minX, node.x - CARD_HALF_W);
    maxX = Math.max(maxX, node.x + CARD_HALF_W);
    minY = Math.min(minY, node.y - CARD_HALF_H);
    maxY = Math.max(maxY, node.y + CARD_HALF_H);
  }
  const contentW = Math.max(maxX - minX, 1);
  const contentH = Math.max(maxY - minY, 1);
  const pad = 0.88;
  const raw = Math.min(vpW / contentW, vpH / contentH) * pad;
  return Math.max(0.28, Math.min(1.35, raw));
}

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
      id: "",
      flags: { overdue: false, bad: false },
      canGoBack: false,
      titleUpper: true,
    };
  }
  const top = stack[stack.length - 1];
  const group = (groups || []).find((item) => item.slug === top.slug);
  if (top.kind === "project" && group) {
    const flags = flagsForTasks(allTasks(group), today, issueIds);
    return {
      kind: "project",
      title: projectLabel(group.slug),
      id: group.slug,
      flags,
      canGoBack: true,
      titleUpper: true,
    };
  }
  if ((top.kind === "epic" || top.kind === "story") && top.task) {
    const flags = flagsForTask(top.task, today, issueIds);
    return {
      kind: top.kind,
      title: top.task.title || top.task.id,
      id: top.task.id,
      flags,
      canGoBack: true,
      titleUpper: false,
    };
  }
  return {
    kind: "vault",
    title: "VAULT",
    id: "",
    flags: { overdue: false, bad: false },
    canGoBack: false,
    titleUpper: true,
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

function toStoredFrame(frame) {
  if (frame.kind === "project") return { kind: "project", slug: frame.slug };
  return { kind: frame.kind, slug: frame.slug, taskId: frame.taskId || frame.task?.id };
}

export function MindMap({ groups, today, issueIds, onOpen, navStack, onNavStackChange }) {
  const [localStack, setLocalStack] = useState([]);
  const controlled = Array.isArray(navStack) && typeof onNavStackChange === "function";
  const rawStack = controlled ? navStack : localStack;
  const setRawStack = controlled ? onNavStackChange : setLocalStack;

  const stack = useMemo(() => resolveNavStack(rawStack, groups), [rawStack, groups]);

  function setStack(next) {
    const value = typeof next === "function" ? next(stack) : next;
    setRawStack((value || []).map(toStoredFrame));
  }

  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const drag = useRef(null);
  const viewportRef = useRef(null);
  const didInitialFit = useRef(false);
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

  function applyFit(nodeList) {
    const el = viewportRef.current;
    if (!el) return;
    const { width, height } = el.getBoundingClientRect();
    if (width < 40 || height < 40) return;
    setPan({ x: 0, y: 0 });
    setZoom(fitZoomForNodes(nodeList, width, height, cx, cy));
  }

  useEffect(() => {
    if (didInitialFit.current) return;
    if (!nodes.length && !(groups || []).length) return;
    didInitialFit.current = true;
    applyFit(nodes);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- one-shot initial fit
  }, [nodes, groups]);

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
        { kind: "epic", slug, taskId: item.task.id, task: item.task },
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
            { kind: "story", slug, taskId: item.task.id, task: item.task },
          ];
        }
        return [
          { kind: "project", slug },
          { kind: "story", slug, taskId: item.task.id, task: item.task },
        ];
      });
    }
  }

  function goBack() {
    if (stack.length === 0) return;
    setPan({ x: 0, y: 0 });
    setStack((prev) => prev.slice(0, -1));
  }

  function handleReset() {
    const vaultNodes = ringItems([], groups).map((item, index, list) => {
      const n = Math.max(list.length, 1);
      const angle = (Math.PI * 2 * index) / n - Math.PI / 2;
      return { ...item, ...polar(cx, cy, ringRadius(list.length), angle) };
    });
    setStack([]);
    applyFit(vaultNodes);
  }

  const transform = `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`;
  const zoomLabel = `${Math.round(zoom * 100)} %`;

  return (
    <div data-layout-panel className={`${panelClass} relative overflow-hidden`} aria-label="Mindmapa">
      <div className="flex flex-wrap items-center gap-3 border-b border-[#e2e2e2] px-4 py-2 text-xs text-[#5c5c5c]">
        <span>
          Zoom: kolečko · posun: tažení podkladu · klik na dlaždici = do středu · klik na střed = zpět
        </span>
        <span className="flex-1" />
        <span aria-live="polite">{zoomLabel}</span>
        <button type="button" className="rounded border border-[#444] px-2 py-1" onClick={() => setZoom(1)}>
          100 %
        </button>
        <button type="button" className="rounded border border-[#444] px-2 py-1" onClick={handleReset}>
          Reset
        </button>
      </div>
      <div
        ref={viewportRef}
        className="relative h-[720px] cursor-grab overflow-hidden active:cursor-grabbing"
        onWheel={(event) => {
          event.preventDefault();
          setZoom((value) => Math.min(1.8, Math.max(0.28, value - event.deltaY * 0.001)));
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
            className="pointer-events-none absolute inset-0 overflow-visible"
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
          <div className="absolute inset-0 overflow-visible" style={{ width: CANVAS_W, height: CANVAS_H }}>
            <button
              type="button"
              data-mind-node
              data-mind-kind="center"
              aria-label={center.canGoBack ? `Zpět z ${center.title}` : center.title}
              className={`absolute flex h-[168px] w-[180px] -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center rounded-[40px] px-3 py-2 text-center text-[#fafafa] shadow-sm ${
                center.canGoBack ? "cursor-pointer bg-[#444] hover:bg-[#333]" : "cursor-default bg-[#444]"
              } ${center.flags.overdue || center.flags.bad ? "ring-2 ring-[#b8002e] ring-offset-2" : ""}`}
              style={{ left: cx, top: cy, width: CENTER_W, height: CENTER_H }}
              onClick={goBack}
              disabled={!center.canGoBack}
            >
              {center.id && center.kind !== "project" && (
                <span className="shrink-0 text-[10px] font-semibold tracking-wide opacity-75">{center.id}</span>
              )}
              <FitCenterLabel text={center.title} uppercase={center.titleUpper} />
              {center.canGoBack && (
                <span className="mt-0.5 shrink-0 text-[10px] font-normal opacity-80">zpět</span>
              )}
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
        <div>Reset = celá mapa do viewportu</div>
      </div>
    </div>
  );
}
