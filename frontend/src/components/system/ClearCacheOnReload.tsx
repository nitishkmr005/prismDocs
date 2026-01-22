"use client";

import { useEffect, useRef } from "react";
import { getApiUrl } from "@/config/api";

function isReloadNavigation(): boolean {
  if (typeof performance === "undefined") {
    return false;
  }
  const entries = performance.getEntriesByType("navigation");
  const navEntry = entries[0] as PerformanceNavigationTiming | undefined;
  if (navEntry) {
    return navEntry.type === "reload";
  }
  const legacy = (performance as Performance & { navigation?: { type?: number } })
    .navigation;
  return legacy?.type === 1;
}

export function ClearCacheOnReload() {
  const hasRun = useRef(false);

  useEffect(() => {
    if (hasRun.current) {
      return;
    }
    hasRun.current = true;

    if (!isReloadNavigation()) {
      return;
    }

    const controller = new AbortController();
    fetch(getApiUrl("/api/cache/clear-all"), {
      method: "DELETE",
      signal: controller.signal,
    }).catch(() => undefined);

    return () => controller.abort();
  }, []);

  return null;
}
