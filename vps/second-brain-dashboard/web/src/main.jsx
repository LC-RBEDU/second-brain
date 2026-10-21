import { StrictMode, useCallback, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./ui/App.jsx";
import { BusyOverlay } from "./ui/BusyOverlay.jsx";
import { BusyProvider, useBusy } from "./ui/BusyContext.jsx";
import "./index.css";

function pragueToday() {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Prague" }).format(new Date());
}

async function readJson(response) {
  const body = await response.json().catch(() => ({}));
  return { ok: response.ok, ...body };
}

const api = {
  patch(body) {
    return fetch("/api/tasks", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(readJson);
  },
  cleanup(body) {
    return fetch("/api/cleanup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(readJson);
  },
  create(body) {
    return fetch("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(readJson);
  },
  item(taskId) {
    return fetch(`/api/tasks/item?task_id=${encodeURIComponent(taskId)}`).then(readJson);
  },
  editBody(body) {
    return fetch("/api/tasks/edit-body", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(readJson);
  },
  propose(body) {
    return fetch("/api/focus/propose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(readJson);
  },
  apply(body) {
    return fetch("/api/focus/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(readJson);
  },
};

function Boot() {
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
      if (response.status === 401) {
        window.location.assign("/oauth/authorize");
        return;
      }
      if (!response.ok) {
        throw new Error("load_failed");
      }
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
  return (
    <>
      <App exportData={data} api={api} today={pragueToday()} onRefresh={load} />
      <BusyOverlay />
    </>
  );
}

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(
    <StrictMode>
      <BusyProvider onError={() => {}}>
        <Boot />
      </BusyProvider>
    </StrictMode>,
  );
}
