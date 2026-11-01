import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import "@testing-library/jest-dom/vitest";
import { App } from "./App.jsx";
import { BusyProvider } from "./BusyContext.jsx";
import { BusyOverlay } from "./BusyOverlay.jsx";

afterEach(() => cleanup());

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

function wrap(ui) {
  return (
    <BusyProvider onError={() => {}}>
      {ui}
      <BusyOverlay />
    </BusyProvider>
  );
}

function looksBare(root) {
  const tables = root.querySelectorAll("table").length;
  const bareParagraphs = [...root.querySelectorAll("section p")].filter((p) => !p.className).length;
  return tables === 0 && bareParagraphs > 0;
}

describe("layout views probe T17", () => {
  it("B-V1…B-V8 hard expects against wireframe DoD", async () => {
    const tasks = [
      task({ id: "F-E1", type: "epic", title: "Cashflow" }),
      task({ id: "F-S1", type: "story", title: "Story", parent: "F-E1", deadline: "2026-10-01" }),
      task({ id: "F-T1", type: "task", title: "Dítě", parent: "F-S1", status: "Doing", deadline: "2026-10-01" }),
      task({ id: "F-T2", type: "task", title: "Bez data", parent: "F-S1" }),
    ];
    const { container } = render(
      wrap(<App exportData={{ tasks, projects: PROJECTS }} today="2026-10-20" />),
    );

    // B-V1 Chrome
    const nav = container.querySelector("nav");
    expect(nav).toBeTruthy();
    expect(nav.className).toMatch(/444444|#444/);
    expect(screen.getByText("Second Brain")).toBeInTheDocument();

    // B-V2 Radar
    const radar = screen.getByRole("region", { name: "Radar" });
    expect(within(radar).getByRole("heading", { level: 1, name: "Radar" })).toBeInTheDocument();
    const tiles = within(radar).getByLabelText("Kategorie").querySelectorAll("button");
    expect(tiles.length).toBeGreaterThanOrEqual(8);
    fireEvent.click(tiles[0]);
    expect(looksBare(container)).toBe(false);

    // B-V8 Chybně zadané
    fireEvent.click(screen.getByRole("button", { name: "Chybně zadané" }));
    const issues = screen.getByRole("region", { name: "Chybně zadané" });
    expect(within(issues).getByRole("table")).toBeInTheDocument();
    expect(looksBare(container)).toBe(false);

    // B-V3 Mapa
    fireEvent.click(screen.getByRole("button", { name: "Mapa" }));
    expect(screen.getByLabelText("Strom")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Mindmapa" }));
    expect(screen.getByLabelText("Mindmapa")).toBeInTheDocument();
    expect(looksBare(container)).toBe(false);

    // B-V4 Projekt
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    const project = screen.getByRole("region", { name: "Projekt" });
    expect(project).toBeInTheDocument();
    fireEvent.click(within(project).getByRole("button", { name: "Kanban" }));
    expect(within(project).getAllByRole("columnheader").length).toBe(4);
    expect(looksBare(container)).toBe(false);

    // B-V6 Nový (+ B-V6m Materiály)
    fireEvent.click(screen.getByRole("button", { name: "Nový task" }));
    const neo = screen.getByRole("region", { name: "Nový task" });
    expect(within(neo).getByRole("radiogroup")).toBeInTheDocument();
    expect(within(neo).getByRole("button", { name: "Založit" })).toBeInTheDocument();
    expect(within(neo).getByLabelText("Materiály nového tasku")).toBeInTheDocument();
    expect(looksBare(container)).toBe(false);

    // B-V7 Úklid
    fireEvent.click(screen.getByRole("button", { name: "Úklid" }));
    expect(screen.getByRole("button", { name: "Náhled" })).toBeInTheDocument();
    expect(looksBare(container)).toBe(false);

    // B-V5 Detail (+ B-V5m Materiály)
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "F-T1 — Dítě" }));
    });
    const detail = screen.getByRole("region", { name: "Detail" });
    expect(detail.className).toMatch(/max-w-xl/);
    expect(within(detail).getByRole("button", { name: "Uložit" })).toBeInTheDocument();
    expect(within(detail).getByLabelText("Materiály a odkazy")).toBeInTheDocument();
    expect(looksBare(container)).toBe(false);
  });
});
