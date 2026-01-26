// frontend/src/components/faq/FAQCard.tsx

"use client";

import { FAQItem, TAG_GRADIENTS } from "@/lib/types/faq";

interface FAQCardProps {
  item: FAQItem;
  tagColors: Record<string, string>;
  direction?: "next" | "prev" | "none";
}

const fallbackGradient = TAG_GRADIENTS["blue-cyan"];

function renderMarkdown(text: string): string {
  const escapeHtml = (value: string) =>
    value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  return escapeHtml(text)
    .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, '<code class="bg-muted px-1.5 py-0.5 rounded text-xs">$1</code>')
    .replace(/\n/g, "<br/>");
}

export function FAQCard({ item, tagColors, direction = "none" }: FAQCardProps) {
  const primaryTag = item.tags[0];
  const gradientKey = primaryTag ? tagColors[primaryTag] : undefined;
  const gradient = TAG_GRADIENTS[gradientKey || ""] || fallbackGradient;

  const animationClass =
    direction === "next"
      ? "animate-in slide-in-from-right-4"
      : direction === "prev"
      ? "animate-in slide-in-from-left-4"
      : "animate-in fade-in";

  return (
    <div className={`relative rounded-2xl p-[1.5px] bg-gradient-to-br ${gradient} ${animationClass} duration-200`}>
      <div className="rounded-[calc(1rem-1.5px)] bg-white/90 dark:bg-slate-900/90 p-6 shadow-sm">
        <div className="space-y-4">
          <h3 className="text-lg sm:text-xl font-semibold text-slate-900 dark:text-white">
            {item.question}
          </h3>
          <div
            className="text-sm leading-relaxed text-slate-600 dark:text-slate-300"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(item.answer) }}
          />
        </div>

        {item.tags.length > 0 && (
          <div className="mt-5 flex flex-wrap gap-2">
            {item.tags.map((tag) => {
              const tagGradientKey = tagColors[tag];
              const tagGradient = TAG_GRADIENTS[tagGradientKey || ""] || fallbackGradient;
              return (
                <span
                  key={tag}
                  className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-semibold text-white shadow-sm bg-gradient-to-r ${tagGradient}`}
                >
                  {tag}
                </span>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
