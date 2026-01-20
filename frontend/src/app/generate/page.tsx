"use client";

import { useCallback, useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useGeneration } from "@/hooks/useGeneration";
import { useMindMapGeneration } from "@/hooks/useMindMapGeneration";
import { useAuth } from "@/hooks/useAuth";
import { AuthModal } from "@/components/auth/AuthModal";
import { UploadedFile } from "@/hooks/useUpload";
import {
  SourceInput,
  OutputTypeSelector,
  DynamicOptions,
  StudioRightPanel,
  contentModelOptions,
} from "@/components/studio";
import type { StudioOutputType } from "@/components/studio";
import { MindMapProgress } from "@/components/mindmap";
import { generateImage } from "@/lib/api/image";
import { StyleCategory } from "@/data/imageStyles";
import {
  Provider,
  Audience,
  ImageStyle,
  SourceItem,
  OutputFormat,
} from "@/lib/types/requests";
import { MindMapMode } from "@/lib/types/mindmap";
import type { OutputFormat as ImageOutputFormat } from "@/lib/types/image";

// Map studio output types to API output formats
function getApiOutputFormat(studioType: StudioOutputType): OutputFormat {
  switch (studioType) {
    case "article_pdf":
      return "pdf";
    case "article_markdown":
      return "markdown";
    case "slide_deck_pdf":
      return "pdf_from_pptx";
    case "presentation_pptx":
      return "pptx";
    default:
      return "pdf";
  }
}

export default function GeneratePage() {
  // Auth state
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Output type selection
  const [outputType, setOutputType] = useState<StudioOutputType>("presentation_pptx");

  // Source state
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [urls, setUrls] = useState<string[]>([]);
  const [textContent, setTextContent] = useState("");

  // Configuration state
  const [provider, setProvider] = useState<Provider>("gemini");
  const [contentModel, setContentModel] = useState("gemini-2.5-flash");
  const [imageModel, setImageModel] = useState("gemini-3-pro-image-preview");
  const [audience, setAudience] = useState<Audience>("technical");
  const [imageStyle, setImageStyle] = useState<ImageStyle>("auto");
  const [mindMapMode, setMindMapMode] = useState<MindMapMode>("summarize");
  const [enableImageGeneration, setEnableImageGeneration] = useState(false);
  const [contentApiKey, setContentApiKey] = useState("");
  const [imageApiKey, setImageApiKey] = useState("");

  // Image generation specific state
  const [imagePrompt, setImagePrompt] = useState("");
  const [imageCategory, setImageCategory] = useState<StyleCategory | null>(null);
  const [selectedStyleId, setSelectedStyleId] = useState<string | null>(null);
  const [imageOutputFormat, setImageOutputFormat] = useState<ImageOutputFormat>("raster");
  const [imageGenState, setImageGenState] = useState<"idle" | "generating" | "success" | "error">("idle");
  const [imageGenError, setImageGenError] = useState<string | null>(null);
  const [generatedImageData, setGeneratedImageData] = useState<string | null>(null);
  const [generatedImageFormat, setGeneratedImageFormat] = useState<"png" | "svg">("png");

  // Generation hooks
  const {
    state: generationState,
    progress: generationProgress,
    status: generationStatus,
    downloadUrl,
    error: generationError,
    metadata,
    generate,
    reset: resetGeneration,
  } = useGeneration();

  const {
    state: mindMapState,
    tree: mindMapTree,
    progress: mindMapProgress,
    error: mindMapError,
    generate: generateMindMap,
    reset: resetMindMap,
  } = useMindMapGeneration();

  // Update content model when provider changes
  useEffect(() => {
    const options = contentModelOptions[provider] || [];
    if (options.length && !options.some((o) => o.value === contentModel)) {
      const defaultByProvider: Partial<Record<Provider, string>> = {
        gemini: "gemini-2.5-flash",
        google: "gemini-2.5-flash",
        openai: "gpt-4.1-mini",
        anthropic: "claude-haiku-4-5-20251001",
      };
      setContentModel(defaultByProvider[provider] || options[0].value);
    }
  }, [provider, contentModel]);

  // Build sources from inputs
  const buildSources = useCallback((): SourceItem[] => {
    const sources: SourceItem[] = [];
    uploadedFiles.forEach((f) => {
      sources.push({ type: "file", file_id: f.fileId });
    });
    urls.forEach((url) => {
      sources.push({ type: "url", url });
    });
    if (textContent.trim()) {
      sources.push({ type: "text", content: textContent.trim() });
    }
    return sources;
  }, [uploadedFiles, urls, textContent]);

  // Check if we have required inputs
  const hasSources = uploadedFiles.length > 0 || urls.length > 0 || textContent.trim().length > 0;
  const isContentType = ["article_pdf", "article_markdown", "slide_deck_pdf", "presentation_pptx"].includes(outputType);
  const isImageType = outputType === "image_generate";
  const isMindMap = outputType === "mindmap";

  const hasRequiredApiKeys = (() => {
    if (isContentType) {
      return contentApiKey.trim() && (!enableImageGeneration || imageApiKey.trim());
    }
    if (isMindMap) {
      return contentApiKey.trim();
    }
    if (isImageType) {
      return imageApiKey.trim();
    }
    return true;
  })();

  // For image types, we use the same sources (textContent) as other types
  const canGenerate = hasSources && hasRequiredApiKeys && !authLoading && isAuthenticated;

  // Handle generation
  const handleGenerate = useCallback(async () => {
    if (!canGenerate) return;

    // Handle image generation
    if (isImageType) {
      setImageGenState("generating");
      setImageGenError(null);
      setGeneratedImageData(null);

      // Use textContent from SourceInput as the prompt for image generation
      const prompt = textContent.trim();
      if (!prompt) {
        setImageGenError("Please enter a description in the Sources text input");
        setImageGenState("error");
        return;
      }

      try {
        const result = await generateImage(
          {
            prompt: prompt,
            style_category: imageCategory,
            style: selectedStyleId,
            output_format: imageOutputFormat,
            free_text_mode: !imageCategory,
          },
          imageApiKey
        );

        if (result.success && result.image_data) {
          setGeneratedImageData(result.image_data);
          setGeneratedImageFormat(result.format);
          setImageGenState("success");
        } else {
          setImageGenError(result.error || "Image generation failed");
          setImageGenState("error");
        }
      } catch (err) {
        setImageGenError(err instanceof Error ? err.message : "Image generation failed");
        setImageGenState("error");
      }
      return;
    }

    const sources = buildSources();

    if (isContentType) {
      generate(
        {
          output_format: getApiOutputFormat(outputType),
          sources,
          provider,
          model: contentModel,
          image_model: imageModel,
          preferences: {
            audience,
            image_style: imageStyle,
            temperature: 0.4,
            max_tokens: 12000,
            max_slides: 10,
            max_summary_points: 5,
            enable_image_generation: enableImageGeneration,
          },
        },
        contentApiKey,
        enableImageGeneration ? imageApiKey : undefined,
        user?.id
      );
    } else if (isMindMap) {
      generateMindMap(
        {
          sources,
          mode: mindMapMode,
          provider,
          model: contentModel,
        },
        contentApiKey,
        user?.id
      );
    }
  }, [
    canGenerate,
    buildSources,
    isContentType,
    isMindMap,
    isImageType,
    outputType,
    provider,
    contentModel,
    imageModel,
    audience,
    imageStyle,
    enableImageGeneration,
    contentApiKey,
    imageApiKey,
    mindMapMode,
    imagePrompt,
    imageCategory,
    selectedStyleId,
    imageOutputFormat,
    generate,
    generateMindMap,
    user?.id,
  ]);

  // Reset handler
  const handleReset = useCallback(() => {
    resetGeneration();
    resetMindMap();
    setImageGenState("idle");
    setImageGenError(null);
    setGeneratedImageData(null);
  }, [resetGeneration, resetMindMap]);

  // Download handler
  const handleDownload = useCallback(() => {
    if (downloadUrl) {
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = metadata?.title || "document";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }

  }, [downloadUrl, metadata]);

  // Determine current state for right panel (map to panel's expected states)
  type PanelState = "idle" | "generating" | "success" | "error";
  
  const getCurrentState = (): PanelState => {
    if (isImageType) {
      return imageGenState;
    }
    if (isMindMap) {
      if (mindMapState === "generating") return "generating";
      if (mindMapState === "error") return "error";
      if (mindMapState === "complete") return "success";
      return "idle";
    }
    // Map hook state to panel state
    if (generationState === "generating") return "generating";
    if (generationState === "error") return "error";
    if (generationState === "complete" || generationState === "cache_hit") return "success";
    return "idle";
  };

  const getCurrentProgress = (): number => {
    if (isImageType) return imageGenState === "generating" ? 50 : (imageGenState === "success" ? 100 : 0);
    if (isMindMap) return mindMapProgress.percent;
    return generationProgress;
  };

  const getCurrentStatus = (): string => {
    if (isImageType) {
      if (imageGenState === "generating") return "Generating image...";
      if (imageGenState === "success") return "Image generated successfully";
      if (imageGenState === "error") return "Image generation failed";
      return "";
    }
    if (isMindMap) return mindMapProgress.message || "Processing...";
    return generationStatus;
  };

  const getCurrentError = (): string | null => {
    if (isImageType) return imageGenError;
    if (isMindMap) return mindMapError;
    return generationError;
  };

  // Auth gate - if not authenticated, show sign in prompt
  if (!authLoading && !isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white dark:from-slate-950 dark:to-slate-900 flex items-center justify-center">
        <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
        <div className="text-center max-w-md mx-auto p-8">
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
            <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold mb-3">Welcome to PrismDocs Studio</h1>
          <p className="text-muted-foreground mb-6">
            Sign in to start generating documents, presentations, mind maps, and images from your content.
          </p>
          <Button size="lg" onClick={() => setShowAuthModal(true)} className="w-full">
            Sign In to Continue
          </Button>
        </div>
      </div>
    );
  }

  // Loading state
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white dark:from-slate-950 dark:to-slate-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-muted-foreground">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      {/* Auth Modal */}
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />

      {/* Enhanced Header */}
      <header className="border-b border-border/40 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md sticky top-0 z-40 shadow-sm">
        <div className="px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <a href="/" className="flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 via-purple-500 to-fuchsia-500 flex items-center justify-center shadow-lg shadow-purple-500/20 group-hover:shadow-purple-500/40 transition-shadow">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <span className="font-bold text-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 bg-clip-text text-transparent">PrismDocs</span>
                <span className="font-medium text-xl text-muted-foreground ml-1">Studio</span>
              </div>
            </a>
          </div>
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              className="text-amber-600 border-amber-200 hover:bg-amber-50 hover:border-amber-300 shadow-sm"
              onClick={() => window.location.href = "/generate/idea-canvas"}
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              Idea Canvas
            </Button>
          </div>
        </div>
      </header>

      {/* Main Studio Layout - Full screen, equal panels */}
      <main className="h-[calc(100vh-4rem)]">
        <div className="h-full grid gap-0 lg:grid-cols-2">
          {/* Left Panel - Inputs (scrollable) */}
          <div className="border-r border-border/30 bg-white/60 dark:bg-slate-900/60 overflow-y-auto p-6 space-y-5">
            {/* Section Header */}
            <div className="flex items-center gap-2 pb-2 border-b border-border/30">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold">Configure Generation</h2>
            </div>

            {/* Source Input */}
            <div className="rounded-2xl border border-border/50 bg-card/80 backdrop-blur-sm p-5 shadow-sm hover:shadow-md transition-shadow">
              <SourceInput
                onSourcesChange={() => {}}
                uploadedFiles={uploadedFiles}
                urls={urls}
                textContent={textContent}
                onFilesChange={setUploadedFiles}
                onUrlsChange={setUrls}
                onTextChange={setTextContent}
              />
            </div>

            {/* Output Type Selector */}
            <div className="rounded-2xl border border-border/50 bg-card/80 backdrop-blur-sm p-5 shadow-sm hover:shadow-md transition-shadow">
              <OutputTypeSelector
                selectedType={outputType}
                onTypeChange={setOutputType}
              />
            </div>

            {/* Dynamic Options */}
            <div className="rounded-2xl border border-border/50 bg-card/80 backdrop-blur-sm p-5 shadow-sm hover:shadow-md transition-shadow">
              <DynamicOptions
                outputType={outputType}
                provider={provider}
                contentModel={contentModel}
                imageModel={imageModel}
                audience={audience}
                imageStyle={imageStyle}
                mindMapMode={mindMapMode}
                enableImageGeneration={enableImageGeneration}
                contentApiKey={contentApiKey}
                imageApiKey={imageApiKey}
                imagePrompt={imagePrompt}
                imageCategory={imageCategory}
                selectedStyleId={selectedStyleId}
                imageOutputFormat={imageOutputFormat}
                onProviderChange={setProvider}
                onContentModelChange={setContentModel}
                onImageModelChange={setImageModel}
                onAudienceChange={setAudience}
                onImageStyleChange={setImageStyle}
                onMindMapModeChange={setMindMapMode}
                onEnableImageGenerationChange={setEnableImageGeneration}
                onContentApiKeyChange={setContentApiKey}
                onImageApiKeyChange={setImageApiKey}
                onImagePromptChange={setImagePrompt}
                onImageCategoryChange={setImageCategory}
                onSelectedStyleIdChange={setSelectedStyleId}
                onImageOutputFormatChange={setImageOutputFormat}
              />
            </div>

            {/* Generate Button */}
            <Button
              size="lg"
              className="w-full h-12 text-base font-semibold shadow-lg hover:shadow-xl transition-all"
              disabled={!canGenerate || getCurrentState() === "generating"}
              onClick={handleGenerate}
            >
              {getCurrentState() === "generating" ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                  Generating...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Generate
                </>
              )}
            </Button>
          </div>

          {/* Right Panel - Output (full height) */}
          <div className="overflow-hidden p-4">
            <div className="h-full">
              {isMindMap && mindMapState === "generating" ? (
                <div className="flex items-center justify-center h-full rounded-xl border bg-card">
                  <MindMapProgress
                    stage={mindMapProgress.stage}
                    progress={mindMapProgress.percent}
                    message={mindMapProgress.message}
                  />
                </div>
              ) : (
                <StudioRightPanel
                  outputType={outputType}
                  state={getCurrentState()}
                  progress={getCurrentProgress()}
                  status={getCurrentStatus()}
                  error={getCurrentError()}
                  downloadUrl={downloadUrl}
                  mindMapTree={mindMapTree}
                  metadata={metadata}
                  imageData={generatedImageData}
                  imageFormat={generatedImageFormat}
                  onReset={handleReset}
                  onDownload={handleDownload}
                  userId={user?.id}
                  imageApiKey={imageApiKey}
                />
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
