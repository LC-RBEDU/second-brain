import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./ui/App.jsx";
import "./index.css";

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(
    <StrictMode>
      <App exportData={{ tasks: [], projects: [] }} />
    </StrictMode>,
  );
}
