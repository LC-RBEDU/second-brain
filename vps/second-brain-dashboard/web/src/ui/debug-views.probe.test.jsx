import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, it } from "vitest";
import { appendFileSync } from "node:fs";
import { App } from "./App.jsx";

afterEach(() => cleanup());

const LOG =
  "/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/.cursor/debug-7e3b98.log";

function log(hypothesisId, message, data) {
  appendFileSync(
    LOG,
    `${JSON.stringify({
      sessionId: "7e3b98",
      hypothesisId,
      location: "debug-views.probe.test.jsx",
      message,
      data,
      timestamp: Date.now(),
      runId: process.env.DEBUG_RUN_ID || "post-fix",
    })}\n`,
  );
}

const PROJECTS = [
  { slug: "finance", hierarchy: true, status: "active", title: "Finance" },
  { slug: "paused", status: "paused" },
];

function task(fields) {
  return {
    type: "task",
    status: "Next",
    project: "finance",
    title: fields.id,
    path: `02-PROJEKTY/finance/tasks/${fields.id}.md`,
    ...fields,
  };
}

function metrics(root) {
  return {
    tables: root.querySelectorAll("table").length,
    articles: root.querySelectorAll("article").length,
    bareParagraphs: [...root.querySelectorAll("section p")].filter((p) => !p.className).length,
    wineNav: Boolean(root.querySelector(".bg-\\[\\#444444\\], [class*='bg-[#444444]']")) || Boolean(root.querySelector("nav.bg-\\[\\#444444\\]")),
    navClass: root.querySelector("nav")?.className || "",
    sectionLabels: [...root.querySelectorAll("section")].map((s) => s.getAttribute("aria-label")),
    h1: [...root.querySelectorAll("h1")].map((h) => h.textContent),
    hasRoundedPanel: Boolean(root.querySelector("[class*='rounded']")),
    hasBorderPanel: Boolean(root.querySelector("[class*='border-[#e2e2e2]'], [class*='border-e2e2e2']")),
    statusButtonsInArticles: [...root.querySelectorAll("article")].reduce(
      (sum, article) => sum + article.querySelectorAll('button[aria-label^="Přesunout"]').length,
      0,
    ),
  };
}

describe("debug view structure probe", () => {
  it("measures every screen against wireframe expectations", () => {
    const tasks = [
      task({ id: "F-E1", type: "epic", title: "Cashflow" }),
      task({ id: "F-S1", type: "story", title: "Story", parent: "F-E1", deadline: "2026-10-01" }),
      task({ id: "F-T1", type: "task", title: "Dítě", parent: "F-S1", status: "Doing", deadline: "2026-10-01" }),
      task({ id: "F-T2", type: "task", title: "Bez data", parent: "F-S1" }),
    ];
    const { container } = render(<App exportData={{ tasks, projects: PROJECTS }} today="2026-10-20" />);

    log("A", "radar metrics", metrics(container));
    log("B", "radar status buttons near title (expect 0)", {
      statusButtonsInArticles: metrics(container).statusButtonsInArticles,
      inlineStatusSelects: container.querySelectorAll('select[aria-label^="Status "]').length,
      expectWireframeTable: metrics(container).tables === 0,
    });

    for (const [name, hyp] of [
      ["Chybně zadané", "D"],
      ["Mapa", "D"],
      ["Projekt", "D"],
      ["Nový task", "D"],
      ["Úklid", "D"],
    ]) {
      fireEvent.click(screen.getByRole("button", { name }));
      const m = metrics(container);
      log(hyp, `${name} metrics`, {
        ...m,
        wireframeExpectsTableOrTree: name !== "Nový task",
        looksBare: m.tables === 0 && m.bareParagraphs > 0,
      });
    }

    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    fireEvent.click(screen.getByRole("button", { name: "F-T1 — Dítě" }));
    log("D", "detail metrics", metrics(container));

    log("C", "shared chrome check", {
      navClass: container.querySelector("nav")?.className || "",
      hasBrand: Boolean(screen.queryByText("Second Brain")),
    });
  });
});
