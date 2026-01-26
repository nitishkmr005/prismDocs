// frontend/src/components/faq/FAQNavigation.tsx

"use client";

import { Button } from "@/components/ui/button";

interface FAQNavigationProps {
  onPrev: () => void;
  onNext: () => void;
  disablePrev?: boolean;
  disableNext?: boolean;
}

export function FAQNavigation({
  onPrev,
  onNext,
  disablePrev = false,
  disableNext = false,
}: FAQNavigationProps) {
  return (
    <div className="flex items-center gap-2">
      <Button
        variant="ghost"
        size="sm"
        onClick={onPrev}
        disabled={disablePrev}
        className="h-8 w-8 p-0"
        aria-label="Previous FAQ"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={onNext}
        disabled={disableNext}
        className="h-8 w-8 p-0"
        aria-label="Next FAQ"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </Button>
    </div>
  );
}
