import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import "@testing-library/jest-dom/vitest";
import { useCallback, useEffect, useState } from "react";
import { BusyOverlay } from "./BusyOverlay.jsx";
import { BusyProvider, useBusy } from "./BusyContext.jsx";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

/** Minimal Boot harness mirroring main.jsx error bridge (T15b). */
function BootHarness() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const { withBusy, setErrorHandler } = useBusy();

  useEffect(() => {
    if (data) return undefined;
    setErrorHandler((message) => setError(message || "Export se nenačetl"));
    return undefined;
  }, [data, setErrorHandler]);

  const load = useCallback(async () => {
    const run = async () => {
      const response = await fetch("/api/export");
      if (!response.ok) throw new Error("load_failed");
      setData(await response.json());
      setError("");
    };
    return withBusy("Načítám…", "Stahuji export otevřených úkolů", run, { reentrant: true });
  }, [withBusy]);

  useEffect(() => {
    load();
  }, [load]);

  if (!data) {
    return (
      <>
        {error ? <p className="p-4 text-sm text-red-700">{error}</p> : null}
        <BusyOverlay />
      </>
    );
  }
  return <p>loaded</p>;
}

describe("Boot busy bridge T15b", () => {
  it("shows Boot setError text on export fail without App dialog", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({}),
      }),
    );
    render(
      <BusyProvider onError={() => {}}>
        <BootHarness />
      </BusyProvider>,
    );
    await waitFor(() => {
      expect(screen.getByText(/Načtení selhalo/i)).toBeInTheDocument();
    });
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
