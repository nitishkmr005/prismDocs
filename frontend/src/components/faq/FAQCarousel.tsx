// frontend/src/components/faq/FAQCarousel.tsx

"use client";

import { Button } from "@/components/ui/button";
import { FAQDocument } from "@/lib/types/faq";
import { FAQCard } from "./FAQCard";
import { FAQProgress } from "./FAQProgress";
import { FAQNavigation } from "./FAQNavigation";
import { FAQExportMenu } from "./FAQExportMenu";
import { useFAQNavigation } from "./hooks/useFAQNavigation";

interface FAQCarouselProps {
  faqDocument: FAQDocument;
  downloadUrl?: string | null;
  onReset?: () => void;
}

export function FAQCarousel({ faqDocument, downloadUrl, onReset }: FAQCarouselProps) {
  const items = faqDocument.items || [];
  const {
    currentIndex,
    direction,
    goNext,
    goPrev,
    onTouchStart,
    onTouchMove,
    onTouchEnd,
  } = useFAQNavigation({ totalItems: items.length });

  if (!items.length) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[360px] text-center rounded-xl border border-border bg-muted/20 p-8">
        <p className="text-sm text-muted-foreground">No FAQ items generated.</p>
        {onReset && (
          <Button variant="ghost" size="sm" className="mt-3" onClick={onReset}>
            Generate Another
          </Button>
        )}
      </div>
    );
  }

  const currentItem = items[currentIndex];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between gap-3 px-4 py-3 border-b bg-muted/20">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold truncate">{faqDocument.title}</h3>
          {faqDocument.description && (
            <p className="text-xs text-muted-foreground truncate">{faqDocument.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <FAQExportMenu faqDocument={faqDocument} downloadUrl={downloadUrl} />
          {onReset && (
            <Button variant="ghost" size="sm" onClick={onReset} className="h-8 text-xs">
              New
            </Button>
          )}
        </div>
      </div>

      <div
        className="flex-1 flex items-center justify-center p-6"
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
      >
        <div className="w-full max-w-xl">
          <FAQCard
            key={currentItem.id || currentIndex}
            item={currentItem}
            tagColors={faqDocument.metadata.tag_colors}
            direction={direction}
          />
        </div>
      </div>

      <div className="flex items-center justify-between px-4 pb-4">
        <FAQNavigation
          onPrev={goPrev}
          onNext={goNext}
          disablePrev={items.length <= 1}
          disableNext={items.length <= 1}
        />
        <FAQProgress current={currentIndex} total={items.length} />
      </div>
    </div>
  );
}
