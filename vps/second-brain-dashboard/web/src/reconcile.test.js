import { describe, expect, it } from "vitest";
import { reconcileExport } from "./reconcile.js";

describe("reconcileExport", () => {
  it("merges patch and oid", () => {
    const next = reconcileExport(
      { tasks: [{ id: "T1", title: "A", status: "Next", oid: "o1" }] },
      [{ id: "T1", patch: { status: "Doing" }, oid: "o2" }],
    );
    expect(next.tasks).toEqual([{ id: "T1", title: "A", status: "Doing", oid: "o2" }]);
  });

  it("drops Done from open list", () => {
    const next = reconcileExport(
      { tasks: [{ id: "T1", status: "Next" }, { id: "T2", status: "Next" }] },
      [{ id: "T1", patch: { status: "Done" } }],
    );
    expect(next.tasks.map((t) => t.id)).toEqual(["T2"]);
  });

  it("keep only updates review_deadline", () => {
    const next = reconcileExport(
      { tasks: [{ id: "T1", status: "Next", review_deadline: "" }] },
      [{ id: "T1", patch: { review_deadline: "2026-11-01" } }],
    );
    expect(next.tasks[0]).toMatchObject({
      id: "T1",
      status: "Next",
      review_deadline: "2026-11-01",
    });
  });
});
