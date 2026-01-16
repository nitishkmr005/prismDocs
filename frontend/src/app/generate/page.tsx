"use client";

import { useCallback, useState } from "react";
import { GenerateForm } from "@/components/forms/GenerateForm";
import { GenerationProgress } from "@/components/progress/GenerationProgress";
import { useGeneration, GenerationState } from "@/hooks/useGeneration";
import {
  OutputFormat,
  Provider,
  Audience,
  ImageStyle,
  SourceItem,
} from "@/lib/types/requests";

// Feature type definition
type FeatureType =
  | "blog"
  | "slides"
  | "image"
  | "image-edit"
  | "resume"
  | "podcast"
  | "mindmap"
  | "faq"
  | "research";

interface OutputOption {
  value: OutputFormat;
  label: string;
}

interface Feature {
  id: FeatureType;
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
  shadowColor: string;
  defaultOutputFormat: OutputFormat;
  outputOptions: OutputOption[];
  comingSoon?: boolean;
}

const features: Feature[] = [
  {
    id: "blog",
    title: "Blog Generation",
    description: "Transform content into engaging blog posts",
    icon: (
      <svg
        className="w-7 h-7"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
        />
      </svg>
    ),
    color: "text-cyan-600",
    bgColor:
      "bg-gradient-to-br from-cyan-100 to-cyan-50 dark:from-cyan-900/40 dark:to-cyan-950/40",
    shadowColor: "hover:shadow-cyan-500/20",
    defaultOutputFormat: "pdf",
    outputOptions: [
      { value: "pdf", label: "PDF Document" },
      { value: "markdown", label: "Markdown" },
    ],
  },
  {
    id: "slides",
    title: "Slide Generation",
    description: "Create professional presentations",
    icon: (
      <svg
        className="w-7 h-7"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
        />
      </svg>
    ),
    color: "text-violet-600",
    bgColor:
      "bg-gradient-to-br from-violet-100 to-violet-50 dark:from-violet-900/40 dark:to-violet-950/40",
    shadowColor: "hover:shadow-violet-500/20",
    defaultOutputFormat: "pptx",
    outputOptions: [
      { value: "pptx", label: "PowerPoint Presentation" },
      { value: "pdf_from_pptx", label: "PDF (from slides)" },
    ],
  },
  {
    id: "image",
    title: "Image Generation",
    description: "Generate AI images from descriptions",
    icon: (
      <svg
        className="w-7 h-7"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
        />
      </svg>
    ),
    color: "text-fuchsia-600",
    bgColor:
      "bg-gradient-to-br from-fuchsia-100 to-fuchsia-50 dark:from-fuchsia-900/40 dark:to-fuchsia-950/40",
    shadowColor: "hover:shadow-fuchsia-500/20",
    defaultOutputFormat: "pdf",
    outputOptions: [{ value: "pdf", label: "PDF Document" }],
    comingSoon: true,
  },
  {
    id: "image-edit",
    title: "Image Editing",
    description: "Edit and enhance existing images",
    icon: (
      <svg
        className="w-7 h-7"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
        />
      </svg>
    ),
    color: "text-rose-600",
    bgColor:
      "bg-gradient-to-br from-rose-100 to-rose-50 dark:from-rose-900/40 dark:to-rose-950/40",
    shadowColor: "hover:shadow-rose-500/20",
    defaultOutputFormat: "pdf",
    outputOptions: [{ value: "pdf", label: "PDF Document" }],
    comingSoon: true,
  },
  {
    id: "resume",
    title: "Resume Creation",
    description: "Build professional resumes",
    icon: (
      <svg
        className="w-7 h-7"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
    ),
    color: "text-teal-600",
    bgColor:
      "bg-gradient-to-br from-teal-100 to-teal-50 dark:from-teal-900/40 dark:to-teal-950/40",
    shadowColor: "hover:shadow-teal-500/20",
    defaultOutputFormat: "pdf",
    outputOptions: [{ value: "pdf", label: "PDF Document" }],
    comingSoon: true,
  },
  {
    id: "podcast",
    title: "Podcast Generation",
    description: "Generate podcast scripts and audio files with TTS",
    icon: (
      <svg
        className="w-7 h-7"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
        />
      </svg>
    ),
    color: "text-orange-600",
    bgColor:
      "bg-gradient-to-br from-orange-100 to-orange-50 dark:from-orange-900/40 dark:to-orange-950/40",
    shadowColor: "hover:shadow-orange-500/20",
    defaultOutputFormat: "pdf",
    outputOptions: [{ value: "pdf", label: "PDF Document" }],
    comingSoon: true,
  },
  {
    id: "mindmap",
    title: "Mind Map",
    description: "Visualize ideas as mind maps",
    icon: (
      <svg
        className="w-7 h-7"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
        />
      </svg>
    ),
    color: "text-purple-600",
    bgColor:
      "bg-gradient-to-br from-purple-100 to-purple-50 dark:from-purple-900/40 dark:to-purple-950/40",
    shadowColor: "hover:shadow-purple-500/20",
    defaultOutputFormat: "pdf",
    outputOptions: [{ value: "pdf", label: "PDF Document" }],
    comingSoon: true,
  },
  {
    id: "faq",
    title: "FAQ Cards",
    description: "Create Q&A cards from content",
    icon: (
      <svg
        className="w-7 h-7"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
    color: "text-blue-600",
    bgColor:
      "bg-gradient-to-br from-blue-100 to-blue-50 dark:from-blue-900/40 dark:to-blue-950/40",
    shadowColor: "hover:shadow-blue-500/20",
    defaultOutputFormat: "pdf",
    outputOptions: [{ value: "pdf", label: "PDF Document" }],
    comingSoon: true,
  },
  {
    id: "research",
    title: "Research Assistant",
    description: "Summarize and analyze research",
    icon: (
      <svg
        className="w-7 h-7"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
        />
      </svg>
    ),
    color: "text-emerald-600",
    bgColor:
      "bg-gradient-to-br from-emerald-100 to-emerald-50 dark:from-emerald-900/40 dark:to-emerald-950/40",
    shadowColor: "hover:shadow-emerald-500/20",
    defaultOutputFormat: "pdf",
    outputOptions: [{ value: "pdf", label: "PDF Document" }],
    comingSoon: true,
  },
];

function FeatureTile({
  feature,
  onClick,
}: {
  feature: Feature;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={feature.comingSoon}
      className={`group relative flex flex-col items-center text-center p-6 rounded-xl border bg-card transition-all duration-300 hover:shadow-lg ${feature.shadowColor} hover:-translate-y-1 disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:shadow-none`}
    >
      {feature.comingSoon && (
        <span className="absolute top-3 right-3 px-2 py-0.5 text-xs font-medium rounded-full bg-muted text-muted-foreground">
          Coming Soon
        </span>
      )}
      <div
        className={`h-14 w-14 rounded-xl ${feature.bgColor} flex items-center justify-center mb-4`}
      >
        <span className={feature.color}>{feature.icon}</span>
      </div>
      <h3 className="text-base font-semibold mb-2">{feature.title}</h3>
      <p className="text-muted-foreground text-sm leading-relaxed">
        {feature.description}
      </p>
    </button>
  );
}

function ProgressPanel({
  state,
  progress,
  status,
  downloadUrl,
  error,
  metadata,
  onReset,
  onNewGeneration,
  featureColor,
}: {
  state: GenerationState;
  progress: number;
  status: string;
  downloadUrl: string | null;
  error: string | null;
  metadata: {
    title?: string;
    pages?: number;
    slides?: number;
    imagesGenerated?: number;
  } | null;
  onReset: () => void;
  onNewGeneration: () => void;
  featureColor: string;
}) {
  if (state === "idle") {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center p-8 rounded-xl border border-dashed border-border bg-muted/20">
        <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center mb-4">
          <svg
            className="w-8 h-8 text-muted-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-muted-foreground mb-2">
          Ready to Generate
        </h3>
        <p className="text-sm text-muted-foreground/70 max-w-xs">
          Fill in the form and click "Generate Document" to create your content
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-[400px] max-h-[calc(100vh-200px)] overflow-hidden rounded-xl border bg-card">
      <div className="flex-1 overflow-auto p-6">
        <GenerationProgress
          state={state}
          progress={progress}
          status={status}
          downloadUrl={downloadUrl}
          error={error}
          metadata={metadata}
          onReset={onReset}
        />
      </div>
    </div>
  );
}

export default function GeneratePage() {
  const [selectedFeature, setSelectedFeature] = useState<Feature | null>(null);
  const {
    state,
    progress,
    status,
    downloadUrl,
    error,
    metadata,
    generate,
    reset,
  } = useGeneration();

  const handleFeatureSelect = useCallback(
    (feature: Feature) => {
      if (!feature.comingSoon) {
        setSelectedFeature(feature);
        reset(); // Reset any previous generation state
      }
    },
    [reset]
  );

  const handleBackToFeatures = useCallback(() => {
    setSelectedFeature(null);
    reset();
  }, [reset]);

  const handleSubmit = useCallback(
    (
      sources: SourceItem[],
      options: {
        outputFormat: OutputFormat;
        provider: Provider;
        audience: Audience;
        imageStyle: ImageStyle;
        enableImageGeneration: boolean;
      },
      contentApiKey: string,
      imageApiKey?: string
    ) => {
      generate(
        {
          output_format: options.outputFormat,
          sources,
          provider: options.provider,
          preferences: {
            audience: options.audience,
            image_style: options.imageStyle,
            temperature: 0.4,
            max_tokens: 8000,
            max_slides: 10,
            max_summary_points: 5,
            enable_image_generation: options.enableImageGeneration,
          },
        },
        contentApiKey,
        imageApiKey
      );
    },
    [generate]
  );

  const handleNewGeneration = useCallback(() => {
    reset();
  }, [reset]);

  const isGenerating = state === "generating";

  // Show form when a feature is selected (split layout)
  if (selectedFeature) {
    return (
      <div className="container mx-auto px-4 py-6 md:py-10">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-center gap-4 mb-6">
            <button
              onClick={handleBackToFeatures}
              className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
              Back
            </button>
            <div className="flex items-center gap-3">
              <div
                className={`h-10 w-10 rounded-lg ${selectedFeature.bgColor} flex items-center justify-center`}
              >
                <span
                  className={`${selectedFeature.color} [&>svg]:w-5 [&>svg]:h-5`}
                >
                  {selectedFeature.icon}
                </span>
              </div>
              <div>
                <h1 className="text-xl font-bold">{selectedFeature.title}</h1>
                <p className="text-sm text-muted-foreground">
                  {selectedFeature.description}
                </p>
              </div>
            </div>
          </div>

          {/* Split Layout */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Left: Form */}
            <div className="order-2 lg:order-1">
              <GenerateForm
                onSubmit={handleSubmit}
                isGenerating={isGenerating}
                defaultOutputFormat={selectedFeature.defaultOutputFormat}
                outputOptions={selectedFeature.outputOptions}
              />
            </div>

            {/* Right: Progress Panel */}
            <div className="order-1 lg:order-2 lg:sticky lg:top-24 lg:self-start">
              <ProgressPanel
                state={state}
                progress={progress}
                status={status}
                downloadUrl={downloadUrl}
                error={error}
                metadata={metadata}
                onReset={reset}
                onNewGeneration={handleNewGeneration}
                featureColor={selectedFeature.color}
              />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show feature tiles
  return (
    <div className="container mx-auto px-4 py-8 md:py-12">
      <div className="mx-auto max-w-5xl space-y-8">
        <div className="text-center space-y-3">
          <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
            What would you like to create?
          </h1>
          <p className="text-muted-foreground text-lg">
            Choose a format and we'll guide you through the process
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <FeatureTile
              key={feature.id}
              feature={feature}
              onClick={() => handleFeatureSelect(feature)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
