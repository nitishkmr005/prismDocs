// frontend/src/components/faq/hooks/useFAQNavigation.ts

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface UseFAQNavigationOptions {
  totalItems: number;
  loop?: boolean;
  initialIndex?: number;
}

interface UseFAQNavigationReturn {
  currentIndex: number;
  direction: "next" | "prev" | "none";
  goNext: () => void;
  goPrev: () => void;
  setIndex: (index: number) => void;
  onTouchStart: (event: React.TouchEvent) => void;
  onTouchMove: (event: React.TouchEvent) => void;
  onTouchEnd: () => void;
}

export function useFAQNavigation({
  totalItems,
  loop = true,
  initialIndex = 0,
}: UseFAQNavigationOptions): UseFAQNavigationReturn {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [direction, setDirection] = useState<"next" | "prev" | "none">("none");
  const touchStartX = useRef<number | null>(null);
  const touchDeltaX = useRef(0);

  const clampIndex = useCallback(
    (index: number) => {
      if (totalItems <= 0) return 0;
      if (loop) {
        return (index + totalItems) % totalItems;
      }
      return Math.max(0, Math.min(totalItems - 1, index));
    },
    [loop, totalItems]
  );

  const goNext = useCallback(() => {
    setDirection("next");
    setCurrentIndex((prev) => clampIndex(prev + 1));
  }, [clampIndex]);

  const goPrev = useCallback(() => {
    setDirection("prev");
    setCurrentIndex((prev) => clampIndex(prev - 1));
  }, [clampIndex]);

  const setIndex = useCallback(
    (index: number) => {
      setDirection(index > currentIndex ? "next" : "prev");
      setCurrentIndex(clampIndex(index));
    },
    [clampIndex, currentIndex]
  );

  useEffect(() => {
    setCurrentIndex((prev) => clampIndex(prev));
  }, [clampIndex]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.isContentEditable) return;
      if (target?.tagName === "INPUT" || target?.tagName === "TEXTAREA") return;

      if (event.key === "ArrowRight") {
        goNext();
      } else if (event.key === "ArrowLeft") {
        goPrev();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [goNext, goPrev]);

  const onTouchStart = useCallback((event: React.TouchEvent) => {
    touchStartX.current = event.touches[0]?.clientX ?? null;
    touchDeltaX.current = 0;
  }, []);

  const onTouchMove = useCallback((event: React.TouchEvent) => {
    if (touchStartX.current === null) return;
    touchDeltaX.current = (event.touches[0]?.clientX ?? 0) - touchStartX.current;
  }, []);

  const onTouchEnd = useCallback(() => {
    const threshold = 50;
    if (touchDeltaX.current > threshold) {
      goPrev();
    } else if (touchDeltaX.current < -threshold) {
      goNext();
    }
    touchStartX.current = null;
    touchDeltaX.current = 0;
  }, [goNext, goPrev]);

  return {
    currentIndex,
    direction,
    goNext,
    goPrev,
    setIndex,
    onTouchStart,
    onTouchMove,
    onTouchEnd,
  };
}
