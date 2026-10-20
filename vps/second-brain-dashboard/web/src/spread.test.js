import { describe, expect, it } from "vitest";
import {
  applySelection,
  assignDays,
  canSend,
  deleteDate,
  isNonWorkDay,
  keepDate,
  occupancy,
  overwriteDate,
  sortQueue,
} from "./spread.js";

function days(queue, opts) {
  return assignDays(queue, opts).map((row) => [row.id, row.date]);
}

describe("spread", () => {
  it("B6 skips a weekend, a holiday and 24 December, and a paused review still occupies", () => {
    const paused = { id: "P-T1", type: "task", status: "Next", project: "paused", review_deadline: "2026-12-23" };
    const queue = [{ id: "F-T1", type: "task", status: "Next", project: "finance" }];
    const taken = occupancy([paused]);
    expect(isNonWorkDay("2026-12-24")).toBe(true);
    expect(isNonWorkDay("2026-12-27")).toBe(true);
    expect(isNonWorkDay("2026-11-17")).toBe(true);
    expect(isNonWorkDay("2026-04-03")).toBe(true);
    expect(isNonWorkDay("2026-04-06")).toBe(true);
    expect(days(queue, { from: "2026-12-23", to: "2026-12-28", maxPerDay: 1, skipNonWork: true, taken })).toEqual([
      ["F-T1", "2026-12-28"],
    ]);
    expect(days(queue, { from: "2026-12-23", to: "2026-12-28", maxPerDay: 1, skipNonWork: false, taken })).toEqual([
      ["F-T1", "2026-12-24"],
    ]);
    expect(taken.get("2026-12-23")).toBe(1);
  });

  it("B7 occupies only the new day", () => {
    const task = { id: "F-T1", type: "task", status: "Next", project: "finance", review_deadline: "2026-11-01" };
    const counts = occupancy([task], new Map([["F-T1", { date: "2026-11-05" }]]));
    expect(counts.get("2026-11-05")).toBe(1);
    expect(counts.has("2026-11-01")).toBe(false);
  });

  it("B21 ignores Done and Cancelled", () => {
    const counts = occupancy([
      { id: "F-T1", type: "task", status: "Next", project: "finance", review_deadline: "2026-11-02" },
      { id: "F-T2", type: "task", status: "Done", project: "finance", deadline: "2026-11-02" },
      { id: "F-T3", type: "task", status: "Cancelled", project: "finance", deadline: "2026-11-02", path: "07-ARCHIV/tasks-done/finance/F-T3.md" },
    ]);
    expect(counts.get("2026-11-02")).toBe(1);
  });

  it("B38 assigns the three orders across 9 to 13 November", () => {
    const lookup = [
      { id: "B-E", type: "epic", project: "proj-b", parent: "", updated: "2026-01-01", priority_score: "", status: "Next" },
    ];
    const projectQueue = [
      { id: "A-X", type: "epic", project: "proj-a", parent: "", updated: "2026-01-01", priority_score: "", status: "Next" },
      { id: "A-T0", type: "task", project: "proj-a", parent: "A-X", updated: "2026-02-01", status: "Next" },
      { id: "A-T1", type: "task", project: "proj-a", parent: "A-X", updated: "2026-03-01", status: "Next" },
      { id: "A-T2", type: "task", project: "proj-a", parent: "A-X", updated: "2026-04-01", status: "Next" },
      { id: "B-T1", type: "task", project: "proj-b", parent: "B-E", updated: "2026-01-01", status: "Next" },
    ];
    const window = { from: "2026-11-09", to: "2026-11-13", maxPerDay: 1, skipNonWork: true };
    const projectDays = days(sortQueue(projectQueue, "project_epic", [...projectQueue, ...lookup]), window);
    expect(projectDays).toEqual([
      ["A-X", "2026-11-09"],
      ["A-T0", "2026-11-10"],
      ["A-T1", "2026-11-11"],
      ["A-T2", "2026-11-12"],
      ["B-T1", "2026-11-13"],
    ]);
    expect(projectDays.map(([id]) => id)).not.toContain("B-E");

    const priorityQueue = [
      { id: "S-OLD", updated: "2026-01-01", priority_score: 10, status: "Next", project: "finance" },
      { id: "S-NEW", updated: "2026-06-01", priority_score: 10, status: "Next", project: "finance" },
      { id: "S-MISS", priority_score: 10, status: "Next", project: "finance" },
      { id: "S-LOW", updated: "2026-01-01", priority_score: 0, status: "Next", project: "finance" },
      { id: "S-EMPTY", updated: "2026-01-01", priority_score: "", status: "Next", project: "finance" },
    ];
    expect(days(sortQueue(priorityQueue, "priority", priorityQueue), window).map(([id]) => id)).toEqual([
      "S-OLD",
      "S-NEW",
      "S-MISS",
      "S-LOW",
      "S-EMPTY",
    ]);

    const ageQueue = [
      { id: "Z-OLD", updated: "2026-01-01", status: "Next", project: "finance" },
      { id: "Z-NEW", updated: "2026-06-01", status: "Next", project: "finance" },
      { id: "Z-B", status: "Next", project: "finance" },
      { id: "Z-A", status: "Next", project: "finance" },
    ];
    expect(days(sortQueue(ageQueue, "age", ageQueue), window).map(([id]) => id)).toEqual([
      "Z-OLD",
      "Z-NEW",
      "Z-A",
      "Z-B",
    ]);
  });

  it("B39 holds the write when the queue cannot fit", () => {
    const queue = [{ id: "F-T1", date: null }];
    expect(canSend({ queue, from: "2026-11-12", to: "2026-11-09", maxPerDay: 1 })).toBe(false);
    expect(canSend({ queue, from: "2026-11-09", to: "2026-11-13", maxPerDay: 0 })).toBe(false);
    const missed = assignDays([{ id: "F-T1" }], {
      from: "2026-11-17",
      to: "2026-11-17",
      maxPerDay: 1,
      skipNonWork: true,
    });
    expect(canSend({ queue: missed, from: "2026-11-17", to: "2026-11-17", maxPerDay: 1 })).toBe(false);
  });

  it("B42 frees a closed day and counts one task once", () => {
    const tasks = [
      { id: "F-T1", status: "Next", project: "finance", deadline: "2026-11-03", review_deadline: "2026-11-03" },
      { id: "F-T2", status: "Next", project: "finance", deadline: "2026-11-04", review_deadline: "2026-11-04" },
    ];
    const open = occupancy(tasks);
    expect(open.get("2026-11-03")).toBe(1);
    const closed = occupancy(tasks, new Map([["F-T1", { resulting: "done" }]]));
    expect(closed.has("2026-11-03")).toBe(false);
    expect(closed.get("2026-11-04")).toBe(1);
  });

  it("B48 lets a filled queue go and keeps both concrete days", () => {
    const own = overwriteDate("2026-11-08");
    const filled = applySelection(keepDate(""), "2026-11-12");
    const tasks = [
      { id: "OWN", status: "Next", project: "finance", review_deadline: "2026-10-01" },
      { id: "FILL", status: "Next", project: "finance" },
      { id: "OTHER", status: "Next", project: "paused", review_deadline: "2026-11-08" },
    ];
    const counts = occupancy(
      tasks,
      new Map([
        ["OWN", own],
        ["FILL", filled],
      ]),
    );
    expect(counts.get("2026-11-08")).toBe(2);
    expect(counts.get("2026-11-12")).toBe(1);
    expect(canSend({ queue: [], from: "" })).toBe(true);
    const waiting = applySelection(keepDate(""), "");
    expect(canSend({ queue: [{ id: "FILL", date: waiting.date }], from: "" })).toBe(false);
  });

  it("B53 drops a deleted prefill and treats a manual day as owned", () => {
    const task = { id: "F-T1", status: "Next", project: "finance", review_deadline: "2026-11-03", updated: "2026-10-01" };
    const manual = overwriteDate("2026-11-15");
    expect(manual.own).toBe(true);
    expect(applySelection(manual, "2026-11-12").date).toBe("2026-11-15");
    const removed = deleteDate();
    const counts = occupancy([task], new Map([["F-T1", removed]]));
    expect(counts.has("2026-11-03")).toBe(false);
    expect(keepDate("2026-11-03").date).toBe("2026-11-03");
  });
});
