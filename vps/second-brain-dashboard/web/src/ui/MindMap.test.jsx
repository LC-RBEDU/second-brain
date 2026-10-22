import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MindMap } from "./MindMap.jsx";

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
    open: 3,
    items: [rbuEpic, rbuStory, rbuTask],
    epics: [{ epic: rbuEpic, stories: [rbuStory], loose: [] }],
    orphanStories: [],
    orphanTasks: [],
  },
];

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
});
