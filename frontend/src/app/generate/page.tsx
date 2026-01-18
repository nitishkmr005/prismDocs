"use client";

import { useCallback, useState } from "react";
import { GenerateForm } from "@/components/forms/GenerateForm";
import { ImageStudioForm } from "@/components/forms/ImageStudioForm";
import { GenerationProgress } from "@/components/progress/GenerationProgress";
import { MindMapForm, MindMapViewer, MindMapProgress } from "@/components/mindmap";
import { IdeaCanvasForm, IdeaCanvas, QuestionCard } from "@/components/idea-canvas";
import { useGeneration, GenerationState } from "@/hooks/useGeneration";
import { useMindMapGeneration } from "@/hooks/useMindMapGeneration";
import { useIdeaCanvas } from "@/hooks/useIdeaCanvas";
import { useAuth } from "@/hooks/useAuth";
import { AuthModal } from "@/components/auth/AuthModal";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  OutputFormat,
  Provider,
  Audience,
  ImageStyle,
  SourceItem,
} from "@/lib/types/requests";
import { MindMapMode } from "@/lib/types/mindmap";
import { StartCanvasRequest } from "@/lib/types/idea-canvas";
import { generateCanvasReport } from "@/lib/api/idea-canvas";
import { generateImage, downloadImage } from "@/lib/api/image";

// Feature type definition
type FeatureType =
  | "content"
  | "image-studio"
  | "resume"
  | "podcast"
  | "mindmap"
  | "idea-canvas"
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
    id: "content",
    title: "Content Generation",
    description: "Create articles, reports & presentations from any source",
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
          d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
        />
      </svg>
    ),
    color: "text-indigo-600",
    bgColor:
      "bg-gradient-to-br from-cyan-100 via-indigo-100 to-violet-100 dark:from-cyan-900/40 dark:via-indigo-900/40 dark:to-violet-900/40",
    shadowColor: "hover:shadow-indigo-500/20",
    defaultOutputFormat: "pdf",
    outputOptions: [
      { value: "pptx", label: "📊 Presentation (PPTX)" },
      { value: "pdf_from_pptx", label: "📑 Slide Deck (PDF)" },
      { value: "pdf", label: "📄 Article (PDF)" },
      { value: "markdown", label: "📝 Article (Markdown)" },
    ],
  },
  {
    id: "image-studio",
    title: "Image Studio",
    description: "Create & refine AI images",
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
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M5 3v4M3 5h4"
        />
      </svg>
    ),
    color: "text-fuchsia-600",
    bgColor:
      "bg-gradient-to-br from-fuchsia-100 via-rose-100 to-fuchsia-50 dark:from-fuchsia-900/40 dark:via-rose-900/40 dark:to-fuchsia-950/40",
    shadowColor: "hover:shadow-fuchsia-500/20",
    defaultOutputFormat: "pdf",
    outputOptions: [{ value: "pdf", label: "PDF Document" }],
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
  },
  {
    id: "idea-canvas",
    title: "Idea Canvas",
    description: "Explore ideas through guided Q&A and get implementation specs",
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
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
        />
      </svg>
    ),
    color: "text-amber-600",
    bgColor:
      "bg-gradient-to-br from-amber-100 via-orange-100 to-amber-50 dark:from-amber-900/40 dark:via-orange-900/40 dark:to-amber-950/40",
    shadowColor: "hover:shadow-amber-500/20",
    defaultOutputFormat: "pdf",
    outputOptions: [{ value: "pdf", label: "PDF Document" }],
  },
  // --- Coming Soon Features ---
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
    description: "Summarize research & talk with AI Voice Agent",
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
      {/* Voice Agent badge for Research Assistant */}
      {feature.id === "research" && (
        <span className="absolute top-3 left-3 px-2 py-0.5 text-xs font-medium rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 text-white flex items-center gap-1">
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1 1.93c-3.94-.49-7-3.85-7-7.93V7h2v1c0 2.76 2.24 5 5 5s5-2.24 5-5V7h2v1c0 4.08-3.06 7.44-7 7.93V18h3v2H9v-2h3v-2.07z"/>
          </svg>
          Voice AI
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
  userId,
  outputFormat,
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
  userId?: string;
  outputFormat?: string;
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
          userId={userId}
          outputFormat={outputFormat}
        />
      </div>
    </div>
  );
}

export default function GeneratePage() {
  const [selectedFeature, setSelectedFeature] = useState<Feature | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
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

  // Mind map generation hook
  const {
    state: mindMapState,
    tree: mindMapTree,
    progress: mindMapProgress,
    error: mindMapError,
    generate: generateMindMap,
    reset: resetMindMap,
  } = useMindMapGeneration();

  // Idea canvas hook
  const {
    state: canvasState,
    sessionId: canvasSessionId,
    canvas,
    currentQuestion,
    questionHistory,
    progressMessage: canvasProgressMessage,
    error: canvasError,
    provider: canvasProvider,
    apiKey: canvasApiKey,
    canGoBack,
    start: startCanvas,
    answer: submitCanvasAnswer,
    goBack: goBackCanvas,
    reset: resetCanvas,
  } = useIdeaCanvas();

  // Report generation state
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [reportData, setReportData] = useState<{
    title: string;
    markdown_content: string;
    pdf_base64?: string;
  } | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);
  const [showReportModal, setShowReportModal] = useState(false);
  const [exitedToSummary, setExitedToSummary] = useState(false);
  const [markdownCopied, setMarkdownCopied] = useState(false);
  
  // Image generation from report state
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [generatedImage, setGeneratedImage] = useState<{data: string; format: string} | null>(null);
  const [imageGenError, setImageGenError] = useState<string | null>(null);

  // Handler to exit to summary view (instead of resetting)
  const handleExitToSummary = useCallback(() => {
    setExitedToSummary(true);
  }, []);

  const handleFeatureSelect = useCallback(
    (feature: Feature) => {
      if (!feature.comingSoon) {
        if (!isAuthenticated) {
          setShowAuthModal(true);
          return;
        }
        setSelectedFeature(feature);
        reset(); // Reset any previous generation state
        resetMindMap(); // Reset mind map state
        resetCanvas(); // Reset canvas state
        setReportData(null);
        setReportError(null);
        setExitedToSummary(false);
      }
    },
    [reset, resetMindMap, resetCanvas, isAuthenticated]
  );

  const handleBackToFeatures = useCallback(() => {
    setSelectedFeature(null);
    reset();
    resetMindMap();
    resetCanvas();
    setReportData(null);
    setReportError(null);
    setExitedToSummary(false);
  }, [reset, resetMindMap, resetCanvas]);

  const handleSubmit = useCallback(
    (
      sources: SourceItem[],
      options: {
        outputFormat: OutputFormat;
        provider: Provider;
        contentModel: string;
        imageModel: string;
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
          model: options.contentModel,
          image_model: options.imageModel,
          preferences: {
            audience: options.audience,
            image_style: options.imageStyle,
            temperature: 0.4,
            max_tokens: 12000,
            max_slides: 10,
            max_summary_points: 5,
            enable_image_generation: options.enableImageGeneration,
          },
        },
        contentApiKey,
        imageApiKey,
        user?.id // Pass user ID for tracking
      );
    },
    [generate]
  );

  const handleNewGeneration = useCallback(() => {
    reset();
  }, [reset]);

  // Mind map submit handler
  const handleMindMapSubmit = useCallback(
    (
      sources: SourceItem[],
      options: {
        mode: MindMapMode;
        provider: Provider;
        model: string;
        maxDepth: number;
      },
      apiKey: string
    ) => {
      generateMindMap(
        {
          sources,
          mode: options.mode,
          provider: options.provider,
          model: options.model,
          max_depth: options.maxDepth,
        },
        apiKey,
        user?.id
      );
    },
    [generateMindMap, user?.id]
  );

  // Idea canvas submit handler
  const handleCanvasSubmit = useCallback(
    (request: StartCanvasRequest, apiKey: string) => {
      startCanvas(request, apiKey, user?.id);
    },
    [startCanvas, user?.id]
  );

  // Idea canvas answer handler
  const handleCanvasAnswer = useCallback(
    (answer: string | string[]) => {
      submitCanvasAnswer(answer, user?.id);
    },
    [submitCanvasAnswer, user?.id]
  );

  const generateImageFromReportContent = useCallback(async (reportTitle: string, reportMarkdown: string) => {
    if (!canvasApiKey) {
      setImageGenError("No API key available");
      return;
    }

    setIsGeneratingImage(true);
    setImageGenError(null);
    setGeneratedImage(null);

    try {
      const summaryPrompt = `Create a beautiful hand-drawn style infographic that visually summarizes this implementation plan:

Title: ${reportTitle}

Key points to visualize:
${reportMarkdown.slice(0, 1500)}

Style: Hand-drawn, sketch-like, warm colors, clean whiteboard aesthetic with icons and arrows connecting concepts. Include the main title at the top.`;

      const result = await generateImage({
        prompt: summaryPrompt,
        style_category: "handwritten_and_human",
        style: "whiteboard_handwritten",
        output_format: "raster",
        free_text_mode: false,
      }, canvasApiKey);

      if (result.success && result.image_data) {
        setGeneratedImage({
          data: result.image_data,
          format: result.format,
        });
      } else {
        setImageGenError(result.error || "Failed to generate image");
      }
    } catch (err) {
      setImageGenError(err instanceof Error ? err.message : "Image generation failed");
    } finally {
      setIsGeneratingImage(false);
    }
  }, [canvasApiKey]);

  // Generate report handler
  const handleGenerateReport = useCallback(async () => {
    if (!canvasSessionId || !canvasApiKey) {
      setReportError("No active canvas session");
      return;
    }

    setIsGeneratingReport(true);
    setReportError(null);
    setImageGenError(null);
    setMarkdownCopied(false);

    try {
      const result = await generateCanvasReport({
        sessionId: canvasSessionId,
        outputFormat: "both",
        provider: canvasProvider,
        apiKey: canvasApiKey,
      });

      setReportData({
        title: result.title,
        markdown_content: result.markdown_content || "",
        pdf_base64: result.pdf_base64,
      });
      setShowReportModal(true);
      void generateImageFromReportContent(result.title, result.markdown_content || "");
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "Failed to generate report");
    } finally {
      setIsGeneratingReport(false);
    }
  }, [canvasSessionId, canvasApiKey, canvasProvider, generateImageFromReportContent]);

  // Download report as markdown
  const handleDownloadMarkdown = useCallback(() => {
    if (!reportData) return;
    
    const blob = new Blob([reportData.markdown_content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${reportData.title.replace(/[^a-z0-9]/gi, "_").toLowerCase()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [reportData]);

  const createPdfBlob = useCallback((pdfBase64: string) => {
    const byteCharacters = atob(pdfBase64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: "application/pdf" });
  }, []);

  // Download report as PDF
  const handleDownloadPdf = useCallback(() => {
    if (!reportData?.pdf_base64) return;
    
    const blob = createPdfBlob(reportData.pdf_base64);
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${reportData.title.replace(/[^a-z0-9]/gi, "_").toLowerCase()}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [reportData, createPdfBlob]);

  const handleOpenPdfPreview = useCallback(() => {
    if (!reportData?.pdf_base64) return;

    const blob = createPdfBlob(reportData.pdf_base64);
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener,noreferrer");
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }, [reportData, createPdfBlob]);

  const handleCopyMarkdown = useCallback(async () => {
    if (!reportData?.markdown_content) return;

    try {
      await navigator.clipboard.writeText(reportData.markdown_content);
      setMarkdownCopied(true);
      setTimeout(() => setMarkdownCopied(false), 1500);
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = reportData.markdown_content;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setMarkdownCopied(true);
      setTimeout(() => setMarkdownCopied(false), 1500);
    }
  }, [reportData]);

  const isGenerating = state === "generating";
  const isMindMapGenerating = mindMapState === "generating";
  const isCanvasStarting = canvasState === "starting";
  const isCanvasAnswering = canvasState === "answering";

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

          {/* Feature-specific content */}
          {selectedFeature.id === "image-studio" ? (
            <ImageStudioForm />
          ) : selectedFeature.id === "mindmap" ? (
            /* Mind Map Layout */
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Left: Form or Progress */}
              <div className="order-2 lg:order-1">
                {mindMapState === "generating" ? (
                  <div className="flex items-center justify-center min-h-[400px]">
                    <MindMapProgress
                      stage={mindMapProgress.stage}
                      progress={mindMapProgress.percent}
                      message={mindMapProgress.message}
                    />
                  </div>
                ) : mindMapState === "error" ? (
                  <div className="flex flex-col items-center justify-center min-h-[400px] p-8 rounded-xl border border-red-200 bg-red-50 dark:bg-red-950/20 dark:border-red-800">
                    <svg className="w-12 h-12 text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <h3 className="text-lg font-medium text-red-800 dark:text-red-200 mb-2">Generation Failed</h3>
                    <p className="text-sm text-red-600 dark:text-red-300 text-center mb-4">{mindMapError}</p>
                    <Button variant="outline" onClick={resetMindMap}>Try Again</Button>
                  </div>
                ) : (
                  <MindMapForm
                    onSubmit={handleMindMapSubmit}
                    isGenerating={isMindMapGenerating}
                  />
                )}
              </div>

              {/* Right: Mind Map Viewer */}
              <div className="order-1 lg:order-2 lg:sticky lg:top-24 lg:self-start min-h-[500px] lg:h-[calc(100vh-200px)]">
                <MindMapViewer
                  tree={mindMapTree}
                  onReset={resetMindMap}
                />
              </div>
            </div>
          ) : selectedFeature.id === "idea-canvas" ? (
            /* Idea Canvas Layout */
            canvasState === "idle" || canvasState === "starting" ? (
              /* Show form when idle */
              <div className="max-w-2xl mx-auto">
                <IdeaCanvasForm
                  onSubmit={handleCanvasSubmit}
                  isStarting={isCanvasStarting}
                />
              </div>
            ) : canvasState === "error" ? (
              /* Show error state */
              <div className="max-w-md mx-auto">
                <div className="flex flex-col items-center justify-center min-h-[400px] p-8 rounded-xl border border-red-200 bg-red-50 dark:bg-red-950/20 dark:border-red-800">
                  <svg className="w-12 h-12 text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h3 className="text-lg font-medium text-red-800 dark:text-red-200 mb-2">Something went wrong</h3>
                  <p className="text-sm text-red-600 dark:text-red-300 text-center mb-4">{canvasError}</p>
                  <Button variant="outline" onClick={resetCanvas}>Try Again</Button>
                </div>
              </div>
            ) : canvasState === "suggest_complete" || reportData || exitedToSummary ? (
              /* Completion/Summary state - Split view: Canvas left, Report right */
              <div className="grid gap-6 lg:grid-cols-2">
                {/* Left: Canvas Decision Tree */}
                <div className="order-1 lg:sticky lg:top-24 lg:self-start">
                  <div className="border rounded-xl overflow-hidden bg-card">
                    <div className="px-4 py-3 border-b bg-muted/50 flex items-center justify-between">
                      <h4 className="font-medium text-sm">Decision Tree</h4>
                      <span className="text-xs text-muted-foreground">
                        {canvas?.question_count || 0} questions explored
                      </span>
                    </div>
                    <div className="h-[500px] lg:h-[calc(100vh-280px)]">
                      <IdeaCanvas
                        canvas={canvas}
                        currentQuestion={null}
                        progressMessage={null}
                        isAnswering={false}
                        onAnswer={() => {}}
                        onReset={resetCanvas}
                        isSuggestComplete={true}
                        hideQuestionCard={true}
                      />
                    </div>
                  </div>
                </div>

                {/* Right: Report & Actions */}
                <div className="order-2 flex flex-col lg:min-h-[calc(100vh-280px)]">
                  <div className="flex flex-col gap-6 h-full">
                    {/* Success Card */}
                    <div className="bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-950/30 dark:to-teal-950/30 border border-emerald-200 dark:border-emerald-800 rounded-xl p-6">
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-full flex items-center justify-center shrink-0">
                          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                        <div>
                          <h3 className="font-semibold text-lg text-emerald-800 dark:text-emerald-200">
                            {reportData ? "Report Generated!" : "Exploration Complete!"}
                          </h3>
                          <p className="text-sm text-emerald-600 dark:text-emerald-400 mt-1">
                            {canvasProgressMessage || `Explored ${canvas?.question_count || 0} questions about your idea.`}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Report Error */}
                    {reportError && (
                      <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-sm text-red-600 dark:text-red-400">
                        {reportError}
                      </div>
                    )}

                    {/* Actions Card */}
                    <div className="bg-card border rounded-xl p-6">
                      <h4 className="font-medium mb-4">
                        {reportData ? "Download Your Spec" : "Generate Implementation Spec"}
                      </h4>
                      
                      {!reportData ? (
                        <div className="space-y-3">
                          <Button 
                            onClick={handleGenerateReport} 
                            disabled={isGeneratingReport}
                            className="w-full"
                            size="lg"
                          >
                            {isGeneratingReport ? (
                              <>
                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                                Generating Report Pack...
                              </>
                            ) : (
                              <>
                                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                Generate Report Pack
                              </>
                            )}
                          </Button>
                          <Button onClick={() => handleCanvasAnswer("continue")} variant="outline" className="w-full">
                            Continue Exploring
                          </Button>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {/* Download Buttons */}
                          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                            <Button 
                              onClick={handleDownloadPdf} 
                              disabled={!reportData?.pdf_base64}
                              className="w-full" 
                              size="lg"
                            >
                              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                              </svg>
                              Download PDF
                            </Button>
                            <Button onClick={handleDownloadMarkdown} variant="outline" className="w-full" size="lg">
                              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                              </svg>
                              Download MD
                            </Button>
                            <Button
                              onClick={() => {
                                if (generatedImage) {
                                  downloadImage(
                                    generatedImage.data,
                                    `${reportData?.title.replace(/[^a-z0-9]/gi, "_").toLowerCase() || "infographic"}`,
                                    generatedImage.format as "png" | "svg"
                                  );
                                }
                              }}
                              disabled={!generatedImage || isGeneratingImage}
                              variant="outline"
                              className="w-full"
                              size="lg"
                            >
                              {isGeneratingImage ? (
                                <>
                                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                                  Generating Image...
                                </>
                              ) : (
                                <>
                                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                  </svg>
                                  Download Image
                                </>
                              )}
                            </Button>
                          </div>

                          {imageGenError && (
                            <p className="text-xs text-red-600">{imageGenError}</p>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Preview Card with Tabs */}
                    {reportData && (
                      <div className="bg-card border rounded-xl overflow-hidden flex flex-col flex-1 min-h-[560px]">
                        <div className="px-4 py-3 border-b bg-muted/50">
                          <h4 className="font-medium text-sm">Report Preview</h4>
                        </div>

                        <Tabs defaultValue="pdf" className="flex flex-col flex-1 min-h-[560px]">
                          <div className="px-4 pt-3">
                            <TabsList>
                              <TabsTrigger value="pdf">PDF</TabsTrigger>
                              <TabsTrigger value="markdown">Markdown</TabsTrigger>
                              <TabsTrigger value="image">Image</TabsTrigger>
                            </TabsList>
                          </div>

                          <TabsContent value="pdf" className="flex flex-1 min-h-[520px] flex-col">
                            <div className="flex items-center justify-end px-4 py-2 border-b">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={handleOpenPdfPreview}
                                disabled={!reportData.pdf_base64}
                              >
                                Open in New Tab
                              </Button>
                            </div>
                            <div className="flex-1 min-h-0">
                              {reportData.pdf_base64 ? (
                                <iframe
                                  src={`data:application/pdf;base64,${reportData.pdf_base64}#view=FitH&zoom=page-width`}
                                  className="w-full h-full border-0 bg-white"
                                  title="PDF Preview"
                                />
                              ) : (
                                <div className="flex items-center justify-center h-full text-muted-foreground">
                                  <p>PDF generation in progress...</p>
                                </div>
                              )}
                            </div>
                          </TabsContent>

                          <TabsContent value="markdown" className="p-4 flex-1 min-h-[520px] overflow-y-auto space-y-3">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-muted-foreground">Markdown</span>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={handleCopyMarkdown}
                                disabled={!reportData.markdown_content}
                              >
                                {markdownCopied ? "Copied" : "Copy"}
                              </Button>
                            </div>
                            <pre className="text-sm font-mono whitespace-pre-wrap text-muted-foreground leading-relaxed">
                              {reportData.markdown_content}
                            </pre>
                          </TabsContent>

                          <TabsContent value="image" className="p-4 flex-1 min-h-[520px] overflow-y-auto">
                            {isGeneratingImage ? (
                              <div className="flex items-center justify-center h-[420px] text-muted-foreground">
                                <div className="flex items-center gap-2 text-sm">
                                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                                  Generating visual summary...
                                </div>
                              </div>
                            ) : generatedImage ? (
                              <div className="space-y-3">
                                <div className="rounded-lg border overflow-hidden bg-white">
                                  <img
                                    src={`data:image/${generatedImage.format};base64,${generatedImage.data}`}
                                    alt="Generated infographic"
                                    className="w-full h-auto"
                                  />
                                </div>
                              </div>
                            ) : imageGenError ? (
                              <div className="flex items-center justify-center h-[420px] text-red-600 text-sm">
                                {imageGenError}
                              </div>
                            ) : (
                              <div className="flex items-center justify-center h-[420px] text-muted-foreground text-sm">
                                Image generation pending...
                              </div>
                            )}
                          </TabsContent>
                        </Tabs>
                      </div>
                    )}

                    {/* Start New */}
                    <Button 
                      variant="ghost" 
                      onClick={() => { resetCanvas(); setReportData(null); setExitedToSummary(false); }}
                      className="w-full mt-auto"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Start New Canvas
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              /* Active questioning - Fullscreen mode */
              <div className="fixed inset-0 z-50 bg-background">
                {/* Header */}
                <div className="h-14 border-b flex items-center justify-between px-4">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleExitToSummary}
                      className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Finish & View Summary
                    </button>
                    <div className="h-6 w-px bg-border" />
                    <span className="text-sm font-medium">{canvas?.idea.slice(0, 50)}{(canvas?.idea.length || 0) > 50 ? "..." : ""}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-sm text-muted-foreground">
                      Questions: <span className="font-medium text-foreground">{canvas?.question_count || 0}</span>
                    </div>
                  </div>
                </div>

                {/* Main content: Questions left, Canvas right */}
                <div className="h-[calc(100vh-3.5rem)] flex">
                  {/* Left: Question Panel */}
                  <div className="w-[420px] border-r bg-muted/30 flex flex-col">
                    {/* Progress indicator */}
                    {questionHistory.length > 0 && (
                      <div className="px-6 pt-4 pb-2 border-b flex items-center justify-end">
                        <span className="text-xs text-muted-foreground">
                          Q{questionHistory.length + 1} of ~{Math.max(questionHistory.length + 3, 8)}
                        </span>
                      </div>
                    )}
                    
                    <div className="flex-1 overflow-y-auto p-6">
                      {currentQuestion ? (
                        <QuestionCard
                          question={currentQuestion}
                          onAnswer={handleCanvasAnswer}
                          onSkip={currentQuestion.allow_skip ? () => handleCanvasAnswer("Skipped") : undefined}
                          isAnswering={isCanvasAnswering}
                        />
                      ) : (
                        <div className="flex items-center justify-center h-full">
                          <div className="text-center">
                            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                            <p className="text-sm text-muted-foreground">{canvasProgressMessage || "Loading next question..."}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Right: Canvas Visualization */}
                  <div className="flex-1 bg-card">
                    <IdeaCanvas
                      canvas={canvas}
                      currentQuestion={currentQuestion}
                      progressMessage={null}
                      isAnswering={isCanvasAnswering}
                      onAnswer={handleCanvasAnswer}
                      onReset={resetCanvas}
                      isSuggestComplete={false}
                      hideQuestionCard={true}
                    />
                  </div>
                </div>
              </div>
            )
          ) : (
            /* Split Layout for other features */
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
                  userId={user?.id}
                  outputFormat={selectedFeature.defaultOutputFormat}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Show feature tiles
  return (
    <div className="container mx-auto px-4 py-8 md:py-12">
      {/* Auth Modal */}
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
      
      <div className="mx-auto max-w-5xl space-y-8">
        <div className="text-center space-y-3">
          <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
            What would you like to create?
          </h1>
          <p className="text-muted-foreground text-lg">
            Choose a format and we'll guide you through the process
          </p>
          
          {/* Sign-in prompt for non-authenticated users */}
          {!authLoading && !isAuthenticated && (
            <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span className="text-sm font-medium">
                Please{" "}
                <button
                  onClick={() => setShowAuthModal(true)}
                  className="underline hover:no-underline font-semibold"
                >
                  sign in
                </button>
                {" "}to start generating documents
              </span>
            </div>
          )}
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
