import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

const BusyContext = createContext(null);

export const SHOW_DELAY_MS = 150;
export const MIN_VISIBLE_MS = 200;

/** Cross-instance mutex for sync double-clicks. Cleared on Provider unmount (StrictMode off in main). */
let globalBusyHeld = false;

export function BusyProvider({ children, onError }) {
  const [busy, setBusy] = useState(null);
  const [locked, setLocked] = useState(false);
  const propErrorRef = useRef(onError);
  const handlerRef = useRef(null);
  const depthRef = useRef(0);
  const generationRef = useRef(0);
  const showTimerRef = useRef(null);
  const shownAtRef = useRef(0);
  const titleRef = useRef({ title: "", subtitle: "" });
  const nestingAllowedRef = useRef(false);

  useEffect(() => {
    propErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    return () => {
      if (showTimerRef.current) clearTimeout(showTimerRef.current);
      generationRef.current += 1;
      depthRef.current = 0;
      shownAtRef.current = 0;
      nestingAllowedRef.current = false;
      globalBusyHeld = false;
    };
  }, []);

  const reportError = useCallback((message) => {
    const fn = handlerRef.current || propErrorRef.current;
    fn?.(message || "Uložení selhalo (síť nebo server).");
  }, []);

  const setErrorHandler = useCallback((handler) => {
    handlerRef.current = handler;
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
      if (depthRef.current > 0 || globalBusyHeld) {
        // Nested export refresh (C12): only while outer fn is on the call stack.
        if (options.reentrant && nestingAllowedRef.current) return fn();
        return undefined;
      }
      // Module mutex first — sync double-clicks / remounts must drop before setState.
      globalBusyHeld = true;
      depthRef.current = 1;
      const gen = ++generationRef.current;
      setLocked(true);
      titleRef.current = { title: title || "Ukládám…", subtitle: subtitle || "Chvilku to trvá…" };
      showTimerRef.current = setTimeout(() => {
        if (generationRef.current !== gen || depthRef.current === 0) return;
        shownAtRef.current = Date.now();
        setBusy({ ...titleRef.current });
      }, SHOW_DELAY_MS);
      try {
        nestingAllowedRef.current = true;
        const result = await fn();
        nestingAllowedRef.current = false;
        if (generationRef.current !== gen) return undefined;
        return result;
      } catch (err) {
        nestingAllowedRef.current = false;
        if (generationRef.current !== gen) return undefined;
        const msg =
          err?.message === "load_failed"
            ? "Načtení selhalo (síť nebo server)."
            : "Uložení selhalo (síť nebo server).";
        reportError(msg);
        return undefined;
      } finally {
        nestingAllowedRef.current = false;
        await hideBusy(gen);
        if (generationRef.current === gen) {
          depthRef.current = 0;
          globalBusyHeld = false;
        }
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
