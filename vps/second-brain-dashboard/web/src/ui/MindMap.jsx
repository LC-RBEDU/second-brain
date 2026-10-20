import { useMemo, useRef, useState } from "react";
import { panelClass, projectLabel } from "./chrome.jsx";

function allTasks(group) {
  const rows = [];
  for (const { epic, stories, loose } of group.epics) {
    rows.push(epic, ...stories, ...loose);
  }
  rows.push(...group.orphanStories, ...group.orphanTasks);
  return rows;
}

function flagsFor(group, today, issueIds) {
  let overdue = false;
  let bad = false;
  for (const task of allTasks(group)) {
    if (issueIds.has(task.id)) bad = true;
    if (task.deadline && task.deadline < today) overdue = true;
  }
  return { overdue, bad };
}

function polar(cx, cy, radius, angle) {
  return {
    x: cx + Math.cos(angle) * radius,
    y: cy + Math.sin(angle) * radius,
  };
}

export function MindMap({ groups, today, issueIds, onOpen }) {
  const [expanded, setExpanded] = useState(() => new Set());
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const drag = useRef(null);
  const width = 1040;
  const height = 720;
  const cx = width / 2;
  const cy = height / 2;

  const nodes = useMemo(() => {
    const list = groups || [];
    const n = Math.max(list.length, 1);
    return list.map((group, index) => {
      const angle = (Math.PI * 2 * index) / n - Math.PI / 2;
      const pos = polar(cx, cy, 260, angle);
      const open = expanded.has(group.slug);
      const flags = flagsFor(group, today, issueIds);
      const epics = open
        ? group.epics.map(({ epic, stories, loose }, epicIndex) => {
            const count = Math.max(group.epics.length, 1);
            const epicAngle = angle - 0.55 + (1.1 * epicIndex) / count;
            const epicPos = polar(pos.x, pos.y, 150, epicAngle);
            return {
              epic,
              stories,
              loose,
              x: epicPos.x,
              y: epicPos.y,
              openCount: stories.length + loose.length,
            };
          })
        : [];
      return { group, ...pos, angle, open, flags, epics };
    });
  }, [groups, today, issueIds, expanded, cx, cy]);

  return (
    <div data-layout-panel className={`${panelClass} relative overflow-hidden`} aria-label="Mindmapa">
      <div className="flex flex-wrap items-center gap-3 border-b border-[#e2e2e2] px-4 py-2 text-xs text-[#5c5c5c]">
        <span>Zoom: kolečko · posun: tažení podkladu · klik na projekt = rozbalit epiců</span>
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
          }}
        >
          Reset
        </button>
      </div>
      <div
        className="relative h-[720px] cursor-grab active:cursor-grabbing"
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
        <svg
          className="absolute inset-0 h-full w-full"
          viewBox={`0 0 ${width} ${height}`}
          style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, transformOrigin: "center center" }}
        >
          {nodes.map((node) => (
            <g key={`line-${node.group.slug}`}>
              <line x1={cx} y1={cy} x2={node.x} y2={node.y} stroke="#b0b2b6" strokeWidth="2" />
              {node.epics.map((epic) => (
                <line
                  key={`eline-${epic.epic.id}`}
                  x1={node.x}
                  y1={node.y}
                  x2={epic.x}
                  y2={epic.y}
                  stroke="#a11834"
                  strokeWidth="1.5"
                />
              ))}
            </g>
          ))}
          <circle cx={cx} cy={cy} r="36" fill="#444" />
          <text x={cx} y={cy + 5} textAnchor="middle" fill="#fafafa" fontSize="12" fontWeight="800">
            VAULT
          </text>
        </svg>
        <div
          className="absolute inset-0"
          style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, transformOrigin: "center center" }}
        >
          {nodes.map((node) => {
            const alert = node.flags.overdue || node.flags.bad;
            return (
              <div key={node.group.slug}>
                <button
                  type="button"
                  data-mind-node
                  className={`absolute w-[200px] -translate-x-1/2 -translate-y-1/2 rounded-md bg-white p-2.5 text-left text-sm shadow-sm ${
                    alert ? "border-2 border-[#b8002e]" : "border border-[#e2e2e2]"
                  } ${node.open ? "border-dashed" : ""}`}
                  style={{ left: node.x, top: node.y }}
                  onClick={() => {
                    setExpanded((prev) => {
                      const next = new Set(prev);
                      if (next.has(node.group.slug)) next.delete(node.group.slug);
                      else next.add(node.group.slug);
                      return next;
                    });
                  }}
                >
                  <div className="flex gap-2">
                    {(node.flags.overdue || node.flags.bad) && (
                      <div className="flex flex-col text-lg leading-none">
                        {node.flags.overdue && <span aria-label="overdue">❗</span>}
                        {node.flags.bad && <span aria-label="chybně zadané">⚠️</span>}
                      </div>
                    )}
                    <div className="min-w-0 flex-1">
                      <div className="text-[11px] text-[#5c5c5c]">{node.group.slug}</div>
                      <div className="font-bold uppercase">{projectLabel(node.group.slug)}</div>
                      <div className={`text-xs ${alert ? "font-bold text-[#b8002e]" : "text-[#5c5c5c]"}`}>
                        {node.group.epics.length} epiců · {node.group.open}
                      </div>
                    </div>
                  </div>
                </button>
                {node.epics.map((epicNode) => (
                  <button
                    key={epicNode.epic.id}
                    type="button"
                    data-mind-node
                    className="absolute w-[180px] -translate-x-1/2 -translate-y-1/2 rounded-md border border-[#e2e2e2] bg-white p-2 text-left text-sm shadow-sm"
                    style={{ left: epicNode.x, top: epicNode.y }}
                    onClick={() => onOpen?.(epicNode.epic)}
                  >
                    <div className="text-[11px] text-[#5c5c5c]">{epicNode.epic.id}</div>
                    <div className="font-bold">{epicNode.epic.title || epicNode.epic.id}</div>
                    <div className="text-xs text-[#5c5c5c]">{epicNode.openCount} otevřených</div>
                  </button>
                ))}
              </div>
            );
          })}
        </div>
      </div>
      <div className="absolute bottom-3 left-3 rounded-md border border-[#e2e2e2] bg-white px-3.5 py-2.5 text-xs text-[#5c5c5c]">
        <div className="mb-1 font-bold uppercase text-[#444]">Legenda</div>
        <div>
          <b className="text-[#b8002e]">Červený rámeček</b> = něco k řešení
        </div>
        <div>❗ overdue · ⚠️ chybně zadané</div>
        <div>Čárkovaný = rozbalený projekt</div>
      </div>
    </div>
  );
}
