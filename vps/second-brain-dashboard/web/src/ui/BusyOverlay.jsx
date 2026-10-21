import { useBusyOptional } from "./BusyContext.jsx";

export function BusyOverlay() {
  const ctx = useBusyOptional();
  if (!ctx?.busy) return null;
  const { title, subtitle } = ctx.busy;
  return (
    <div
      id="busy"
      role="status"
      aria-live="polite"
      aria-busy="true"
      className="busy-overlay"
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.preventDefault();
          event.stopPropagation();
        }
      }}
    >
      <div className="busy-card">
        <div className="busy-icon">
          <div className="busy-pulse" aria-hidden="true" />
          <svg className="busy-spin" viewBox="0 0 64 64" fill="none" aria-hidden="true">
            <circle cx="32" cy="32" r="28" stroke="currentColor" strokeOpacity="0.15" strokeWidth="4" />
            <path d="M60 32A28 28 0 0 0 32 4" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
          </svg>
          <img src="/logo.svg" alt="" className="busy-logo" />
        </div>
        <p data-busy-text className="busy-title">
          {title}
        </p>
        <p data-busy-subtitle className="busy-subtitle">
          {subtitle}
        </p>
        <div className="busy-bar-track">
          <div className="busy-bar" />
        </div>
      </div>
    </div>
  );
}
