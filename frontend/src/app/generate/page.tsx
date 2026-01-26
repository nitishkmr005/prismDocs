"use client";

import { useCallback, useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useGeneration } from "@/hooks/useGeneration";
import { useMindMapGeneration } from "@/hooks/useMindMapGeneration";
import { usePodcastGeneration } from "@/hooks/usePodcastGeneration";
import { useFAQGeneration } from "@/hooks/useFAQGeneration";
import { useAuth } from "@/hooks/useAuth";
import { AuthModal } from "@/components/auth/AuthModal";
import { UploadedFile } from "@/hooks/useUpload";
import {
  SourceInput,
  OutputTypeSelector,
  DynamicOptions,
  ApiKeysModal,
  StudioRightPanel,
  contentModelOptions,
} from "@/components/studio";
import type { StudioOutputType } from "@/components/studio";
import type { CombinedOutputType } from "@/components/studio/OutputTypeSelector";
import { MindMapProgress } from "@/components/mindmap";
import { generateImage } from "@/lib/api/image";
import { generateDocument } from "@/lib/api/generate";
import { isCompleteEvent, isCacheHitEvent } from "@/lib/types/responses";
import { StyleCategory } from "@/data/imageStyles";
import { getApiUrl } from "@/config/api";
import {
  Provider,
  Audience,
  ImageStyle,
  SourceItem,
  OutputFormat,
  DEFAULT_PREFERENCES,
  DEFAULT_CACHE_OPTIONS,
} from "@/lib/types/requests";
import { MindMapMode } from "@/lib/types/mindmap";
import type { OutputFormat as ImageOutputFormat } from "@/lib/types/image";
import { PodcastStyle, SpeakerConfig, DEFAULT_SPEAKERS } from "@/lib/types/podcast";

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
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);

  // Panel collapse state
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false);

  // Collapsible section state for left panel
  const [expandedSections, setExpandedSections] = useState<{
    sources: boolean;
    outputType: boolean;
    options: boolean;
  }>({
    sources: true,
    outputType: true,
    options: true,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  // Output type selection
  const [outputType, setOutputType] = useState<StudioOutputType>("presentation_pptx");
  const [combinedOutputType, setCombinedOutputType] = useState<CombinedOutputType | null>("presentation");

  // Source state
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [urls, setUrls] = useState<string[]>([]);
  const [textContent, setTextContent] = useState("");

  // Configuration state
  const [provider, setProvider] = useState<Provider>("gemini");
  const [contentModel, setContentModel] = useState("gemini-2.5-flash");
  const [imageModel, setImageModel] = useState("gemini-2.5-flash-image");
  const [audience, setAudience] = useState<Audience>("technical");
  const [imageStyle, setImageStyle] = useState<ImageStyle>("auto");
  const [mindMapMode, setMindMapMode] = useState<MindMapMode>("summarize");
  const [enableImageGeneration, setEnableImageGeneration] = useState(false);
  const [contentApiKey, setContentApiKey] = useState("");
  const [imageApiKey, setImageApiKey] = useState("");
  const hasContentKey = contentApiKey.trim().length > 0;
  // For Gemini, use content key for images if no explicit image key is provided
  const effectiveImageKey = imageApiKey.trim() || (provider === "gemini" ? contentApiKey.trim() : "");
  const hasImageKey = effectiveImageKey.length > 0;
  // Check if user has Gemini API key available (for features like podcast/image that require Gemini)
  // Gemini key is available if: explicit image key exists, OR user is using Gemini provider with content key
  const hasGeminiKey = imageApiKey.trim().length > 0 || (provider === "gemini" && contentApiKey.trim().length > 0);


  // Image generation specific state
  const [imagePrompt, setImagePrompt] = useState("");
  const [imageCategory, setImageCategory] = useState<StyleCategory | null>("diagram_and_architecture");
  const [selectedStyleId, setSelectedStyleId] = useState<string | null>(null);
  const [imageOutputFormat, setImageOutputFormat] = useState<ImageOutputFormat>("raster");
  const [imageGenState, setImageGenState] = useState<"idle" | "generating" | "success" | "error">("idle");
  const [imageGenError, setImageGenError] = useState<string | null>(null);
  const [generatedImageData, setGeneratedImageData] = useState<string | null>(null);
  const [generatedImageFormat, setGeneratedImageFormat] = useState<"png" | "svg">("png");

  // Podcast generation specific state
  const [podcastStyle, setPodcastStyle] = useState<PodcastStyle>("conversational");
  const [podcastSpeakers, setPodcastSpeakers] = useState<SpeakerConfig[]>(DEFAULT_SPEAKERS);
  const [podcastDuration, setPodcastDuration] = useState(3);
  // Podcast enablement for non-Gemini providers
  const [enablePodcast, setEnablePodcast] = useState(true);
  const [podcastGeminiApiKey, setPodcastGeminiApiKey] = useState("");
  // Effective podcast key: use explicit podcast key if provided, otherwise use content key for Gemini provider
  const effectivePodcastKey = provider === "gemini" ? contentApiKey : podcastGeminiApiKey;
  // Podcast is actually enabled when: enabled toggle is on AND has the right key
  const isPodcastActuallyEnabled = provider === "gemini" ? hasGeminiKey : (enablePodcast && podcastGeminiApiKey.trim().length > 0);

  // Generation hooks
  const {
    state: generationState,
    progress: generationProgress,
    status: generationStatus,
    downloadUrl,
    error: generationError,
    pdfBase64,
    markdownContent,
    metadata,
    generate,
    reset: resetGeneration,
  } = useGeneration();

  // Secondary generation state (for combined output types)
  const [secondaryPdfBase64, setSecondaryPdfBase64] = useState<string | null>(null);
  const [secondaryMarkdownContent, setSecondaryMarkdownContent] = useState<string | null>(null);
  const [secondaryDownloadUrl, setSecondaryDownloadUrl] = useState<string | null>(null);
  const [isSecondaryGenerating, setIsSecondaryGenerating] = useState(false);

  const {
    state: mindMapState,
    tree: mindMapTree,
    progress: mindMapProgress,
    error: mindMapError,
    generate: generateMindMap,
    reset: resetMindMap,
  } = useMindMapGeneration();

  const {
    state: podcastState,
    progress: podcastProgress,
    result: podcastResult,
    error: podcastError,
    generate: generatePodcast,
    reset: resetPodcast,
  } = usePodcastGeneration();

  const {
    state: faqState,
    progress: faqProgress,
    result: faqResult,
    error: faqError,
    generate: generateFAQ,
    reset: resetFAQ,
  } = useFAQGeneration();

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
  const isImageFreeTextMode = !imageCategory;
  const hasImagePrompt = isImageFreeTextMode && imagePrompt.trim().length > 0;
  const isContentType = ["article_pdf", "article_markdown", "slide_deck_pdf", "presentation_pptx"].includes(outputType);
  const isImageType = outputType === "image_generate";
  const isMindMap = outputType === "mindmap";
  const isPodcast = outputType === "podcast";
  const isFaq = outputType === "faq";
  const requiresImageKey = isImageType || (isContentType && enableImageGeneration);

  const hasRequiredApiKeys = (() => {
    if (isContentType) {
      return hasContentKey && (!enableImageGeneration || hasImageKey);
    }
    if (isMindMap) {
      return hasContentKey;
    }
    if (isPodcast) {
      // Podcast requires content key for script generation AND Gemini key for TTS
      // For Gemini provider, content key is used for both; for others, need separate podcast Gemini key
      const hasPodcastKey = provider === "gemini" ? hasGeminiKey : (enablePodcast && podcastGeminiApiKey.trim().length > 0);
      return hasContentKey && hasPodcastKey;
    }
    if (isFaq) {
      return hasContentKey;
    }
    if (isImageType) {
      const needsContentKey = !isImageFreeTextMode && hasSources;
      return hasImageKey && (!needsContentKey || hasContentKey);
    }
    return true;
  })();

  // For image types, allow prompt-only generation
  const canGenerate = (isImageType ? (isImageFreeTextMode ? hasImagePrompt : hasSources) : hasSources)
    && !authLoading
    && isAuthenticated;

  // Load API keys from sessionStorage (set by home page)
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    const storedContentKey = sessionStorage.getItem('prismdocs_content_api_key');
    const storedProvider = sessionStorage.getItem('prismdocs_provider') as Provider | null;
    const storedModel = sessionStorage.getItem('prismdocs_content_model');
    const storedImageKey = sessionStorage.getItem('prismdocs_image_api_key');
    const storedEnableImages = sessionStorage.getItem('prismdocs_enable_image_generation');
    
    if (storedContentKey) {
      setContentApiKey(storedContentKey);
      sessionStorage.removeItem('prismdocs_content_api_key');
    }
    if (storedProvider) {
      setProvider(storedProvider);
      sessionStorage.removeItem('prismdocs_provider');
    }
    if (storedModel) {
      setContentModel(storedModel);
      sessionStorage.removeItem('prismdocs_content_model');
    }
    if (storedImageKey) {
      setImageApiKey(storedImageKey);
      sessionStorage.removeItem('prismdocs_image_api_key');
    }
    if (storedEnableImages !== null) {
      setEnableImageGeneration(storedEnableImages === "1");
      sessionStorage.removeItem('prismdocs_enable_image_generation');
    }
  }, []);

  useEffect(() => {
    if (showApiKeyModal) return;
    if (!hasImageKey && enableImageGeneration) {
      setEnableImageGeneration(false);
    }
  }, [showApiKeyModal, hasImageKey, enableImageGeneration]);

  useEffect(() => {
    if (showApiKeyModal) return;
    if (!hasImageKey && outputType === "image_generate") {
      setOutputType("presentation_pptx");
    }
  }, [showApiKeyModal, hasImageKey, outputType]);

  // Handle generation
  const handleGenerate = useCallback(async () => {
    if (!canGenerate || !hasRequiredApiKeys) return;


    // Handle image generation
    if (isImageType) {
      setImageGenState("generating");
      setImageGenError(null);
      setGeneratedImageData(null);

      const isFreeTextMode = !imageCategory;
      const sources = isFreeTextMode ? [] : buildSources();
      const prompt = isFreeTextMode ? imagePrompt.trim() : "";

      if (isFreeTextMode && !prompt) {
        setImageGenError("Please enter a prompt for free text mode.");
        setImageGenState("error");
        return;
      }

      if (!isFreeTextMode && sources.length === 0) {
        setImageGenError("Please add a source to summarize.");
        setImageGenState("error");
        return;
      }

      try {
        const result = await generateImage(
          {
            prompt: prompt || undefined,
            sources: sources.length ? sources : undefined,
            provider,
            model: contentModel,
            style_category: imageCategory,
            style: selectedStyleId,
            output_format: imageOutputFormat,
            free_text_mode: isFreeTextMode,
          },
          effectiveImageKey,
          {
            provider,
            contentApiKey,
            userId: user?.id,
          }
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
      // Clear secondary generation state
      setSecondaryPdfBase64(null);
      setSecondaryMarkdownContent(null);
      setSecondaryDownloadUrl(null);

      // Primary generation
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
            max_slides: 25,
            max_summary_points: 5,
            enable_image_generation: enableImageGeneration,
          },
        },
        contentApiKey,
        enableImageGeneration ? effectiveImageKey : undefined,
        user?.id
      );

      // Secondary generation for combined types
      if (combinedOutputType) {
        setIsSecondaryGenerating(true);

        // Determine secondary format
        let secondaryFormat: OutputFormat;
        if (combinedOutputType === "article") {
          // Article: Primary is PDF, secondary is Markdown
          secondaryFormat = "markdown";
        } else {
          // Presentation: Primary is PPTX, secondary is PDF from PPTX
          secondaryFormat = "pdf_from_pptx";
        }

        // Build request for secondary generation
        const secondaryRequest = {
          output_format: secondaryFormat,
          sources,
          provider,
          model: contentModel,
          image_model: imageModel,
          preferences: {
            ...DEFAULT_PREFERENCES,
            audience,
            image_style: imageStyle,
            temperature: 0.4,
            max_tokens: 12000,
            max_slides: 25,
            max_summary_points: 5,
            enable_image_generation: enableImageGeneration,
          },
          cache: DEFAULT_CACHE_OPTIONS,
        };

        // Trigger secondary generation in parallel
        generateDocument({
          request: secondaryRequest,
          apiKey: contentApiKey,
          imageApiKey: enableImageGeneration ? effectiveImageKey : undefined,
          userId: user?.id,
          onEvent: (event) => {
            if (isCompleteEvent(event) || isCacheHitEvent(event)) {
              if (combinedOutputType === "article") {
                setSecondaryMarkdownContent(event.markdown_content || null);
              } else {
                setSecondaryPdfBase64(event.pdf_base64 || null);
              }
              setSecondaryDownloadUrl(event.download_url || null);
              setIsSecondaryGenerating(false);
            }
          },
          onError: () => {
            setIsSecondaryGenerating(false);
          },
        }).catch(() => {
          setIsSecondaryGenerating(false);
        });
      }
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
    } else if (isPodcast) {
      generatePodcast(
        {
          sources,
          style: podcastStyle,
          provider,
          model: contentModel,
          speakers: podcastSpeakers,
          duration_minutes: podcastDuration,
        },
        contentApiKey,
        effectivePodcastKey,
        user?.id
      );
    } else if (isFaq) {
      generateFAQ(
        {
          sources,
          provider,
          model: contentModel,
        },
        contentApiKey,
        user?.id
      );
    }
  }, [
    canGenerate,
    hasRequiredApiKeys,
    buildSources,
    isContentType,
    isMindMap,
    isPodcast,
    isImageType,
    outputType,
    combinedOutputType,
    provider,
    contentModel,
    imageModel,
    audience,
    imageStyle,
    enableImageGeneration,
    contentApiKey,
    effectiveImageKey,
    effectivePodcastKey,
    mindMapMode,
    imageCategory,
    selectedStyleId,
    imageOutputFormat,
    imagePrompt,
    podcastStyle,
    podcastSpeakers,
    podcastDuration,
    isFaq,
    generateFAQ,
    generate,
    generateMindMap,
    generatePodcast,
    textContent,
    uploadedFiles,
    urls,
    user?.id,
  ]);

  // Handle generate button click - check API keys first
  const handleGenerateClick = useCallback(() => {
    if (!canGenerate) return;
    
    // Check if we have required API keys - if not, show the modal
    if (!hasRequiredApiKeys) {
      setShowApiKeyModal(true);
      return;
    }
    
    // API keys are set, proceed with generation
    handleGenerate();
  }, [canGenerate, hasRequiredApiKeys, handleGenerate]);

  // Reset handler
  const handleReset = useCallback(() => {
    resetGeneration();
    resetMindMap();
    resetPodcast();
    resetFAQ();
    setImageGenState("idle");
    setImageGenError(null);
    setGeneratedImageData(null);
    // Clear secondary generation state
    setSecondaryPdfBase64(null);
    setSecondaryMarkdownContent(null);
    setSecondaryDownloadUrl(null);
    setIsSecondaryGenerating(false);
  }, [resetGeneration, resetMindMap, resetPodcast, resetFAQ]);

  // Download handler
  const handleDownload = useCallback(() => {
    const url = isFaq ? faqResult?.downloadUrl : downloadUrl;
    if (!url) return;
    const resolvedUrl = url.startsWith("http") ? url : getApiUrl(url);
    const a = document.createElement("a");
    a.href = resolvedUrl;
    a.download = isFaq
      ? faqResult?.document.title || "faq"
      : metadata?.title || "document";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }, [downloadUrl, faqResult, isFaq, metadata]);

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
    if (isPodcast) {
      if (podcastState === "generating") return "generating";
      if (podcastState === "error") return "error";
      if (podcastState === "complete") return "success";
      return "idle";
    }
    if (isFaq) {
      if (faqState === "generating") return "generating";
      if (faqState === "error") return "error";
      if (faqState === "complete") return "success";
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
    if (isPodcast) return podcastProgress.percent;
    if (isFaq) return faqProgress.percent;
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
    if (isPodcast) return podcastProgress.message || "Processing...";
    if (isFaq) return faqProgress.message || "Processing...";
    return generationStatus;
  };

  const getCurrentError = (): string | null => {
    if (isImageType) return imageGenError;
    if (isMindMap) return mindMapError;
    if (isPodcast) return podcastError;
    if (isFaq) return faqError;
    return generationError;
  };

  // Auth gate - if not authenticated, show sign in prompt
  if (!authLoading && !isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-amber-50/30 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 flex items-center justify-center relative overflow-hidden">
        {/* Background effects */}
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `linear-gradient(to right, #f59e0b 1px, transparent 1px), linear-gradient(to bottom, #f59e0b 1px, transparent 1px)`,
          backgroundSize: '80px 80px'
        }} />
        <div className="absolute top-1/4 right-1/4 w-[400px] h-[400px] bg-amber-500/10 dark:bg-amber-500/5 rounded-full blur-[100px]" />

        <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
        <div className="relative text-center max-w-md mx-auto p-8">
          {/* Prism icon */}
          <div className="relative w-20 h-20 mx-auto mb-8">
            <div className="absolute inset-0 bg-gradient-to-br from-amber-500 to-amber-600 rounded-2xl rotate-45 shadow-lg shadow-amber-500/25" />
            <div className="absolute inset-0 flex items-center justify-center">
              <svg className="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2L2 19h20L12 2zm0 4l6.5 11h-13L12 6z" />
              </svg>
            </div>
          </div>
          <h1 className="font-display text-3xl font-bold text-slate-900 dark:text-white mb-3 tracking-tight">Welcome to PrismDocs</h1>
          <p className="text-slate-600 dark:text-slate-400 mb-8 leading-relaxed">
            Sign in to start generating documents, presentations, mind maps, and podcasts from your content.
          </p>
          <Button
            size="lg"
            onClick={() => setShowAuthModal(true)}
            className="w-full h-12 text-sm font-semibold uppercase tracking-wider bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-white shadow-lg shadow-amber-500/25"
          >
            Sign In to Continue
          </Button>
        </div>
      </div>
    );
  }

  // Loading state
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-amber-50/30 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 flex items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `linear-gradient(to right, #f59e0b 1px, transparent 1px), linear-gradient(to bottom, #f59e0b 1px, transparent 1px)`,
          backgroundSize: '80px 80px'
        }} />
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-3 border-amber-200 dark:border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
          <span className="text-slate-500 dark:text-slate-400 text-sm tracking-wide">Loading...</span>
        </div>
      </div>
    );
  }

  const keysStatusLabel = hasRequiredApiKeys ? "Keys set" : "Keys required";
  const keysActionLabel = hasRequiredApiKeys ? "Change" : "Add keys";

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-amber-50/30 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 relative overflow-hidden">
      {/* Subtle background texture */}
      <div className="absolute inset-0 opacity-[0.02] dark:opacity-[0.015]" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`
      }} />

      {/* Geometric grid pattern */}
      <div className="absolute inset-0 opacity-[0.03]" style={{
        backgroundImage: `linear-gradient(to right, #f59e0b 1px, transparent 1px), linear-gradient(to bottom, #f59e0b 1px, transparent 1px)`,
        backgroundSize: '80px 80px'
      }} />

      {/* Ambient glow effects */}
      <div className="absolute top-0 right-1/4 w-[600px] h-[600px] bg-amber-500/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-[400px] h-[400px] bg-amber-400/5 dark:bg-amber-500/3 rounded-full blur-[100px] pointer-events-none" />

      {/* Auth Modal */}
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
      <ApiKeysModal
        isOpen={showApiKeyModal}
        onOpenChange={setShowApiKeyModal}
        provider={provider}
        contentModel={contentModel}
        onProviderChange={setProvider}
        onContentModelChange={setContentModel}
        contentApiKey={contentApiKey}
        onContentApiKeyChange={setContentApiKey}
        enableImageGeneration={enableImageGeneration}
        onEnableImageGenerationChange={setEnableImageGeneration}
        allowImageGenerationToggle={true}
        requireImageKey={requiresImageKey}
        imageModel={imageModel}
        onImageModelChange={setImageModel}
        imageApiKey={imageApiKey}
        onImageApiKeyChange={setImageApiKey}
        canClose={hasContentKey}
        enablePodcast={enablePodcast}
        onEnablePodcastChange={setEnablePodcast}
        podcastGeminiApiKey={podcastGeminiApiKey}
        onPodcastGeminiApiKeyChange={setPodcastGeminiApiKey}
      />

      {/* Editorial Header */}
      <header className="relative z-40 border-b border-slate-200/80 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl shadow-sm dark:shadow-none">
        <div className="px-6 h-16 flex items-center justify-between max-w-screen-2xl mx-auto">
          <div className="flex items-center gap-4">
            <a href="/" className="flex items-center gap-3 group">
              {/* Prism icon with amber accent */}
              <div className="relative w-10 h-10 flex items-center justify-center">
                <div className="absolute inset-0 bg-gradient-to-br from-amber-500 to-amber-600 rounded-lg rotate-45 transform group-hover:rotate-[50deg] transition-transform duration-300 shadow-lg shadow-amber-500/20" />
                <svg className="relative w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2L2 19h20L12 2zm0 4l6.5 11h-13L12 6z" />
                </svg>
              </div>
              <div className="flex items-baseline gap-1">
                <span className="font-display font-bold text-xl text-slate-900 dark:text-white tracking-tight">PrismDocs</span>
                <span className="text-sm font-medium text-amber-600 dark:text-amber-500 tracking-wide">STUDIO</span>
              </div>
            </a>
          </div>
          <div className="flex items-center gap-3">
            {/* API Key status pill */}
            <div className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-all ${
              hasRequiredApiKeys
                ? "border-emerald-200 dark:border-emerald-500/30 bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
                : "border-amber-200 dark:border-amber-500/30 bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400"
            }`}>
              <span className={`h-1.5 w-1.5 rounded-full ${
                hasRequiredApiKeys ? "bg-emerald-500 animate-pulse" : "bg-amber-500"
              }`} />
              <span className="tracking-wide">{keysStatusLabel}</span>
              <button
                type="button"
                onClick={() => setShowApiKeyModal(true)}
                className="ml-1 text-[10px] uppercase tracking-wider opacity-60 hover:opacity-100 transition-opacity"
              >
                {keysActionLabel}
              </button>
            </div>
            {/* Idea Canvas button */}
            <Button
              variant="outline"
              size="sm"
              className="h-9 px-4 text-xs font-semibold tracking-wide uppercase border-amber-300 dark:border-amber-500/30 text-amber-700 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-500/10 hover:border-amber-400 dark:hover:border-amber-500/50 hover:text-amber-800 dark:hover:text-amber-300 transition-all"
              onClick={() => window.location.href = "/generate/idea-canvas"}
            >
              <svg className="w-3.5 h-3.5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2L2 19h20L12 2zm0 4l6.5 11h-13L12 6z" />
              </svg>
              Idea Canvas
            </Button>
          </div>
        </div>
      </header>

      {/* Main Studio Layout */}
      <main className="relative z-10 flex-1 px-4 py-6 lg:px-8 xl:px-12 overflow-auto">
        <div className={`max-w-screen-2xl mx-auto grid gap-4 grid-cols-1 transition-all duration-300 ${
          leftPanelCollapsed
            ? "lg:grid-cols-[56px_1fr]"
            : "lg:grid-cols-[420px_1fr]"
        }`}>
          {/* Left Panel - Inputs with Collapsible Sections */}
          <div className={`transition-all duration-300 ${
            leftPanelCollapsed ? "lg:w-14" : ""
          }`}>
            {/* Collapsed state */}
            {leftPanelCollapsed ? (
              <div className="hidden lg:flex flex-col items-center py-4 h-full rounded-2xl border border-slate-200 dark:border-slate-700/50 bg-white/60 dark:bg-slate-800/40 backdrop-blur-sm shadow-sm dark:shadow-none">
                <button
                  onClick={() => setLeftPanelCollapsed(false)}
                  className="w-10 h-10 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-amber-100 dark:hover:bg-amber-900/30 flex items-center justify-center transition-colors group"
                  title="Expand configuration panel"
                >
                  <svg className="w-5 h-5 text-slate-500 dark:text-slate-400 group-hover:text-amber-600 dark:group-hover:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
                <div className="mt-4 writing-mode-vertical text-xs font-medium text-slate-500 dark:text-slate-400" style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}>
                  Configuration
                </div>
              </div>
            ) : (
              <div className="rounded-2xl border border-slate-200 dark:border-slate-700/50 bg-white/60 dark:bg-slate-800/40 backdrop-blur-sm shadow-sm dark:shadow-none">
                {/* Panel header */}
                <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-700/50">
                  <div className="flex items-center gap-3">
                    <div className="w-1 h-5 bg-gradient-to-b from-amber-500 to-amber-600 rounded-full" />
                    <h2 className="font-display font-semibold text-slate-900 dark:text-white tracking-tight">Configuration</h2>
                  </div>
                  <button
                    onClick={() => setLeftPanelCollapsed(true)}
                    className="hidden lg:flex w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-amber-100 dark:hover:bg-amber-900/30 items-center justify-center transition-colors group"
                    title="Collapse panel"
                  >
                    <svg className="w-4 h-4 text-slate-500 dark:text-slate-400 group-hover:text-amber-600 dark:group-hover:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                </div>

                {/* Content */}
                <div className="p-4 space-y-3">

            {/* Sources Section */}
            <div className="rounded-xl border border-slate-200 dark:border-slate-700/50 bg-white/80 dark:bg-slate-800/50 backdrop-blur-sm overflow-hidden hover:border-slate-300 dark:hover:border-slate-600 hover:shadow-sm transition-all">
              <button
                type="button"
                onClick={() => toggleSection("sources")}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50/50 dark:hover:bg-slate-700/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-500/20 flex items-center justify-center">
                    <svg className="w-4 h-4 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  </div>
                  <div className="text-left">
                    <span className="text-sm font-medium text-slate-900 dark:text-white block">Sources</span>
                    <span className="text-[11px] text-slate-500 dark:text-slate-400">
                      {uploadedFiles.length + urls.length + (textContent.trim() ? 1 : 0)} added
                    </span>
                  </div>
                </div>
                <svg
                  className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${expandedSections.sources ? "rotate-180" : ""}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div className={`overflow-hidden transition-all duration-300 ease-out ${expandedSections.sources ? "max-h-[9999px]" : "max-h-0"}`}>
                <div className="px-4 pb-4 border-t border-slate-100 dark:border-slate-700/50">
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
              </div>
            </div>

            {/* Output Type Section */}
            <div className="rounded-xl border border-slate-200 dark:border-slate-700/50 bg-white/80 dark:bg-slate-800/50 backdrop-blur-sm overflow-hidden hover:border-slate-300 dark:hover:border-slate-600 hover:shadow-sm transition-all">
              <button
                type="button"
                onClick={() => toggleSection("outputType")}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50/50 dark:hover:bg-slate-700/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-500/20 flex items-center justify-center">
                    <svg className="w-4 h-4 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                    </svg>
                  </div>
                  <div className="text-left">
                    <span className="text-sm font-medium text-slate-900 dark:text-white block">Output Format</span>
                    <span className="text-[11px] text-slate-500 dark:text-slate-400">Choose your output type</span>
                  </div>
                </div>
                <svg
                  className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${expandedSections.outputType ? "rotate-180" : ""}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div className={`overflow-hidden transition-all duration-300 ease-out ${expandedSections.outputType ? "max-h-[9999px]" : "max-h-0"}`}>
                <div className="px-4 pb-4 border-t border-slate-100 dark:border-slate-700/50">
                  <OutputTypeSelector
                    selectedType={outputType}
                    onTypeChange={setOutputType}
                    geminiKeyAvailable={hasGeminiKey}
                    imageGenerationEnabled={enableImageGeneration}
                    podcastEnabled={provider === "gemini" ? true : (enablePodcast && podcastGeminiApiKey.trim().length > 0)}
                    onCombinedTypeChange={setCombinedOutputType}
                    selectedCombinedType={combinedOutputType}
                  />
                </div>
              </div>
            </div>

            {/* Settings/Options Section */}
            <div className="rounded-xl border border-slate-200 dark:border-slate-700/50 bg-white/80 dark:bg-slate-800/50 backdrop-blur-sm overflow-hidden hover:border-slate-300 dark:hover:border-slate-600 hover:shadow-sm transition-all">
              <button
                type="button"
                onClick={() => toggleSection("options")}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50/50 dark:hover:bg-slate-700/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-500/20 flex items-center justify-center">
                    <svg className="w-4 h-4 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </div>
                  <div className="text-left">
                    <span className="text-sm font-medium text-slate-900 dark:text-white block">Settings</span>
                    <span className="text-[11px] text-slate-500 dark:text-slate-400">Fine-tune your output</span>
                  </div>
                </div>
                <svg
                  className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${expandedSections.options ? "rotate-180" : ""}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div className={`overflow-hidden transition-all duration-300 ease-out ${expandedSections.options ? "max-h-[9999px]" : "max-h-0"}`}>
                <div className="px-4 pb-4 border-t border-slate-100 dark:border-slate-700/50">
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
                    showApiKeys={false}
                    showProviderModel={false}
                    imageGenerationAvailable={hasImageKey}
                    imagePrompt={imagePrompt}
                    imageCategory={imageCategory}
                    selectedStyleId={selectedStyleId}
                    imageOutputFormat={imageOutputFormat}
                    podcastStyle={podcastStyle}
                    podcastSpeakers={podcastSpeakers}
                    podcastDuration={podcastDuration}
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
                    onPodcastStyleChange={setPodcastStyle}
                    onPodcastSpeakersChange={setPodcastSpeakers}
                    onPodcastDurationChange={setPodcastDuration}
                  />
                </div>
              </div>
            </div>

            {/* Generate Button */}
            <div className="pt-2">
              <Button
                size="lg"
                className={`w-full h-12 text-sm font-semibold uppercase tracking-wider transition-all duration-300 ${
                  getCurrentState() === "generating"
                    ? "bg-slate-200 dark:bg-slate-700 text-slate-500 dark:text-slate-400"
                    : "bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-white shadow-lg shadow-amber-500/25 hover:shadow-amber-500/40 hover:-translate-y-0.5"
                }`}
                disabled={!canGenerate || getCurrentState() === "generating"}
                onClick={handleGenerateClick}
              >
                {getCurrentState() === "generating" ? (
                  <>
                    <div className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin mr-3" />
                    Processing...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    {hasRequiredApiKeys ? "Generate" : "Configure & Generate"}
                  </>
                )}
              </Button>
            </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Panel - Output Preview */}
          <div className="min-h-[500px] lg:h-full overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-700/50 bg-white/60 dark:bg-slate-800/40 backdrop-blur-sm shadow-sm dark:shadow-none flex flex-col">
            {/* Panel header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-700/50 flex-shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-1 h-5 bg-gradient-to-b from-amber-500 to-amber-600 rounded-full" />
                <h2 className="font-display font-semibold text-slate-900 dark:text-white tracking-tight">Preview</h2>
                {combinedOutputType && (
                  <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300">
                    Dual Output
                  </span>
                )}
              </div>
              {getCurrentState() === "generating" && (
                <div className="flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400">
                  <div className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" />
                  <span className="font-medium tracking-wide">{Math.round(getCurrentProgress())}%</span>
                </div>
              )}
            </div>
            <div className="flex-1 min-h-0 p-4">
              {isMindMap && mindMapState === "generating" ? (
                <div className="flex items-center justify-center h-full rounded-xl border border-slate-200 dark:border-slate-700/50 bg-slate-50/50 dark:bg-slate-800/50">
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
                  pdfBase64={pdfBase64}
                  markdownContent={markdownContent}
                  downloadUrl={downloadUrl}
                  mindMapTree={mindMapTree}
                  podcastResult={podcastResult}
                  faqDocument={faqResult?.document || null}
                  faqDownloadUrl={faqResult?.downloadUrl || null}
                  metadata={metadata}
                  imageData={generatedImageData}
                  imageFormat={generatedImageFormat}
                  onReset={handleReset}
                  onDownload={handleDownload}
                  userId={user?.id}
                  imageApiKey={effectiveImageKey}
                  combinedOutputType={combinedOutputType}
                  secondaryPdfBase64={secondaryPdfBase64}
                  secondaryMarkdownContent={secondaryMarkdownContent}
                  isSecondaryGenerating={isSecondaryGenerating}
                />
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
