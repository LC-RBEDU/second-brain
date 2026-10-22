import { describe, expect, it } from "vitest";
import { closingPreview, kanbanPatch, openChildrenOf, resolveCloser, rowPatch } from "./writes.js";

const story = { id: "F-S1", type: "story", status: "Next", project: "finance", title: "Story", parent: "F-E1" };
const same = { id: "F-T1", type: "task", status: "Next", project: "finance", title: "Stejný", parent: "F-S1" };
const other = { id: "F-T2", type: "task", status: "Doing", project: "sales", title: "Jiný", parent: "F-S1" };
const paused = { id: "F-T3", type: "task", status: "Backlog", project: "paused", title: "Pauza", parent: "F-S1" };

describe("writes", () => {
  it("B5 locks open children and leaves a Done child out", () => {
    const rows = closingPreview("F-S1", "cancelled", [story, same, other, paused]);
    const ids = rows.map((row) => row.id).sort();
    expect(ids).toEqual(["F-S1", "F-T1", "F-T2", "F-T3"]);
    for (const row of rows.filter((item) => item.id !== "F-S1")) {
      expect(row.resulting || row.action).toBe("cancelled");
      expect(row.locked).toBe(true);
    }
  });

  it("B25 sends status only", () => {
    const patch = kanbanPatch(
      { id: "F-T1", type: "task", status: "Doing", project: "finance", title: "Karta" },
      "Next",
      [{ id: "F-T1", type: "task", status: "Doing", project: "finance", title: "Karta" }],
    );
    expect(patch).toEqual({ status: "Next" });
    expect(patch).not.toHaveProperty("parent");
  });

  it("B41 does not compose a close when a paused child is still open", () => {
    const tasks = [story, paused];
    expect(kanbanPatch(story, "Done", tasks)).toBeNull();
    expect(kanbanPatch(paused, "Done", tasks)).toEqual({ status: "Done" });
  });

  it("allows non-terminal status moves on a parent with open children", () => {
    const tasks = [story, same];
    expect(kanbanPatch(story, "Doing", tasks)).toEqual({ status: "Doing" });
    expect(kanbanPatch(story, "Backlog", tasks)).toEqual({ status: "Backlog" });
    expect(kanbanPatch(story, "Cancelled", tasks)).toBeNull();
  });

  it("openChildrenOf lists only direct open kids", () => {
    const done = { ...same, id: "F-T9", status: "Done", title: "Hotový" };
    expect(openChildrenOf("F-S1", [story, same, other, done]).map((t) => t.id).sort()).toEqual([
      "F-T1",
      "F-T2",
    ]);
  });

  it("B43 lets the closer cancel replace Ponechat", () => {
    const [resolved] = resolveCloser([
      { id: "F-S1", parent: "", action: "cancelled", direct: true },
      { id: "F-T1", parent: "F-S1", action: "keep", direct: false, locked: false },
    ]).filter((row) => row.id === "F-T1");
    expect(resolved.resulting).toBe("cancelled");
    expect(resolved.locked).toBe(true);
    expect(resolved.needsDay).toBe(false);
  });

  it("B44 does not pull a child through an archived hop", () => {
    const epic = { id: "F-E1", type: "epic", status: "Next", project: "finance", title: "Epic" };
    const child = { id: "F-T1", type: "task", status: "Next", project: "finance", title: "Dítě", parent: "F-S1" };
    const rows = closingPreview("F-E1", "cancelled", [epic, child]);
    expect(rows.map((row) => row.id)).toEqual(["F-E1"]);
    expect(child.status).toBe("Next");
  });

  it("B49 sends only the toggled status", () => {
    const [row] = resolveCloser([
      {
        id: "F-T1",
        parent: "F-S1",
        action: "done",
        direct: true,
        locked: true,
        review_deadline: "2026-11-03",
      },
    ]);
    expect(rowPatch(row)).toEqual({ status: "Done" });
  });

  it("B53 confirm sends the prefilled review and leaves updated alone", () => {
    const patch = rowPatch({ resulting: "keep", date: "2026-11-03" });
    expect(patch).toEqual({ review_deadline: "2026-11-03" });
    expect(patch).not.toHaveProperty("updated");
  });
});
