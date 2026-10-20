import { StrictMode, useCallback, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./ui/App.jsx";
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
};

function Boot() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    const response = await fetch("/api/export");
    if (response.status === 401) {
      window.location.assign("/oauth/authorize");
      return;
    }
    if (!response.ok) {
      setError("Export se nenačetl");
      return;
    }
    setData(await response.json());
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (!data) return <p>{error || "Načítám"}</p>;
  return <App exportData={data} api={api} today={pragueToday()} onRefresh={load} />;
}

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(
    <StrictMode>
      <Boot />
    </StrictMode>,
  );
}
