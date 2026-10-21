import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

const BusyContext = createContext(null);

export const SHOW_DELAY_MS = 150;
export const MIN_VISIBLE_MS = 200;

export function BusyProvider({ children, onError }) {
  const [busy, setBusy] = useState(null);
  const [locked, setLocked] = useState(false);
  const onErrorRef = useRef(onError);
  const depthRef = useRef(0);
  const generationRef = useRef(0);
  const showTimerRef = useRef(null);
  const shownAtRef = useRef(0);
  const titleRef = useRef({ title: "", subtitle: "" });

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    return () => {
      if (showTimerRef.current) clearTimeout(showTimerRef.current);
      generationRef.current += 1;
      depthRef.current = 0;
    };
  }, []);

  const reportError = useCallback((message) => {
    onErrorRef.current?.(message || "Uložení selhalo (síť nebo server).");
  }, []);

  const setErrorHandler = useCallback((handler) => {
    onErrorRef.current = handler;
  }, []);

  const hideBusy = useCallback(async (gen) => {
    if (showTimerRef.current) {
      clearTimeout(showTimerRef.current);
      showTimerRef.current = null;
    }
    if (shownAtRef.current) {
      const elapsed = Date.now() - shownAtRef.current;
      if (elapsed < MIN_VISIBLE_MS) {
        await new Promise((resolve) => setTimeout(resolve, MIN_VISIBLE_MS - elapsed));
      }
    }
    if (generationRef.current !== gen) return;
    shownAtRef.current = 0;
    setBusy(null);
    setLocked(false);
  }, []);

  const withBusy = useCallback(
    async (title, subtitle, fn, options = {}) => {
      if (depthRef.current > 0) {
        // Nested export refresh (C12): same slot. Other concurrent user calls drop.
        if (options.reentrant) return fn();
        return undefined;
      }
      depthRef.current = 1;
      setLocked(true);
      const gen = generationRef.current;
      titleRef.current = { title: title || "Ukládám…", subtitle: subtitle || "Chvilku to trvá…" };
      showTimerRef.current = setTimeout(() => {
        if (generationRef.current !== gen || depthRef.current === 0) return;
        shownAtRef.current = Date.now();
        setBusy({ ...titleRef.current });
      }, SHOW_DELAY_MS);
      try {
        return await fn();
      } catch (err) {
        const msg =
          err?.message === "load_failed"
            ? "Načtení selhalo (síť nebo server)."
            : "Uložení selhalo (síť nebo server).";
        reportError(msg);
        return undefined;
      } finally {
        depthRef.current = 0;
        await hideBusy(gen);
      }
    },
    [hideBusy, reportError],
  );

  const value = {
    busy,
    locked,
    isBusy: locked || Boolean(busy),
    withBusy,
    reportError,
    setErrorHandler,
  };

  return <BusyContext.Provider value={value}>{children}</BusyContext.Provider>;
}

export function useBusy() {
  const ctx = useContext(BusyContext);
  if (!ctx) throw new Error("useBusy requires BusyProvider");
  return ctx;
}

export function useBusyOptional() {
  return useContext(BusyContext);
}
