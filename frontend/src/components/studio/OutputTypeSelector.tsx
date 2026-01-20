"use client";

import { Label } from "@/components/ui/label";

export type StudioOutputType =
  | "article_pdf"
  | "article_markdown"
  | "slide_deck_pdf"
  | "presentation_pptx"
  | "mindmap"
  | "image_generate"
  | "podcast"
  | "faq";

interface OutputTypeConfig {
  id: StudioOutputType;
  label: string;
  icon: string;
  description: string;
  color: string;
  bgColor: string;
  comingSoon?: boolean;
}

const outputTypes: OutputTypeConfig[] = [
  {
    id: "article_pdf",
    label: "Article (PDF)",
    icon: "📄",
    description: "Professional PDF article",
    color: "text-red-600",
    bgColor: "bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800",
  },
  {
    id: "article_markdown",
    label: "Article (MD)",
    icon: "📝",
    description: "Markdown document",
    color: "text-violet-600",
    bgColor: "bg-violet-50 dark:bg-violet-950/30 border-violet-200 dark:border-violet-800",
  },
  {
    id: "slide_deck_pdf",
    label: "Slides (PDF)",
    icon: "📑",
    description: "Slide deck as PDF",
    color: "text-blue-600",
    bgColor: "bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800",
  },
  {
    id: "presentation_pptx",
    label: "Presentation",
    icon: "📊",
    description: "PowerPoint PPTX",
    color: "text-orange-600",
    bgColor: "bg-orange-50 dark:bg-orange-950/30 border-orange-200 dark:border-orange-800",
  },
  {
    id: "mindmap",
    label: "Mind Map",
    icon: "🧠",
    description: "Visual mind map",
    color: "text-purple-600",
    bgColor: "bg-purple-50 dark:bg-purple-950/30 border-purple-200 dark:border-purple-800",
  },
  {
    id: "image_generate",
    label: "Image",
    icon: "🎨",
    description: "AI-generated image",
    color: "text-fuchsia-600",
    bgColor: "bg-fuchsia-50 dark:bg-fuchsia-950/30 border-fuchsia-200 dark:border-fuchsia-800",
  },
  {
    id: "podcast",
    label: "Podcast",
    icon: "🎙️",
    description: "Audio content",
    color: "text-amber-600",
    bgColor: "bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800",
    comingSoon: true,
  },
  {
    id: "faq",
    label: "FAQ Cards",
    icon: "❓",
    description: "Q&A cards",
    color: "text-cyan-600",
    bgColor: "bg-cyan-50 dark:bg-cyan-950/30 border-cyan-200 dark:border-cyan-800",
    comingSoon: true,
  },
];

interface OutputTypeSelectorProps {
  selectedType: StudioOutputType;
  onTypeChange: (type: StudioOutputType) => void;
}

export function OutputTypeSelector({ selectedType, onTypeChange }: OutputTypeSelectorProps) {
  return (
    <div className="space-y-3">
      <Label className="text-sm font-semibold">Output Type</Label>
      <div className="grid grid-cols-3 gap-2">
        {outputTypes.map((type) => {
          const isSelected = selectedType === type.id;
          return (
            <button
              key={type.id}
              type="button"
              onClick={() => !type.comingSoon && onTypeChange(type.id)}
              disabled={type.comingSoon}
              className={`relative flex flex-col items-center text-center p-3 rounded-xl border-2 transition-all duration-200 ${
                type.comingSoon
                  ? "opacity-50 cursor-not-allowed bg-muted/30 border-border"
                  : isSelected
                  ? `${type.bgColor} ring-2 ring-offset-1 ring-primary/30`
                  : "bg-card border-border hover:border-muted-foreground/30 hover:bg-muted/20"
              }`}
            >
              {type.comingSoon && (
                <span className="absolute -top-1.5 -right-1.5 px-1.5 py-0.5 text-[9px] font-bold rounded-full bg-muted text-muted-foreground">
                  Soon
                </span>
              )}
              {type.id === "presentation_pptx" && !type.comingSoon && (
                <span className="absolute -top-1.5 -right-1.5 px-1.5 py-0.5 text-[9px] font-bold rounded-full bg-gradient-to-r from-orange-500 to-amber-500 text-white">
                  Best
                </span>
              )}
              <span className="text-xl mb-1">{type.icon}</span>
              <span className={`text-[10px] font-semibold leading-tight ${isSelected ? type.color : "text-foreground"}`}>
                {type.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export { outputTypes };
