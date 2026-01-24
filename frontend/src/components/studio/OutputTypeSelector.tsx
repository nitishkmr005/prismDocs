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

// Combined output types that generate both formats
export type CombinedOutputType = "article" | "presentation";

interface OutputTypeConfig {
  id: StudioOutputType | CombinedOutputType;
  label: string;
  icon: React.ReactNode;
  description: string;
  color: string;
  bgColor: string;
  hoverBgColor: string;
  comingSoon?: boolean;
  /** Features that require Gemini API key specifically */
  requiresGeminiKey?: boolean;
  /** For combined types, the actual output types they map to */
  outputTypes?: StudioOutputType[];
}

// Icon components for cleaner rendering
const ArticleIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const PresentationIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
  </svg>
);

const MindMapIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
  </svg>
);

const ImageIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const PodcastIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
  </svg>
);

const FAQIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const outputTypes: OutputTypeConfig[] = [
  {
    id: "article",
    label: "Article",
    icon: <ArticleIcon />,
    description: "PDF & Markdown",
    color: "text-rose-600 dark:text-rose-400",
    bgColor: "bg-gradient-to-br from-rose-50 to-orange-50 dark:from-rose-950/40 dark:to-orange-950/30 border-rose-200/80 dark:border-rose-800/50",
    hoverBgColor: "hover:border-rose-300 dark:hover:border-rose-700",
    outputTypes: ["article_pdf", "article_markdown"],
  },
  {
    id: "presentation",
    label: "Presentation",
    icon: <PresentationIcon />,
    description: "PPTX & PDF Slides",
    color: "text-blue-600 dark:text-blue-400",
    bgColor: "bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/40 dark:to-indigo-950/30 border-blue-200/80 dark:border-blue-800/50",
    hoverBgColor: "hover:border-blue-300 dark:hover:border-blue-700",
    outputTypes: ["presentation_pptx", "slide_deck_pdf"],
  },
  {
    id: "mindmap",
    label: "Mind Map",
    icon: <MindMapIcon />,
    description: "Interactive visual map",
    color: "text-violet-600 dark:text-violet-400",
    bgColor: "bg-gradient-to-br from-violet-50 to-purple-50 dark:from-violet-950/40 dark:to-purple-950/30 border-violet-200/80 dark:border-violet-800/50",
    hoverBgColor: "hover:border-violet-300 dark:hover:border-violet-700",
  },
  {
    id: "image_generate",
    label: "Image",
    icon: <ImageIcon />,
    description: "AI-generated visual",
    color: "text-fuchsia-600 dark:text-fuchsia-400",
    bgColor: "bg-gradient-to-br from-fuchsia-50 to-pink-50 dark:from-fuchsia-950/40 dark:to-pink-950/30 border-fuchsia-200/80 dark:border-fuchsia-800/50",
    hoverBgColor: "hover:border-fuchsia-300 dark:hover:border-fuchsia-700",
    requiresGeminiKey: true,
  },
  {
    id: "podcast",
    label: "Podcast",
    icon: <PodcastIcon />,
    description: "Audio with AI voices",
    color: "text-amber-600 dark:text-amber-400",
    bgColor: "bg-gradient-to-br from-amber-50 to-yellow-50 dark:from-amber-950/40 dark:to-yellow-950/30 border-amber-200/80 dark:border-amber-800/50",
    hoverBgColor: "hover:border-amber-300 dark:hover:border-amber-700",
    requiresGeminiKey: true,
  },
  {
    id: "faq",
    label: "FAQ Cards",
    icon: <FAQIcon />,
    description: "Q&A format",
    color: "text-cyan-600 dark:text-cyan-400",
    bgColor: "bg-gradient-to-br from-cyan-50 to-teal-50 dark:from-cyan-950/40 dark:to-teal-950/30 border-cyan-200/80 dark:border-cyan-800/50",
    hoverBgColor: "hover:border-cyan-300 dark:hover:border-cyan-700",
    comingSoon: true,
  },
];

// Legacy output types for backwards compatibility
const legacyOutputTypes: OutputTypeConfig[] = [
  {
    id: "article_pdf",
    label: "Article (PDF)",
    icon: <ArticleIcon />,
    description: "Professional PDF article",
    color: "text-red-600",
    bgColor: "bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800",
    hoverBgColor: "hover:border-red-300 dark:hover:border-red-700",
  },
  {
    id: "article_markdown",
    label: "Article (MD)",
    icon: <ArticleIcon />,
    description: "Markdown document",
    color: "text-violet-600",
    bgColor: "bg-violet-50 dark:bg-violet-950/30 border-violet-200 dark:border-violet-800",
    hoverBgColor: "hover:border-violet-300 dark:hover:border-violet-700",
  },
  {
    id: "slide_deck_pdf",
    label: "Slides (PDF)",
    icon: <PresentationIcon />,
    description: "Slide deck as PDF",
    color: "text-blue-600",
    bgColor: "bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800",
    hoverBgColor: "hover:border-blue-300 dark:hover:border-blue-700",
  },
  {
    id: "presentation_pptx",
    label: "Presentation (PPTX)",
    icon: <PresentationIcon />,
    description: "PowerPoint PPTX",
    color: "text-orange-600",
    bgColor: "bg-orange-50 dark:bg-orange-950/30 border-orange-200 dark:border-orange-800",
    hoverBgColor: "hover:border-orange-300 dark:hover:border-orange-700",
  },
];

interface OutputTypeSelectorProps {
  selectedType: StudioOutputType;
  onTypeChange: (type: StudioOutputType) => void;
  /** Whether Gemini API key is available (required for image and podcast) */
  geminiKeyAvailable?: boolean;
  /** Whether image generation is enabled (user toggle in modal) */
  imageGenerationEnabled?: boolean;
  /** Whether podcast generation is enabled (user toggle in modal) */
  podcastEnabled?: boolean;
  /** @deprecated Use geminiKeyAvailable instead */
  imageGenerationAvailable?: boolean;
  /** Callback for combined type selection (article, presentation) */
  onCombinedTypeChange?: (type: CombinedOutputType) => void;
  /** Currently selected combined type */
  selectedCombinedType?: CombinedOutputType | null;
}

// Helper to check if a type is a combined type
export function isCombinedType(type: string): type is CombinedOutputType {
  return type === "article" || type === "presentation";
}

// Helper to get the primary output type for a combined type
export function getPrimaryOutputType(combinedType: CombinedOutputType): StudioOutputType {
  switch (combinedType) {
    case "article":
      return "article_pdf";
    case "presentation":
      return "presentation_pptx";
  }
}

// Helper to check if a studio output type belongs to a combined type
export function getCombinedTypeForOutput(outputType: StudioOutputType): CombinedOutputType | null {
  if (outputType === "article_pdf" || outputType === "article_markdown") {
    return "article";
  }
  if (outputType === "presentation_pptx" || outputType === "slide_deck_pdf") {
    return "presentation";
  }
  return null;
}

export function OutputTypeSelector({
  selectedType,
  onTypeChange,
  geminiKeyAvailable,
  imageGenerationEnabled = true,
  podcastEnabled = true,
  imageGenerationAvailable = true,
  onCombinedTypeChange,
  selectedCombinedType,
}: OutputTypeSelectorProps) {
  // Use geminiKeyAvailable if provided, otherwise fall back to imageGenerationAvailable for backwards compatibility
  const hasGeminiKey = geminiKeyAvailable ?? imageGenerationAvailable;

  // Determine if specific features are disabled
  const isImageDisabled = !hasGeminiKey || !imageGenerationEnabled;
  const isPodcastDisabled = !hasGeminiKey || !podcastEnabled;

  // Check if current selection matches a type
  const isTypeSelected = (typeId: StudioOutputType | CombinedOutputType) => {
    // For combined types, check if selectedCombinedType matches
    if (isCombinedType(typeId)) {
      return selectedCombinedType === typeId;
    }
    // For regular types, check selectedType and ensure no combined type is active
    return selectedType === typeId && !selectedCombinedType;
  };

  const handleTypeClick = (type: OutputTypeConfig) => {
    if (isCombinedType(type.id)) {
      // For combined types, use the combined callback if available
      if (onCombinedTypeChange) {
        onCombinedTypeChange(type.id);
      }
      // Also set the primary output type
      onTypeChange(getPrimaryOutputType(type.id));
    } else {
      // For regular types, clear combined type and set the type
      if (onCombinedTypeChange) {
        onCombinedTypeChange(null as unknown as CombinedOutputType);
      }
      onTypeChange(type.id as StudioOutputType);
    }
  };

  return (
    <div className="space-y-3 pt-3">
      <div className="grid grid-cols-2 gap-2">
        {outputTypes.map((type) => {
          const isSelected = isTypeSelected(type.id);

          // Determine if this specific type is disabled and why
          let isDisabled = type.comingSoon;
          let disabledReason: "soon" | "gemini_key" | "disabled" | null = type.comingSoon ? "soon" : null;

          if (type.id === "image_generate") {
            if (!hasGeminiKey) {
              isDisabled = true;
              disabledReason = "gemini_key";
            } else if (!imageGenerationEnabled) {
              isDisabled = true;
              disabledReason = "disabled";
            }
          } else if (type.id === "podcast") {
            if (!hasGeminiKey) {
              isDisabled = true;
              disabledReason = "gemini_key";
            } else if (!podcastEnabled) {
              isDisabled = true;
              disabledReason = "disabled";
            }
          }

          return (
            <button
              key={type.id}
              type="button"
              onClick={() => !isDisabled && handleTypeClick(type)}
              disabled={isDisabled}
              className={`group relative flex items-center gap-3 p-3 rounded-xl border transition-all duration-200 ${
                isDisabled
                  ? "opacity-50 cursor-not-allowed bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800"
                  : isSelected
                  ? `${type.bgColor} shadow-sm ring-1 ring-slate-900/5 dark:ring-white/10`
                  : `bg-white dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/50 ${type.hoverBgColor} hover:shadow-sm`
              }`}
            >
              {/* Icon */}
              <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center transition-colors ${
                isSelected
                  ? `${type.color} bg-white/60 dark:bg-slate-900/40`
                  : "text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-700/50 group-hover:text-slate-700 dark:group-hover:text-slate-300"
              }`}>
                {type.icon}
              </div>

              {/* Text */}
              <div className="flex-1 text-left min-w-0">
                <span className={`text-sm font-semibold block truncate ${
                  isSelected ? type.color : "text-slate-900 dark:text-white"
                }`}>
                  {type.label}
                </span>
                <span className="text-[11px] text-slate-500 dark:text-slate-400 block truncate">
                  {type.description}
                </span>
              </div>

              {/* Badges */}
              {type.comingSoon && (
                <span className="absolute -top-1.5 -right-1.5 px-2 py-0.5 text-[10px] font-semibold rounded-full bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                  Soon
                </span>
              )}
              {disabledReason === "gemini_key" && (
                <span className="absolute -top-1.5 -right-1.5 px-2 py-0.5 text-[10px] font-semibold rounded-full bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300">
                  Gemini
                </span>
              )}
              {(type.id === "article" || type.id === "presentation") && isSelected && (
                <span className="absolute -top-1.5 -right-1.5 px-2 py-0.5 text-[10px] font-semibold rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-sm">
                  Dual
                </span>
              )}

              {/* Selection indicator */}
              {isSelected && (
                <div className="absolute top-2 right-2">
                  <svg className={`w-4 h-4 ${type.color}`} fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export { outputTypes, legacyOutputTypes };

