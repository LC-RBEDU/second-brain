import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useState } from "react";
import { MindMap, fitZoomForNodes, resolveNavStack } from "./MindMap.jsx";

afterEach(() => cleanup());

const today = "2026-10-22";
const issueIds = new Set(["T-BAD"]);

const sbTasks = [
  { id: "SB1", title: "Alpha", type: "task", status: "Next", parent: "", deadline: null },
  { id: "T-BAD", title: "Beta", type: "task", status: "Doing", parent: "", deadline: "2026-01-01" },
];
const rbuEpic = { id: "RBU-E1", title: "Epic One", type: "epic", status: "Doing", parent: "", deadline: null };
const rbuStory = {
  id: "RBU-S1",
  title: "Story One",
  type: "story",
  status: "Next",
  parent: "[[RBU-E1]]",
  deadline: null,
};
const rbuTask = {
  id: "RBU-T1",
  title: "Leaf task",
  type: "task",
  status: "Next",
  parent: "[[RBU-S1 — Story One]]",
  deadline: null,
};
const longEpic = {
  id: "RBU-E99",
  title: "SignatureSatori — centrální e-mailové podpisy v RB Universe",
  type: "epic",
  status: "Doing",
  parent: "",
  deadline: "2026-01-01",
};

const groups = [
  {
    slug: "second-brain",
    open: 2,
    items: sbTasks,
    epics: [],
    orphanStories: [],
    orphanTasks: sbTasks,
  },
  {
    slug: "rb-universe-development",
    open: 4,
    items: [rbuEpic, rbuStory, rbuTask, longEpic],
    epics: [
      { epic: rbuEpic, stories: [rbuStory], loose: [] },
      { epic: longEpic, stories: [], loose: [] },
    ],
    orphanStories: [],
    orphanTasks: [],
  },
];

describe("MindMap helpers", () => {
  it("fitZoomForNodes zmenší zoom, aby se kruh vešel do úzkého viewportu", () => {
    const nodes = [
      { x: 520, y: 100 },
      { x: 520, y: 620 },
      { x: 100, y: 360 },
      { x: 940, y: 360 },
    ];
    const zoom = fitZoomForNodes(nodes, 670, 720, 520, 360);
    expect(zoom).toBeLessThan(1);
    expect(zoom).toBeGreaterThanOrEqual(0.28);
  });

  it("resolveNavStack doplní task z groups podle taskId", () => {
    const resolved = resolveNavStack(
      [
        { kind: "project", slug: "rb-universe-development" },
        { kind: "epic", slug: "rb-universe-development", taskId: "RBU-E1" },
      ],
      groups,
    );
    expect(resolved).toHaveLength(2);
    expect(resolved[1].task.title).toBe("Epic One");
  });
});

describe("MindMap", () => {
  it("kreslí spojnice a dlaždice ve stejném canvasu (left/top = line x2/y2)", () => {
    const { container } = render(
      <MindMap groups={groups} today={today} issueIds={issueIds} onOpen={() => {}} />,
    );
    const canvas = container.querySelector('[aria-label="Mindmapa"] .absolute.left-1\\/2');
    expect(canvas).toBeTruthy();
    const svg = canvas.querySelector("svg");
    expect(svg.getAttribute("width")).toBe("1040");
    expect(svg.getAttribute("height")).toBe("720");
    const line = svg.querySelector("line");
    const firstProject = screen.getByRole("button", { name: /second-brain/i });
    const left = Number.parseFloat(firstProject.style.left);
    const top = Number.parseFloat(firstProject.style.top);
    expect(Number.parseFloat(line.getAttribute("x2"))).toBeCloseTo(left, 0);
    expect(Number.parseFloat(line.getAttribute("y2"))).toBeCloseTo(top, 0);
  });

  it("střed má prostor pro 2–3 řádky dlouhého názvu", () => {
    const stack = [
      { kind: "project", slug: "rb-universe-development" },
      { kind: "epic", slug: "rb-universe-development", taskId: "RBU-E99" },
    ];
    render(
      <MindMap
        groups={groups}
        today={today}
        issueIds={issueIds}
        onOpen={() => {}}
        navStack={stack}
        onNavStackChange={() => {}}
      />,
    );
    const center = screen.getByRole("button", { name: /Zpět z SignatureSatori/i });
    expect(center.className).toMatch(/min-h-\[168px\]/);
    expect(center.className).toMatch(/w-\[180px\]/);
    expect(center.textContent).toMatch(/RBU-E99/);
    expect(center.textContent).toMatch(/SignatureSatori/);
    expect(center.textContent).toMatch(/zpět/);
  });

  it("drill-down projekt → tasky a zpět přes střed", () => {
    const onOpen = vi.fn();
    render(<MindMap groups={groups} today={today} issueIds={issueIds} onOpen={onOpen} />);

    fireEvent.click(screen.getByRole("button", { name: /SECOND-BRAIN/i }));
    expect(screen.getByRole("button", { name: /Zpět z SECOND-BRAIN/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Alpha/i })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Alpha/i }));
    expect(onOpen).toHaveBeenCalledWith(expect.objectContaining({ id: "SB1" }));

    fireEvent.click(screen.getByRole("button", { name: /Zpět z SECOND-BRAIN/i }));
    expect(screen.getByRole("button", { name: /^VAULT$/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /SECOND-BRAIN/i })).toBeTruthy();
  });

  it("drill-down projekt → epic → story → task", () => {
    const onOpen = vi.fn();
    render(<MindMap groups={groups} today={today} issueIds={issueIds} onOpen={onOpen} />);

    fireEvent.click(screen.getByRole("button", { name: /RB-UNIVERSE-DEVELOPMENT/i }));
    fireEvent.click(screen.getByRole("button", { name: /Epic One/i }));
    expect(screen.getByRole("button", { name: /Zpět z Epic One/i })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Story One/i }));
    expect(screen.getByRole("button", { name: /Zpět z Story One/i })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Leaf task/i }));
    expect(onOpen).toHaveBeenCalledWith(expect.objectContaining({ id: "RBU-T1" }));

    fireEvent.click(screen.getByRole("button", { name: /Zpět z Story One/i }));
    expect(screen.getByRole("button", { name: /Zpět z Epic One/i })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Zpět z Epic One/i }));
    expect(screen.getByRole("button", { name: /Zpět z RB-UNIVERSE-DEVELOPMENT/i })).toBeTruthy();
  });

  it("po unmount/remount s navStack zůstane úroveň (návrat z detailu)", () => {
    function Harness({ open }) {
      const [stack, setStack] = useState([
        { kind: "project", slug: "second-brain" },
      ]);
      if (!open) return <div>detail</div>;
      return (
        <MindMap
          groups={groups}
          today={today}
          issueIds={issueIds}
          onOpen={() => {}}
          navStack={stack}
          onNavStackChange={setStack}
        />
      );
    }
    const { rerender } = render(<Harness open />);
    expect(screen.getByRole("button", { name: /Zpět z SECOND-BRAIN/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Alpha/i })).toBeTruthy();
    rerender(<Harness open={false} />);
    expect(screen.getByText("detail")).toBeTruthy();
    rerender(<Harness open />);
    expect(screen.getByRole("button", { name: /Zpět z SECOND-BRAIN/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Alpha/i })).toBeTruthy();
  });

  it("Reset vrátí VAULT a nastaví zoom podle viewportu (fit)", () => {
    const crowded = Array.from({ length: 16 }, (_, index) => ({
      slug: `proj-${index}`,
      open: 1,
      items: [{ id: `T${index}`, title: `T${index}`, type: "task", status: "Next", parent: "", deadline: null }],
      epics: [],
      orphanStories: [],
      orphanTasks: [{ id: `T${index}`, title: `T${index}`, type: "task", status: "Next", parent: "", deadline: null }],
    }));
    const { container } = render(
      <MindMap groups={crowded} today={today} issueIds={issueIds} onOpen={() => {}} />,
    );
    fireEvent.click(screen.getByRole("button", { name: /PROJ-0/i }));
    expect(screen.getByRole("button", { name: /Zpět z PROJ-0/i })).toBeTruthy();

    const viewport = container.querySelector(".cursor-grab");
    viewport.getBoundingClientRect = () => ({
      width: 480,
      height: 720,
      top: 0,
      left: 0,
      bottom: 720,
      right: 480,
      x: 0,
      y: 0,
      toJSON() {},
    });
    fireEvent.click(screen.getByRole("button", { name: /^Reset$/i }));
    expect(screen.getByRole("button", { name: /^VAULT$/i })).toBeTruthy();
    const label = container.querySelector("[aria-live='polite']");
    const pct = Number.parseInt(label?.textContent || "100", 10);
    expect(pct).toBeLessThan(100);
    expect(pct).toBeGreaterThanOrEqual(28);
  });
});
