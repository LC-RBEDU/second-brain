import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import "@testing-library/jest-dom/vitest";
import { App } from "./App.jsx";
import { BusyProvider, SHOW_DELAY_MS, MIN_VISIBLE_MS, useBusy } from "./BusyContext.jsx";
import { BusyOverlay } from "./BusyOverlay.jsx";

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

const PROJECTS = [{ slug: "finance", hierarchy: true, status: "active" }];

function task(fields) {
  return {
    type: "task",
    status: "Next",
    project: "finance",
    title: fields.id,
    path: `02-PROJEKTY/finance/tasks/${fields.id}.md`,
    expect_oid: "oid-1",
    ...fields,
  };
}

function wrap(ui, onError = () => {}) {
  return (
    <BusyProvider onError={onError}>
      {ui}
      <BusyOverlay />
    </BusyProvider>
  );
}

function Probe({ run }) {
  const { withBusy, isBusy } = useBusy();
  return (
    <div>
      <button type="button" disabled={isBusy} onClick={() => run(withBusy)}>
        Go
      </button>
      <span data-testid="busy-flag">{isBusy ? "yes" : "no"}</span>
    </div>
  );
}

describe("busy overlay", () => {
  it("T9 shows overlay after 150ms and keeps it at least 200ms", async () => {
    vi.useFakeTimers();
    let resolveFn;
    const slow = () =>
      new Promise((resolve) => {
        resolveFn = resolve;
      });
    render(
      wrap(
        <Probe
          run={(withBusy) => {
            withBusy("Ukládám…", "Zapisuji změnu do vaultu", slow);
          }}
        />,
      ),
    );
    fireEvent.click(screen.getByRole("button", { name: "Go" }));
    expect(document.querySelector("#busy")).toBeNull();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(SHOW_DELAY_MS - 1);
    });
    expect(document.querySelector("#busy")).toBeNull();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    const overlay = document.querySelector("#busy");
    expect(overlay).toBeTruthy();
    expect(overlay.querySelector("[data-busy-text]")?.textContent).toBe("Ukládám…");
    expect(overlay.querySelector("[data-busy-subtitle]")?.textContent).toBe("Zapisuji změnu do vaultu");
    await act(async () => {
      resolveFn();
      await Promise.resolve();
    });
    expect(document.querySelector("#busy")).toBeTruthy();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(MIN_VISIBLE_MS);
    });
    expect(document.querySelector("#busy")).toBeNull();
  });

  it("T11 SSOT selectors include non-empty subtitle", async () => {
    vi.useFakeTimers();
    let resolveFn;
    render(
      wrap(
        <Probe
          run={(withBusy) => {
            withBusy("Ukládám…", "Ukládám změnu úkolu", () => new Promise((r) => (resolveFn = r)));
          }}
        />,
      ),
    );
    fireEvent.click(screen.getByRole("button", { name: "Go" }));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(SHOW_DELAY_MS);
    });
    const overlay = document.querySelector("#busy.busy-overlay");
    expect(overlay).toBeTruthy();
    expect(overlay.getAttribute("role")).toBe("status");
    expect(overlay.getAttribute("aria-busy")).toBe("true");
    expect(overlay.querySelector(".busy-card")).toBeTruthy();
    expect(overlay.querySelector(".busy-pulse")).toBeTruthy();
    expect(overlay.querySelector("img.busy-logo")?.getAttribute("src")).toBe("/logo.svg");
    expect(overlay.querySelector("[data-busy-subtitle]")?.textContent?.trim()).toBeTruthy();
    expect(overlay.querySelector(".busy-bar")).toBeTruthy();
    await act(async () => {
      resolveFn();
      await vi.advanceTimersByTimeAsync(MIN_VISIBLE_MS);
    });
  });

  it("T9b keeps busy until export resolves and calls export once", async () => {
    vi.useFakeTimers();
    let resolveExport;
    const onRefresh = vi.fn(
      () =>
        new Promise((resolve) => {
          resolveExport = resolve;
        }),
    );
    const api = {
      patch: vi.fn().mockResolvedValue({ ok: true, oid: "oid-2" }),
    };
    render(
      wrap(
        <App
          exportData={{ tasks: [task({ id: "T1", title: "Úkol" })], projects: PROJECTS }}
          api={api}
          today="2026-10-20"
          onRefresh={onRefresh}
        />,
      ),
    );
    fireEvent.click(screen.getByRole("button", { name: "Projekt" }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "T1 — Úkol" }));
      await vi.advanceTimersByTimeAsync(SHOW_DELAY_MS + MIN_VISIBLE_MS);
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Uložit" }));
      await Promise.resolve();
      await vi.advanceTimersByTimeAsync(SHOW_DELAY_MS);
    });
    expect(document.querySelector("#busy")).toBeTruthy();
    expect(api.patch).toHaveBeenCalledTimes(1);
    expect(onRefresh).toHaveBeenCalledTimes(1);
    expect(document.querySelector("#busy")).toBeTruthy();
    await act(async () => {
      resolveExport();
      await Promise.resolve();
      await vi.advanceTimersByTimeAsync(MIN_VISIBLE_MS);
    });
    expect(document.querySelector("#busy")).toBeNull();
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it("T10 drops a second concurrent user withBusy", async () => {
    vi.useFakeTimers();
    const calls = [];
    let resolveFirst;
    function Harness() {
      const { withBusy } = useBusy();
      return (
        <button
          type="button"
          onClick={() => {
            withBusy("A", "a", () => {
              calls.push("a");
              return new Promise((r) => (resolveFirst = r));
            });
            withBusy("B", "b", async () => {
              calls.push("b");
            });
          }}
        >
          Dual
        </button>
      );
    }
    render(wrap(<Harness />));
    fireEvent.click(screen.getByRole("button", { name: "Dual" }));
    expect(calls).toEqual(["a"]);
    // Sync double-activate (Playwright save.click(); save.click())
    fireEvent.click(screen.getByRole("button", { name: "Dual" }));
    expect(calls).toEqual(["a"]);
    await act(async () => {
      resolveFirst();
      await vi.advanceTimersByTimeAsync(MIN_VISIBLE_MS + SHOW_DELAY_MS);
    });
    expect(calls).toEqual(["a"]);
  });

  it("T12 createTask guards and create failures show error dialog", async () => {
    const api = {
      create: vi.fn().mockResolvedValue({ ok: false }),
    };
    render(
      wrap(
        <App
          exportData={{ tasks: [task({ id: "T1", title: "Úkol" })], projects: PROJECTS }}
          api={api}
          today="2026-10-20"
        />,
      ),
    );
    fireEvent.click(screen.getByRole("button", { name: "Nový task" }));
    fireEvent.change(screen.getByLabelText("Název nového tasku"), { target: { value: "Nový" } });
    fireEvent.change(screen.getByLabelText("Stav nového tasku"), { target: { value: "Doing" } });
    fireEvent.click(screen.getByRole("button", { name: "Založit" }));
    expect(api.create).not.toHaveBeenCalled();
    expect(await screen.findByText(/Doing vyžaduje deadline/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Zavřít" }));
    fireEvent.change(screen.getByLabelText("Stav nového tasku"), { target: { value: "Waiting" } });
    fireEvent.click(screen.getByRole("button", { name: "Založit" }));
    expect(api.create).not.toHaveBeenCalled();
    expect(await screen.findByText(/Waiting vyžaduje datum waitUntil/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Zavřít" }));
    fireEvent.change(screen.getByLabelText("Stav nového tasku"), { target: { value: "Next" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Založit" }));
    });
    expect(api.create).toHaveBeenCalled();
    expect(await screen.findByRole("dialog", { name: "Chyba uložení" })).toBeInTheDocument();
  });

  it("T9c clears busy on unmount mid-operation", async () => {
    vi.useFakeTimers();
    let resolveFn;
    const { unmount } = render(
      wrap(
        <Probe
          run={(withBusy) => {
            withBusy("Ukládám…", "Zapisuji změnu do vaultu", () => new Promise((r) => (resolveFn = r)));
          }}
        />,
      ),
    );
    fireEvent.click(screen.getByRole("button", { name: "Go" }));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(SHOW_DELAY_MS);
    });
    expect(document.querySelector("#busy")).toBeTruthy();
    unmount();
    expect(document.querySelector("#busy")).toBeNull();
    await act(async () => {
      resolveFn?.();
      await vi.advanceTimersByTimeAsync(MIN_VISIBLE_MS);
    });
  });
});
