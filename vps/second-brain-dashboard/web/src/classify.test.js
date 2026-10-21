import { describe, expect, it } from "vitest";
import { classify, RULE_HELP, ruleHelp } from "./classify.js";
import { isoWeek } from "./focusSlots.js";

const TODAY = "2026-10-20";

function run(tasks, extra = {}) {
  return classify({ tasks }, { today: TODAY, ...extra });
}

describe("classify", () => {
  it("ruleHelp explains stale and title_markup", () => {
    expect(RULE_HELP.stale).toMatch(/30/);
    expect(ruleHelp("title_markup")).toMatch(/markup|\[\[/);
    expect(ruleHelp("parse_yaml")).toMatch(/parsování/);
  });

  it("B1 counts a task once, keeps no_date off the error tile, and ignores stale_unknown", () => {
    const result = run([
      {
        id: "F-E2",
        type: "epic",
        status: "Next",
        project: "finance",
        parent: "F-E1",
        title: "Dvě chyby",
        deadline: "2026-11-01",
      },
      { id: "F-E1", type: "epic", status: "Next", project: "finance", title: "Epic", deadline: "2026-12-01" },
      { id: "F-T1", type: "task", status: "Next", project: "finance", title: "Bez data" },
      {
        id: "F-T2",
        type: "task",
        status: "Next",
        project: "finance",
        title: "Starý",
        review_deadline: "2026-11-01",
        updated: "2026-01-01",
      },
      {
        id: "F-T3",
        type: "task",
        status: "Next",
        project: "finance",
        title: "Bez updated",
        review_deadline: "2026-11-01",
        filename_title_mismatch: true,
      },
    ]);
    expect(result.tiles.errors).toBe(1);
    expect(result.tiles.stale).toBe(1);
    expect(result.tiles.no_date).toBe(1);
    expect(result.issues.some((item) => item.rule === "filename_title")).toBe(false);
    expect(result.issues.filter((item) => item.id === "F-E2" && item.severity === "error")).toHaveLength(2);
  });

  it("B2 splits missing dates, Doing, overdue and a past review", () => {
    const result = run([
      { id: "F-T1", type: "task", status: "Next", project: "finance", title: "Bez" },
      { id: "F-T2", type: "task", status: "Doing", project: "finance", title: "Delam" },
      { id: "F-T3", type: "task", status: "Next", project: "finance", title: "Po", deadline: "2026-10-01" },
      { id: "F-T4", type: "task", status: "Next", project: "finance", title: "Review", review_deadline: "2026-10-01" },
      { id: "F-T5", type: "task", status: "Waiting", project: "finance", title: "Cekam", review_deadline: "2026-10-01", waitUntil: "2026-11-01" },
    ]);
    expect(result.radar.no_date).toEqual(["F-T1"]);
    expect(result.radar.doing).toEqual(["F-T2"]);
    expect(result.radar.overdue).toEqual(["F-T3"]);
    expect(result.radar.to_decide).toEqual(["F-T4"]);
    expect(result.radar.to_decide).not.toContain("F-T3");
    expect(result.radar.to_decide).not.toContain("F-T5");
  });

  it("B3 applies story_no_epic only where hierarchy is true", () => {
    const result = run(
      [
        { id: "F-S1", type: "story", status: "Next", project: "finance", title: "S", review_deadline: "2026-11-01" },
        { id: "F-S2", type: "story", status: "Next", project: "other", title: "S", review_deadline: "2026-11-01" },
        { id: "F-S3", type: "story", status: "Next", project: "plain", title: "S", review_deadline: "2026-11-01" },
      ],
      {
        projects: [
          { slug: "finance", hierarchy: true, status: "active" },
          { slug: "other", hierarchy: false, status: "active" },
          { slug: "plain", status: "active" },
        ],
      },
    );
    const stories = result.issues.filter((item) => item.rule === "story_no_epic").map((item) => item.id);
    expect(stories).toEqual(["F-S1"]);
  });

  it("B4 skips parent_closed and counts the task once", () => {
    const result = run([
      {
        id: "F-S9",
        type: "story",
        status: "Done",
        project: "finance",
        title: "Hotovo",
        path: "07-ARCHIV/tasks-done/finance/F-S9.md",
      },
      {
        id: "F-T9",
        type: "task",
        status: "Next",
        project: "finance",
        title: "Dite",
        parent: "F-S9",
        review_deadline: "2026-11-01",
        updated: "2026-10-01",
        parse_errors: ["parent_closed", "parent_not_found"],
      },
    ]);
    expect(result.tasks.map((task) => task.id)).toEqual(["F-T9"]);
    expect(result.issues.map((item) => item.rule)).toEqual(["parent_missing_or_closed"]);
    expect(result.tiles.errors).toBe(1);
  });

  it("B20 returns zero tiles for an empty export", () => {
    const result = run([]);
    expect(Object.keys(result.tiles)).toHaveLength(9);
    expect(Object.values(result.tiles).every((value) => value === 0)).toBe(true);
  });

  it("B24 counts recurring and a story whose only child is paused", () => {
    const week = isoWeek(TODAY);
    const projects = [
      { slug: "active", hierarchy: true, status: "active" },
      { slug: "paused", status: "paused" },
    ];
    const result = run(
      [
        { id: "F-E1", type: "epic", status: "Next", project: "active", title: "Epic", focus: week, deadline: "2026-12-01" },
        { id: "F-S1", type: "story", status: "Next", project: "active", title: "Story", parent: "F-E1", focus: week, deadline: "2026-12-01" },
        { id: "F-T1", type: "task", status: "Next", project: "active", title: "Dite", parent: "F-S1", deadline: "2026-12-01" },
        { id: "F-T2", type: "task", status: "Next", project: "active", title: "Rituál", focus: week, deadline: "2026-12-01", is_recurring: true },
        { id: "F-T3", type: "task", status: "Waiting", project: "active", title: "Cekam", focus: week, waitUntil: "2026-12-01" },
        { id: "F-S2", type: "story", status: "Next", project: "active", title: "Pauza", parent: "F-E1", focus: week, deadline: "2026-12-01" },
        { id: "F-T4", type: "task", status: "Next", project: "paused", title: "Dite pauzy", parent: "F-S2", deadline: "2026-12-01" },
      ],
      { projects },
    );
    expect(result.radar.focus_week).toHaveLength(5);
    expect(result.tiles.focus).toBe(2);
  });

  it("B32 treats the Prague day after 22:30Z as overdue", () => {
    const result = classify(
      {
        tasks: [
          { id: "F-T1", type: "task", status: "Next", project: "finance", title: "Vecer", deadline: "2026-10-19" },
        ],
      },
      { now: "2026-10-19T22:30:00Z" },
    );
    expect(result.today).toBe("2026-10-20");
    expect(result.tiles.overdue).toBe(1);
  });
});
