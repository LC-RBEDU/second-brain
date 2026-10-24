import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import "@testing-library/jest-dom/vitest";
import { App } from "./App.jsx";
import { BusyProvider } from "./BusyContext.jsx";
import { BusyOverlay } from "./BusyOverlay.jsx";

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

function wrap(ui) {
  return (
    <BusyProvider onError={() => {}}>
      {ui}
      <BusyOverlay />
    </BusyProvider>
  );
}

function renderApp(tasks, api = {}, extra = {}) {
  return render(wrap(<App exportData={{ tasks, projects: PROJECTS, ...extra }} api={api} today="2026-10-20" />));
}

describe("screens", () => {
  it("Radar TaskTable shows clickable parent and open children", async () => {
    const api = { item: vi.fn().mockResolvedValue({ ok: true, body: "", oid: "o1" }) };
    renderApp(
      [
        task({ id: "IAD-E1", type: "epic", title: "Epic", deadline: "2026-11-01" }),
        task({
          id: "IAD-S31",
          type: "story",
          title: "Onboarding do Claude Team - 1. vlna",
          parent: "IAD-E1",
          deadline: "2026-10-25",
        }),
        task({ id: "IAD-T1", title: "Podúkol A", parent: "IAD-S31", deadline: "2026-10-24" }),
        task({ id: "IAD-T2", title: "Podúkol B", parent: "IAD-S31", status: "Done", deadline: "2026-10-20" }),
      ],
      api,
    );
    fireEvent.click(screen.getByRole("button", { name: "Radar" }));
    fireEvent.click(screen.getByRole("button", { name: /Due soon/i }));
    const list = screen.getByRole("region", { name: "Seznam" });
    expect(within(list).getByText(/otevřené děti \(1\):/)).toBeInTheDocument();
    expect(within(list).getByRole("button", { name: "IAD-T1" })).toBeInTheDocument();
    expect(within(list).queryByRole("button", { name: "IAD-T2" })).toBeNull();
    expect(within(list).getAllByRole("button", { name: "IAD-E1" }).length).toBeGreaterThanOrEqual(1);
    fireEvent.change(within(list).getByLabelText("Status IAD-S31"), { target: { value: "Done" } });
    const errDialog = screen.getByRole("dialog", { name: "Chyba uložení" });
    expect(within(errDialog).getByText(/Otevřené podúkoly/)).toBeInTheDocument();
    await act(async () => {
      fireEvent.click(within(errDialog).getByRole("button", { name: "IAD-T1 — Podúkol A" }));
    });
    expect(api.item).toHaveBeenCalledWith("IAD-T1");
  });

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

  it("kanban drop changes status and map toggles mindmap", async () => {
    const api = { patch: vi.fn().mockResolvedValue({ ok: true }) };
    renderApp(
      [
        task({ id: "F-E1", type: "epic", title: "Epic" }),
        task({ id: "F-T1", title: "Kartička", parent: "F-E1", status: "Next", deadline: "2026-11-01" }),
      ],
      api,
    );
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    fireEvent.click(screen.getByRole("button", { name: "Kanban" }));
    const card = screen.getByText("F-T1 — Kartička").closest("[data-kanban-card]");
    const doing = screen.getByText("Doing").closest("[data-kanban-column]");
    const dataTransfer = {
      setData: vi.fn(),
      getData: vi.fn(() => "F-T1"),
      effectAllowed: "move",
    };
    fireEvent.dragStart(card, { dataTransfer });
    fireEvent.dragOver(doing, { dataTransfer });
    await act(async () => {
      fireEvent.drop(doing, { dataTransfer });
    });
    expect(api.patch).toHaveBeenCalledWith({
      path: "02-PROJEKTY/finance/tasks/F-T1.md",
      patch: { status: "Doing" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Mapa" }));
    fireEvent.click(screen.getByRole("button", { name: "Mindmapa" }));
    expect(screen.getByLabelText("Mindmapa")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Strom" }));
    expect(screen.getByLabelText("Strom")).toBeInTheDocument();
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
    expect(screen.getAllByText("parent_missing_or_closed").length).toBeGreaterThanOrEqual(1);
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
    fireEvent.click(within(screen.getByLabelText("Akce F-S1")).getByRole("button", { name: "Zrušit" }));
    fireEvent.click(screen.getByRole("button", { name: "Náhled" }));
    const preview = screen.getByRole("region", { name: "Náhled úklidu" });
    expect(within(preview).getByText(/Pauza/)).toBeInTheDocument();
    expect(within(preview).getByText(/Jiný/)).toBeInTheDocument();
    expect(within(preview).getByRole("checkbox", { name: "Náhled F-T3 — Pauza" })).toBeDisabled();
    expect(within(preview).queryByText(/Hotový/)).toBeNull();
  });

  it("Úklid explains actions and opens detail on title double-click", async () => {
    const api = { item: vi.fn().mockResolvedValue({ ok: true, body: "", oid: "o1" }) };
    renderApp([task({ id: "F-T9", title: "T6 C14 guard test" })], api);
    fireEvent.click(screen.getByRole("button", { name: "Úklid" }));
    expect(screen.getByText(/status Done \(skutečně dokončeno\)/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Hotovo" })).toHaveAttribute(
      "title",
      expect.stringMatching(/Done/),
    );
    await act(async () => {
      fireEvent.doubleClick(screen.getByRole("button", { name: "T6 C14 guard test" }));
    });
    expect(api.item).toHaveBeenCalledWith("F-T9");
    expect(screen.getByLabelText("Název")).toHaveValue("T6 C14 guard test");
  });

  it("Zahodit resets dirty detail draft in place; clean Zahodit leaves", async () => {
    const api = {
      item: vi.fn().mockResolvedValue({ ok: true, body: "**Detail:** původní popis\n", oid: "o1" }),
    };
    renderApp([task({ id: "F-T1", title: "Původní", deadline: "2026-11-01" })], api);
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "F-T1 — Původní" }));
    });
    await waitFor(() => expect(screen.getByLabelText("Název")).toHaveValue("Původní"));
    fireEvent.change(screen.getByLabelText("Název"), { target: { value: "Změněný" } });
    fireEvent.click(screen.getByLabelText("Detail úkolu"));
    fireEvent.change(screen.getByLabelText("Detail úkolu"), { target: { value: "nový popis" } });
    expect(screen.getByText(/title:/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Zahodit" }));
    expect(screen.getByRole("region", { name: "Detail" })).toBeInTheDocument();
    expect(screen.getByLabelText("Název")).toHaveValue("Původní");
    expect(screen.getByLabelText("Detail úkolu")).toHaveTextContent("původní popis");
    expect(screen.getByText("Beze změny")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Zahodit" }));
    expect(screen.queryByRole("region", { name: "Detail" })).toBeNull();
  });

  it("Detail / popis shows clickable links in read view", async () => {
    const api = {
      item: vi.fn().mockResolvedValue({
        ok: true,
        body: "**Detail:** Mrkni https://rb-edu.slack.com/archives/C061/p1 a dny.ai\n",
        oid: "o1",
      }),
    };
    renderApp([task({ id: "F-T1", title: "S odkazem" })], api);
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "F-T1 — S odkazem" }));
    });
    await waitFor(() => expect(screen.getByLabelText("Detail úkolu")).toBeInTheDocument());
    const slack = screen.getByRole("link", {
      name: "https://rb-edu.slack.com/archives/C061/p1",
    });
    expect(slack).toHaveAttribute("href", "https://rb-edu.slack.com/archives/C061/p1");
    expect(slack).toHaveAttribute("target", "_blank");
    const bare = screen.getByRole("link", { name: "dny.ai" });
    expect(bare).toHaveAttribute("href", "https://dny.ai/");
  });

  it("Chybně zadané shows rule glossary", () => {
    renderApp([
      task({
        id: "F-T8",
        title: "Stale row",
        status: "Next",
        updated: "2026-08-01",
      }),
    ]);
    fireEvent.click(screen.getByRole("button", { name: "Chybně zadané" }));
    fireEvent.click(screen.getByText("Co znamenají pravidla"));
    expect(screen.getByText(/Next nebo Doing — pole updated starší/)).toBeInTheDocument();
    expect(screen.getByTitle(/30 dní/)).toBeInTheDocument();
  });

  it("B27 sends Done as status only and ignores an empty Doing confirm", async () => {
    const api = { patch: vi.fn().mockResolvedValue({ ok: true, oid: "next" }) };
    renderApp([
      task({ id: "F-Y", title: "Hotovo karta", deadline: "2026-12-01", expect_oid: "y" }),
      task({ id: "F-D", title: "Bez data" }),
    ], api);
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    fireEvent.change(screen.getByLabelText("Status F-Y"), { target: { value: "Done" } });
    expect(api.patch).toHaveBeenCalledWith({
      path: "02-PROJEKTY/finance/tasks/F-Y.md",
      patch: { status: "Done" },
      expect_oid: "y",
    });
    await waitFor(() => expect(screen.getByLabelText("Status F-D")).not.toBeDisabled());
    fireEvent.change(screen.getByLabelText("Status F-D"), { target: { value: "Doing" } });
    fireEvent.click(screen.getByRole("button", { name: "Potvrdit" }));
    expect(api.patch).toHaveBeenCalledTimes(1);
    fireEvent.change(screen.getByLabelText("Datum deadline"), { target: { value: "2026-11-02" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Potvrdit" }));
    });
    await waitFor(() => expect(api.patch).toHaveBeenCalledTimes(2));
    expect(api.patch).toHaveBeenLastCalledWith({
      path: "02-PROJEKTY/finance/tasks/F-D.md",
      patch: { status: "Doing", deadline: "2026-11-02" },
    });
    await waitFor(() => expect(screen.getByLabelText("Status F-D")).not.toBeDisabled());
    fireEvent.change(screen.getByLabelText("Status F-D"), { target: { value: "Waiting" } });
    expect(screen.getByRole("dialog", { name: "Doplň waitUntil" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Potvrdit" }));
    expect(api.patch).toHaveBeenCalledTimes(2);
  });

  it("B34 offers force-save with the new oid, and Upravit sends nothing", async () => {
    const api = {
      patch: vi.fn().mockResolvedValue({
        ok: false,
        error_reason: "oid_mismatch",
        oid: "oid-new",
        current: { title: "Někdo jiný změnil" },
      }),
    };
    renderApp([task({ id: "F-T1", title: "Původní", expect_oid: "old" })], api);
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "F-T1 — Původní" }));
    });
    fireEvent.change(screen.getByLabelText("Název"), { target: { value: "Nový název" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    });
    expect(screen.getByRole("dialog", { name: "Neshoda verze" })).toBeInTheDocument();
    expect(screen.getByText(/Konflikt:/)).toBeInTheDocument();
    expect(screen.getByText("Tvůj návrh")).toBeInTheDocument();
    expect(screen.getByText("Ve vaultu teď")).toBeInTheDocument();
    expect(screen.getByText("Nový název")).toBeInTheDocument();
    expect(screen.getByText("Někdo jiný změnil")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Zrušit konflikt" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Zpět k formuláři" }));
    expect(api.patch).toHaveBeenCalledTimes(1);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    });
    fireEvent.click(screen.getByRole("button", { name: "Přesto uložit" }));
    expect(api.patch).toHaveBeenLastCalledWith({
      path: "02-PROJEKTY/finance/tasks/F-T1.md",
      patch: { title: "Nový název", status: "Next" },
      expect_oid: "oid-new",
    });
  });

  it("stale oid with unchanged vault content auto-retries without conflict dialog", async () => {
    const api = {
      patch: vi
        .fn()
        .mockResolvedValueOnce({
          ok: false,
          error_reason: "oid_mismatch",
          oid: "oid-new",
          current: { title: "Hotovo karta", status: "Next" },
        })
        .mockResolvedValueOnce({ ok: true, oid: "oid-written" }),
      item: vi.fn().mockResolvedValue({
        body: "",
        frontmatter: { title: "Hotovo karta", status: "Next" },
      }),
    };
    renderApp([task({ id: "F-Y", title: "Hotovo karta", status: "Next", expect_oid: "stale" })], api);
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "F-Y — Hotovo karta" }));
    });
    fireEvent.change(screen.getByLabelText("Status"), { target: { value: "Done" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    });
    expect(screen.queryByRole("dialog", { name: "Neshoda verze" })).toBeNull();
    expect(api.patch).toHaveBeenCalledTimes(2);
    expect(api.patch).toHaveBeenLastCalledWith({
      path: "02-PROJEKTY/finance/tasks/F-Y.md",
      patch: { title: "Hotovo karta", status: "Done" },
      expect_oid: "oid-new",
    });
  });

  it("CAS-only oid mismatch with matching fields saves without conflict dialog", async () => {
    const api = {
      patch: vi
        .fn()
        .mockResolvedValueOnce({
          ok: false,
          error_reason: "oid_mismatch",
          oid: "oid-new",
        })
        .mockResolvedValueOnce({ ok: true, oid: "oid-written" }),
      item: vi.fn().mockResolvedValue({
        body: "",
        oid: "oid-new",
        frontmatter: {
          title: "Stejný",
          status: "Next",
          // datetime vs date10 baseline → concurrent true, but proposal matches vault
          deadline: "2026-10-01T00:00:00",
          review_deadline: "",
          waitUntil: "",
          parent: "",
        },
      }),
    };
    renderApp(
      [task({ id: "F-C", title: "Stejný", status: "Next", deadline: "2026-10-01", expect_oid: "stale" })],
      api,
    );
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "F-C — Stejný" }));
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    });
    expect(screen.queryByRole("dialog", { name: "Neshoda verze" })).toBeNull();
    expect(api.patch).toHaveBeenCalledTimes(2);
    expect(api.patch).toHaveBeenLastCalledWith({
      path: "02-PROJEKTY/finance/tasks/F-C.md",
      patch: { title: "Stejný", status: "Next" },
      expect_oid: "oid-new",
    });
  });

  it("T3 shows error dialog when patch returns ok false without error_reason", async () => {
    const api = {
      patch: vi.fn().mockResolvedValue({ ok: false }),
    };
    renderApp([task({ id: "F-T1", title: "Úkol", expect_oid: "o1" })], api);
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "F-T1 — Úkol" }));
    });
    await waitFor(() => expect(screen.getByRole("button", { name: "Uložit" })).not.toBeDisabled());
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    });
    expect(await screen.findByRole("dialog", { name: "Chyba uložení" })).toHaveTextContent(/Uložení selhalo/);
  });

  it("shows an error dialog when Done is blocked by open children", async () => {
    const api = {
      patch: vi.fn().mockResolvedValue({
        ok: false,
        error_reason: "open_child_under_closed_parent",
        detail: { parent_id: "F-S1", child_ids: ["F-T2"] },
      }),
    };
    renderApp([task({ id: "F-S1", type: "story", title: "Story s dětmi", expect_oid: "s1" })], api);
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "F-S1 — Story s dětmi" }));
    });
    fireEvent.change(screen.getByLabelText("Status"), { target: { value: "Done" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    });
    expect(screen.getByRole("dialog", { name: "Chyba uložení" })).toHaveTextContent("F-T2");
    expect(screen.queryByRole("dialog", { name: "Neshoda verze" })).toBeNull();
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
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "F-T1 — Dítě" }));
    });
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
    const view = render(wrap(<App exportData={data} today="2026-10-20" />));
    fireEvent.click(screen.getByRole("button", { name: "Úklid" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Vybrat F-T1 — Review" }));
    fireEvent.click(screen.getByRole("button", { name: "Náhled" }));
    expect(screen.getByLabelText("Termín F-T1")).toHaveValue("2026-11-03");
    fireEvent.change(screen.getByLabelText("Termín F-T1"), { target: { value: "" } });
    view.rerender(wrap(<App exportData={data} today="2026-10-20" />));
    expect(screen.getByLabelText("Termín F-T1")).toHaveValue("");
    fireEvent.change(screen.getByLabelText("Termín F-T1"), { target: { value: "2026-11-15" } });
    fireEvent.change(screen.getByLabelText("Termín pro výběr"), { target: { value: "2026-11-12" } });
    view.rerender(wrap(<App exportData={data} today="2026-10-20" />));
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
      fireEvent.click(within(screen.getByLabelText(`Akce ${id}`)).getByRole("button", { name: "Hotovo" }));
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
    fireEvent.click(within(screen.getByLabelText("Akce F-E1")).getByRole("button", { name: "Zrušit" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Vybrat F-S2 — Jiná" }));
    fireEvent.click(within(screen.getByLabelText("Akce F-S2")).getByRole("button", { name: "Zrušit" }));
    fireEvent.click(screen.getByRole("button", { name: "Náhled" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    });
    expect(screen.getByText("F-T1 — Dítě")).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "Vybrat F-E1 — Epic" })).toBeChecked();
    expect(screen.queryByRole("button", { name: "Přesto uložit" })).toBeNull();
    expect(api.cleanup).toHaveBeenCalledTimes(1);
  });

  it("B19 proposes the current Prague week and shows the task limit without force-save", async () => {
    const api = {
      propose: vi.fn()
        .mockResolvedValueOnce({ ok: false, error_reason: "focus_limit_exceeded" })
        .mockResolvedValueOnce({ ok: true, proposal_id: "p1" }),
      apply: vi.fn().mockResolvedValue({ ok: true }),
    };
    renderApp([task({ id: "F-T1", title: "Focus karta" })], api);
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "F-T1 — Focus karta" }));
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Focus F-T1" }));
    });
    expect(api.propose).toHaveBeenCalledWith({
      task_path: "02-PROJEKTY/finance/tasks/F-T1.md",
      expect_oid: "",
      focus_week: "2026-W43",
    });
    expect(screen.getByText("Focus už má 10 tasků")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Přesto uložit" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Použít focus" })).toBeNull();
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Focus F-T1" }));
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Použít focus" }));
    });
    expect(api.apply).toHaveBeenCalledWith({ proposal_id: "p1" });
  });

  it("A16 shows the six fields from the vault item", async () => {
    const api = {
      patch: vi.fn().mockResolvedValue({ ok: false, error_reason: "oid_mismatch", oid: "oid-new" }),
      item: vi.fn().mockResolvedValue({
        body: "**Detail:** poznámka k úkolu\n",
        frontmatter: {
          title: "Původní",
          status: "Next",
          deadline: "2026-10-01",
          review_deadline: "2026-11-01",
          waitUntil: "",
          parent: "[[F-S1]]",
        },
      }),
    };
    renderApp([task({ id: "F-T1", title: "Původní" })], api);
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "F-T1 — Původní" }));
    });
    expect(api.item).toHaveBeenCalledWith("F-T1");
    expect(screen.getByLabelText("Detail úkolu")).toHaveTextContent("poznámka k úkolu");
    fireEvent.change(screen.getByLabelText("Název"), { target: { value: "Nový název" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    });
    expect(api.item).toHaveBeenCalledWith("F-T1");
    expect(screen.getByText(/Konflikt:/)).toBeInTheDocument();
    expect(screen.getByText("Tvůj návrh")).toBeInTheDocument();
    expect(screen.getByText("Nový název")).toBeInTheDocument();
    expect(screen.getByText("Původní")).toBeInTheDocument();
    expect(screen.queryByText("status: Next / Next")).toBeNull();
  });

  it("Q2 changes the parent from the detail and the kanban does not", async () => {
    const api = { patch: vi.fn().mockResolvedValue({ ok: true }) };
    renderApp([
      task({ id: "F-E1", type: "epic", title: "Epic" }),
      task({ id: "F-S1", type: "story", title: "Story", parent: "F-E1" }),
      task({ id: "F-S2", type: "story", title: "Jiná", parent: "F-E1" }),
      task({ id: "F-T1", type: "task", title: "Dítě", parent: "F-S1" }),
    ], api);
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "F-T1 — Dítě" }));
    });
    expect(screen.getByLabelText("Parent úkolu")).toHaveValue("F-S1");
    fireEvent.change(screen.getByLabelText("Parent úkolu"), { target: { value: "F-S2" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    });
    expect(api.patch).toHaveBeenLastCalledWith({
      path: "02-PROJEKTY/finance/tasks/F-T1.md",
      patch: { title: "Dítě", status: "Next", parent: "F-S2" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "F-E1 — Epic" }));
    });
    expect(screen.queryByLabelText("Parent úkolu")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    fireEvent.change(screen.getByLabelText("Status F-T1"), { target: { value: "Backlog" } });
    expect(api.patch).toHaveBeenLastCalledWith({
      path: "02-PROJEKTY/finance/tasks/F-T1.md",
      patch: { status: "Backlog" },
    });
  });

  it("detail shows Children with title and back navigates parent→child history", async () => {
    const api = { item: vi.fn().mockResolvedValue({ ok: true, body: "", oid: "o1" }) };
    renderApp(
      [
        task({ id: "F-E1", type: "epic", title: "Epic One" }),
        task({ id: "F-S1", type: "story", title: "Story One", parent: "F-E1" }),
        task({ id: "F-T1", type: "task", title: "Leaf One", parent: "F-S1" }),
      ],
      api,
    );
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "F-S1 — Story One" }));
    });
    expect(screen.getByLabelText("Detail")).toBeInTheDocument();
    expect(screen.getByLabelText("Otevřít parent F-E1 — Epic One")).toBeInTheDocument();
    const children = screen.getByLabelText("Children");
    expect(within(children).getByRole("button", { name: "Otevřít child F-T1 — Leaf One" })).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(within(children).getByRole("button", { name: "Otevřít child F-T1 — Leaf One" }));
    });
    expect(screen.getByText("F-T1")).toBeInTheDocument();
    expect(screen.getByLabelText("Název")).toHaveValue("Leaf One");

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Zpět" }));
    });
    expect(screen.getByText("F-S1")).toBeInTheDocument();
    expect(screen.getByLabelText("Název")).toHaveValue("Story One");
  });

  it("B45 keeps the preview when the family is over 80 and when the server rejects it", async () => {
    const api = { cleanup: vi.fn().mockResolvedValue({ ok: false, error_reason: "batch_too_large" }) };
    const children = Array.from({ length: 80 }, (_, index) => task({
      id: `F-T${index}`,
      title: `Dítě ${index}`,
      parent: "F-S1",
    }));
    renderApp([task({ id: "F-S1", type: "story", title: "Rodič" }), ...children], api);
    fireEvent.click(screen.getByRole("button", { name: "Úklid" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Vybrat F-S1 — Rodič" }));
    fireEvent.click(within(screen.getByLabelText("Akce F-S1")).getByRole("button", { name: "Hotovo" }));
    fireEvent.click(screen.getByRole("button", { name: "Náhled" }));
    expect(screen.getByText("Rodina je nad 80. Odeber předka.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Uložit" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    expect(api.cleanup).not.toHaveBeenCalled();
    expect(screen.getByRole("checkbox", { name: "Vybrat F-S1 — Rodič" })).toBeChecked();
    cleanup();
    const small = {
      cleanup: vi.fn().mockImplementation(async (body) => {
        if (!body.items?.length) return { ok: true, written: { count: 0, ids: [] }, failed: [], pending: [] };
        return { ok: false, error_reason: "batch_too_large" };
      }),
    };
    renderApp([task({ id: "F-S1", type: "story", title: "Rodič" })], small);
    fireEvent.click(screen.getByRole("button", { name: "Úklid" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Vybrat F-S1 — Rodič" }));
    fireEvent.click(within(screen.getByLabelText("Akce F-S1")).getByRole("button", { name: "Hotovo" }));
    fireEvent.click(screen.getByRole("button", { name: "Náhled" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
    });
    expect(small.cleanup).toHaveBeenCalledTimes(2);
    expect(small.cleanup.mock.calls[1][0].items.map((item) => item.id)).toEqual(["F-S1"]);
    expect(screen.getByRole("region", { name: "Náhled úklidu" })).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "Vybrat F-S1 — Rodič" })).toBeChecked();
  });
});
