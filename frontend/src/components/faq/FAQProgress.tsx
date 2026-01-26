// frontend/src/components/faq/FAQProgress.tsx

"use client";

interface FAQProgressProps {
  current: number;
  total: number;
}

export function FAQProgress({ current, total }: FAQProgressProps) {
  const safeTotal = Math.max(1, total);
  const displayIndex = Math.min(current + 1, safeTotal);

  return (
    <div className="text-xs font-semibold text-slate-600 dark:text-slate-300">
      {displayIndex}/{safeTotal}
    </div>
  );
}
