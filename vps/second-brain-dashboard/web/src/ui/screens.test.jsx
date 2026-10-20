import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import "@testing-library/jest-dom/vitest";
import { App } from "./App.jsx";

afterEach(() => cleanup());

const PROJECTS = [
  { slug: "finance", hierarchy: true, status: "active" },
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

function renderApp(tasks, api = {}, extra = {}) {
  return render(<App exportData={{ tasks, projects: PROJECTS, ...extra }} api={api} today="2026-10-20" />);
}

describe("screens", () => {
  it("B21 and B57 hide closed and archived rows and have no Done column", () => {
    renderApp([
      task({ id: "OPEN-1", title: "Otevřený", deadline: "2026-11-01" }),
      task({ id: "DONE-1", title: "Hotový řádek", status: "Done", deadline: "2026-10-01" }),
      task({ id: "CANCEL-1", title: "Zrušený řádek", status: "Cancelled" }),
      task({ id: "ARCH-1", title: "Archiv", path: "07-ARCHIV/tasks-done/finance/ARCH-1.md", deadline: "2026-10-01" }),
    ]);
    expect(screen.getByText("Overdue 0")).toBeInTheDocument();
    expect(screen.queryByText(/DONE-1/)).toBeNull();
    expect(screen.queryByText(/CANCEL-1/)).toBeNull();
    expect(screen.queryByText(/ARCH-1/)).toBeNull();
    for (const name of ["Chybně zadané", "Mapa", "Projekt", "Nový task", "Úklid"]) {
      fireEvent.click(screen.getByRole("button", { name }));
      expect(screen.queryByText(/DONE-1/)).toBeNull();
      expect(screen.queryByText(/ARCH-1/)).toBeNull();
      if (name === "Nový task") {
        expect(within(screen.getByRole("region", { name: "Nový task" })).queryByRole("option", { name: "paused" })).toBeNull();
      }
    }
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    fireEvent.click(screen.getByRole("button", { name: "Kanban" }));
    expect(screen.getAllByRole("columnheader").map((item) => item.textContent)).toEqual([
      "Doing",
      "Next",
      "Waiting",
      "Backlog",
    ]);
    expect(screen.queryByRole("columnheader", { name: "Hotovo" })).toBeNull();
  });

  it("B4 shows one missing-parent error and not the closed parent", () => {
    renderApp([
      task({ id: "F-S9", type: "story", status: "Done", title: "Uzavřený rodič" }),
      task({
        id: "F-T9",
        title: "Dítě",
        parent: "F-S9",
        review_deadline: "2026-11-01",
        updated: "2026-10-01",
        parse_errors: ["parent_closed"],
      }),
    ]);
    fireEvent.click(screen.getByRole("button", { name: "Chybně zadané" }));
    expect(screen.getByRole("heading", { name: "Chybně zadané 1" })).toBeInTheDocument();
    expect(screen.getByText("F-T9 — Dítě")).toBeInTheDocument();
    expect(screen.getByText("parent_missing_or_closed")).toBeInTheDocument();
    expect(screen.queryByText(/Uzavřený rodič/)).toBeNull();
  });

  it("B5 locks open children from a paused project and skips a Done child", () => {
    renderApp([
      task({ id: "F-S1", type: "story", title: "Story", parent: "F-E1" }),
      task({ id: "F-T1", title: "Stejný", parent: "F-S1" }),
      task({ id: "F-T2", title: "Jiný", project: "sales", parent: "F-S1" }),
      task({ id: "F-T3", title: "Pauza", project: "paused", parent: "F-S1" }),
    ]);
    fireEvent.click(screen.getByRole("button", { name: "Úklid" }));
    const browse = screen.getByRole("region", { name: "Seznam úklidu" });
    expect(within(browse).queryByText(/Pauza/)).toBeNull();
    fireEvent.click(within(browse).getByRole("checkbox", { name: "Vybrat F-S1 — Story" }));
    fireEvent.change(screen.getByLabelText("Akce F-S1"), { target: { value: "cancelled" } });
    fireEvent.click(screen.getByRole("button", { name: "Náhled" }));
    const preview = screen.getByRole("region", { name: "Náhled úklidu" });
    expect(within(preview).getByText(/Pauza/)).toBeInTheDocument();
    expect(within(preview).getByText(/Jiný/)).toBeInTheDocument();
    expect(within(preview).getByRole("checkbox", { name: "Náhled F-T3 — Pauza" })).toBeDisabled();
    expect(within(preview).queryByText(/Hotový/)).toBeNull();
  });

  it("B27 sends Done as status only and ignores an empty Doing confirm", () => {
    const api = { patch: vi.fn() };
    renderApp([
      task({ id: "F-Y", title: "Hotovo karta", deadline: "2026-12-01", expect_oid: "y" }),
      task({ id: "F-D", title: "Bez data" }),
    ], api);
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    const ready = screen.getByRole("button", { name: "F-Y — Hotovo karta" }).closest("article");
    fireEvent.click(within(ready).getByRole("button", { name: "Označit hotovo" }));
    expect(api.patch).toHaveBeenCalledWith({
      path: "02-PROJEKTY/finance/tasks/F-Y.md",
      patch: { status: "Done" },
      expect_oid: "y",
    });
    const empty = screen.getByRole("button", { name: "F-D — Bez data" }).closest("article");
    fireEvent.click(within(empty).getByRole("button", { name: "Přesunout na Doing" }));
    fireEvent.click(screen.getByRole("button", { name: "Potvrdit" }));
    expect(api.patch).toHaveBeenCalledTimes(1);
    fireEvent.change(screen.getByLabelText("Datum deadline"), { target: { value: "2026-11-02" } });
    fireEvent.click(screen.getByRole("button", { name: "Potvrdit" }));
    expect(api.patch).toHaveBeenLastCalledWith({
      path: "02-PROJEKTY/finance/tasks/F-D.md",
      patch: { status: "Doing", deadline: "2026-11-02" },
      expect_oid: "",
    });
  });

  it("B34 offers force-save with the new oid, and Upravit sends nothing", async () => {
    const api = {
      patch: vi.fn().mockResolvedValue({
        ok: false,
        error_reason: "oid_mismatch",
        oid: "oid-new",
        current: { title: "Původní" },
      }),
    };
    renderApp([task({ id: "F-T1", title: "Původní", expect_oid: "old" })], api);
    fireEvent.click(screen.getByRole("button", { name: "F-T1 — Původní" }));
    fireEvent.change(screen.getByLabelText("Název"), { target: { value: "Nový název" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    });
    expect(screen.getByRole("dialog", { name: "Neshoda verze" })).toBeInTheDocument();
    expect(screen.getByText("U tebe: Nový název")).toBeInTheDocument();
    expect(screen.getByText("Ve vaultu: Původní")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Upravit" }));
    expect(api.patch).toHaveBeenCalledTimes(1);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    });
    fireEvent.click(screen.getByRole("button", { name: "Přesto uložit" }));
    expect(api.patch).toHaveBeenLastCalledWith({
      path: "02-PROJEKTY/finance/tasks/F-T1.md",
      patch: { title: "Nový název" },
      expect_oid: "oid-new",
    });
  });

  it("B40 and B52 show the deadline panel once per save and never force it", async () => {
    const api = {
      patch: vi.fn().mockResolvedValue({
        ok: false,
        error_reason: "deadline_order",
        detail: { message: "F-T1 2026-11-20 > F-E1 2026-11-01" },
      }),
    };
    renderApp([task({ id: "F-T1", title: "Dítě", deadline: "2026-11-20" })], api);
    fireEvent.click(screen.getByRole("button", { name: "F-T1 — Dítě" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    });
    expect(screen.getByRole("dialog", { name: "Pořadí termínů" })).toHaveTextContent("F-T1 2026-11-20");
    expect(screen.queryByRole("button", { name: "Přesto uložit" })).toBeNull();
    expect(api.patch).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    expect(api.patch).toHaveBeenCalledTimes(2);
  });

  it("B48 lets a filled selection go without Od and counts both days", () => {
    renderApp([
      task({ id: "OWN", title: "Vlastní", review_deadline: "2026-11-08" }),
      task({ id: "FILL", title: "Doplnit" }),
      task({ id: "OTHER", title: "Pauza", project: "paused", review_deadline: "2026-11-08" }),
    ]);
    fireEvent.click(screen.getByRole("button", { name: "Úklid" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Vybrat OWN — Vlastní" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Vybrat FILL — Doplnit" }));
    fireEvent.click(screen.getByRole("button", { name: "Náhled" }));
    expect(screen.getByRole("button", { name: "Uložit" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Termín pro výběr"), { target: { value: "2026-11-12" } });
    expect(screen.getByLabelText("Termín OWN")).toHaveValue("2026-11-08");
    expect(screen.getByLabelText("Termín FILL")).toHaveValue("2026-11-12");
    expect(screen.getByRole("button", { name: "Uložit" })).toBeEnabled();
    expect(screen.getByText("Obsazenost 2026-11-08: 2")).toBeInTheDocument();
    expect(screen.getByText("Obsazenost 2026-11-12: 1")).toBeInTheDocument();
  });

  it("B55 keeps a deleted or typed date across refresh and prefills on a new open", () => {
    const data = {
      tasks: [task({ id: "F-T1", title: "Review", review_deadline: "2026-11-03", updated: "2026-10-01" })],
      projects: PROJECTS,
    };
    const view = render(<App exportData={data} today="2026-10-20" />);
    fireEvent.click(screen.getByRole("button", { name: "Úklid" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Vybrat F-T1 — Review" }));
    fireEvent.click(screen.getByRole("button", { name: "Náhled" }));
    expect(screen.getByLabelText("Termín F-T1")).toHaveValue("2026-11-03");
    fireEvent.change(screen.getByLabelText("Termín F-T1"), { target: { value: "" } });
    view.rerender(<App exportData={data} today="2026-10-20" />);
    expect(screen.getByLabelText("Termín F-T1")).toHaveValue("");
    fireEvent.change(screen.getByLabelText("Termín F-T1"), { target: { value: "2026-11-15" } });
    fireEvent.change(screen.getByLabelText("Termín pro výběr"), { target: { value: "2026-11-12" } });
    view.rerender(<App exportData={data} today="2026-10-20" />);
    expect(screen.getByLabelText("Termín F-T1")).toHaveValue("2026-11-15");
    fireEvent.click(screen.getByRole("button", { name: "Zavřít náhled" }));
    fireEvent.click(screen.getByRole("button", { name: "Náhled" }));
    expect(screen.getByLabelText("Termín F-T1")).toHaveValue("2026-11-03");
  });

  it("B18 keeps the failed rows selected and does not draw a force-save dialog", async () => {
    const api = {
      cleanup: vi.fn().mockResolvedValue({
        written: { count: 2, ids: ["A1", "A2"] },
        saved: [],
        failed: ["B1", "B2"],
        pending: ["C1", "C2"],
        expect_oid: { B1: "oid-new", B2: "oid-b2" },
        lines: [],
        dialog: null,
        preview_open: true,
      }),
    };
    renderApp(["A1", "A2", "B1", "B2", "C1", "C2"].map((id) => task({ id, title: id, expect_oid: "old" })), api);
    fireEvent.click(screen.getByRole("button", { name: "Úklid" }));
    for (const id of ["A1", "A2", "B1", "B2", "C1", "C2"]) {
      fireEvent.click(screen.getByRole("checkbox", { name: `Vybrat ${id} — ${id}` }));
      fireEvent.change(screen.getByLabelText(`Akce ${id}`), { target: { value: "done" } });
    }
    fireEvent.click(screen.getByRole("button", { name: "Náhled" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    });
    expect(screen.getByText("Uloženo 2: A1, A2")).toBeInTheDocument();
    expect(screen.queryByRole("checkbox", { name: /A1/ })).toBeNull();
    expect(screen.getByRole("checkbox", { name: "Vybrat B1 — B1" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Vybrat C1 — C1" })).toBeChecked();
    expect(screen.queryByRole("button", { name: "Přesto uložit" })).toBeNull();
    expect(api.cleanup).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    expect(api.cleanup).toHaveBeenCalledTimes(2);
    const second = api.cleanup.mock.calls[1][0].items;
    expect(second.find((item) => item.id === "B1").expect_oid).toBe("oid-new");
    expect(second.map((item) => item.id)).not.toContain("A1");
  });

  it("B56 keeps the selection and shows id and title without an oid dialog", async () => {
    const api = {
      cleanup: vi.fn().mockResolvedValue({
        written: { count: 0, ids: [] },
        saved: [],
        failed: ["F-E1", "F-S2"],
        pending: [],
        expect_oid: {},
        lines: ["F-E1 — Epic", "F-T1 — Dítě"],
        dialog: null,
        error_reason: "open_child_under_closed_parent",
        preview_open: true,
      }),
    };
    renderApp([
      task({ id: "F-E1", type: "epic", title: "Epic" }),
      task({ id: "F-S2", type: "story", title: "Jiná" }),
    ], api);
    fireEvent.click(screen.getByRole("button", { name: "Úklid" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Vybrat F-E1 — Epic" }));
    fireEvent.change(screen.getByLabelText("Akce F-E1"), { target: { value: "cancelled" } });
    fireEvent.click(screen.getByRole("checkbox", { name: "Vybrat F-S2 — Jiná" }));
    fireEvent.change(screen.getByLabelText("Akce F-S2"), { target: { value: "cancelled" } });
    fireEvent.click(screen.getByRole("button", { name: "Náhled" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    });
    expect(screen.getByText("F-T1 — Dítě")).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "Vybrat F-E1 — Epic" })).toBeChecked();
    expect(screen.queryByRole("button", { name: "Přesto uložit" })).toBeNull();
    expect(api.cleanup).toHaveBeenCalledTimes(1);
  });
});
