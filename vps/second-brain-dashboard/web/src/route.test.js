import { describe, expect, it } from "vitest";
import { parseRoute, serializeRoute } from "./route.js";

describe("route", () => {
  it("defaults empty hash to radar", () => {
    expect(parseRoute("")).toEqual({ view: "radar", project: "", detailId: "" });
    expect(parseRoute("#")).toEqual({ view: "radar", project: "", detailId: "" });
  });

  it("round-trips map / cleanup / issues / new", () => {
    for (const view of ["map", "cleanup", "issues", "new", "radar"]) {
      expect(parseRoute(`#${serializeRoute({ view })}`).view).toBe(view);
    }
  });

  it("keeps project slug and detail id", () => {
    expect(serializeRoute({ view: "project", project: "it-ai-data" })).toBe("project/it-ai-data");
    expect(parseRoute("#project/it-ai-data")).toEqual({
      view: "project",
      project: "it-ai-data",
      detailId: "",
    });
    expect(parseRoute("#detail/F-T175")).toEqual({
      view: "detail",
      project: "",
      detailId: "F-T175",
    });
    expect(serializeRoute({ view: "detail", detailId: "IAD-S44" })).toBe("detail/IAD-S44");
  });

  it("falls back unknown pages to radar", () => {
    expect(parseRoute("#nope").view).toBe("radar");
  });
});
