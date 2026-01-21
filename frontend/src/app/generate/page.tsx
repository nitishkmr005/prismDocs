"use client";

import { useCallback, useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useGeneration } from "@/hooks/useGeneration";
import { useMindMapGeneration } from "@/hooks/useMindMapGeneration";
import { usePodcastGeneration } from "@/hooks/usePodcastGeneration";
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
import { MindMapProgress } from "@/components/mindmap";
import { generateImage } from "@/lib/api/image";
import { generateMindMap as generateMindMapApi } from "@/lib/api/mindmap";
import { MindMapEvent, MindMapNode, MindMapTree } from "@/lib/types/mindmap";
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

const MAX_IMAGE_PROMPT_CHARS = 3600;
const MAX_MINDMAP_OUTLINE_NODES = 30;
const MAX_MINDMAP_OUTLINE_DEPTH = 3;

function clampText(text: string, maxChars: number): string {
  if (text.length <= maxChars) return text;
  return `${text.slice(0, Math.max(0, maxChars - 3)).trimEnd()}...`;
}

function buildMindMapOutline(
  root: MindMapNode,
  maxNodes = MAX_MINDMAP_OUTLINE_NODES,
  maxDepth = MAX_MINDMAP_OUTLINE_DEPTH
): string[] {
  const lines: string[] = [];
  const queue: Array<{ node: MindMapNode; depth: number }> = [];

  if (root.children?.length) {
    for (const child of root.children) {
      queue.push({ node: child, depth: 1 });
    }
  } else {
    queue.push({ node: root, depth: 1 });
  }

  while (queue.length && lines.length < maxNodes) {
    const next = queue.shift();
    if (!next) break;
    const { node, depth } = next;
    if (!node.label) continue;
    const prefix = "  ".repeat(Math.max(0, depth - 1));
    lines.push(`${prefix}- ${node.label}`);

    if (node.children && depth < maxDepth) {
      for (const child of node.children) {
        queue.push({ node: child, depth: depth + 1 });
      }
    }
  }

  return lines;
}

function buildImagePromptFromMindMap(tree: MindMapTree, userPrompt: string): string {
  const outline = buildMindMapOutline(tree.nodes);
  const parts: string[] = [];

  parts.push("Create an image that strictly reflects the source content.");
  if (userPrompt) {
    parts.push(`User focus: ${userPrompt}`);
  }
  if (tree.title) {
    parts.push(`Title: ${tree.title}`);
  }
  if (tree.summary) {
    parts.push(`Summary: ${tree.summary}`);
  }
  if (tree.nodes?.label) {
    parts.push(`Central topic: ${tree.nodes.label}`);
  }
  if (outline.length) {
    parts.push(`Key points:\n${outline.join("\n")}`);
  }
  parts.push("Use only these points. Do not add extra concepts or labels.");

  return clampText(parts.join("\n"), MAX_IMAGE_PROMPT_CHARS);
}

export default function GeneratePage() {
  // Auth state
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);

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
  const isPodcast = outputType === "podcast";
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
    if (isImageType) {
      const needsContentKey = uploadedFiles.length > 0 || urls.length > 0;
      return hasImageKey && (!needsContentKey || hasContentKey);
    }
    return true;
  })();

  // For image types, we use the same sources (textContent) as other types
  const canGenerate = hasSources && !authLoading && isAuthenticated;

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

      // Determine the prompt: use text content, or summarize files/URLs if provided
      const userPrompt = textContent.trim();
      let prompt = userPrompt;
      
      // If we have files or URLs, we need to summarize the content first
      const hasFiles = uploadedFiles.length > 0;
      const hasUrls = urls.length > 0;
      const hasSourcesToProcess = hasFiles || hasUrls;
      
      if (hasSourcesToProcess) {
        // Use mindmap API to parse and summarize the content for image generation
        try {
          const sources = buildSources();
          
          // Use the content API key for summarization (text models)
          const apiKeyForSummarization = contentApiKey;
          if (!apiKeyForSummarization) {
            setImageGenError("Please enter a Content API key to process your files.");
            setImageGenState("error");
            return;
          }
          
          // Create a promise that resolves when we get the complete event
          const summaryPromise = new Promise<string>((resolve, reject) => {
            let summaryText = "";
            let resolved = false;
            let idleTimer: ReturnType<typeof setInterval> | null = null;
            let hardTimeout: ReturnType<typeof setTimeout> | null = null;
            const idleTimeoutMs = 120000;
            const hardTimeoutMs = 300000;
            let lastEventAt = Date.now();

            const cleanupTimers = () => {
              if (idleTimer) clearInterval(idleTimer);
              if (hardTimeout) clearTimeout(hardTimeout);
              idleTimer = null;
              hardTimeout = null;
            };
            
            const handleEvent = (event: MindMapEvent) => {
              if (resolved) return;
              lastEventAt = Date.now();
              
              console.log("MindMap event received:", JSON.stringify(event).substring(0, 500));
              
              // Check for complete event with tree (MindMapCompleteEvent has type="complete" and tree)
              if (event.type === "complete" && "tree" in event && event.tree) {
                // Build a structured prompt from the tree for better content fidelity
                const tree = event.tree;
                summaryText = buildImagePromptFromMindMap(tree, userPrompt);
                console.log("Extracted summary from tree:", summaryText.substring(0, 200));
                resolved = true;
                cleanupTimers();
                resolve(summaryText);
              } else if (event.type === "progress") {
                // Progress event - just log it
                console.log("Progress:", event.stage, event.percent);
              } else if (event.type === "error") {
                // Error event
                resolved = true;
                cleanupTimers();
                reject(new Error(event.message || "Summarization failed"));
              }
            };
            
            const handleError = (err: Error) => {
              if (resolved) return;
              resolved = true;
              cleanupTimers();
              console.error("MindMap API error:", err);
              reject(err);
            };
            
            // Call the mindmap API with summarize mode - use selected provider/model
            generateMindMapApi({
              request: {
                sources,
                mode: "summarize",
                provider: provider,  // Use user-selected provider (default: gemini)
                model: contentModel, // Use user-selected model
              },
              apiKey: apiKeyForSummarization,
              userId: user?.id,
              onEvent: handleEvent,
              onError: handleError,
            }).catch((err) => {
              if (!resolved) {
                resolved = true;
                cleanupTimers();
                reject(err);
              }
            });
            
            idleTimer = setInterval(() => {
              if (resolved) return;
              if (Date.now() - lastEventAt > idleTimeoutMs) {
                resolved = true;
                cleanupTimers();
                reject(new Error("Summarization timed out. Please try again."));
              }
            }, 5000);

            hardTimeout = setTimeout(() => {
              if (!resolved) {
                resolved = true;
                cleanupTimers();
                reject(new Error("Summarization took too long. Please try again."));
              }
            }, hardTimeoutMs);
          });
          
          const summarizedContent = await summaryPromise;
          
          // Use the structured summary as the final prompt
          if (summarizedContent) {
            prompt = summarizedContent;
          }
          
        } catch (err) {
          console.error("Failed to summarize sources for image generation:", err);
          const errorMessage = err instanceof Error ? err.message : "Unknown error";
          setImageGenError(`Failed to process your sources: ${errorMessage}`);
          setImageGenState("error");
          return;
        }
      }
      
      if (!prompt) {
        setImageGenError("Please enter a description or upload files/URLs to generate an image");
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
          effectiveImageKey
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
            max_slides: 25,
            max_summary_points: 5,
            enable_image_generation: enableImageGeneration,
          },
        },
        contentApiKey,
        enableImageGeneration ? effectiveImageKey : undefined,
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
        effectivePodcastKey,  // Use Gemini content key or separate podcast Gemini key
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
    podcastStyle,
    podcastSpeakers,
    podcastDuration,
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
    setImageGenState("idle");
    setImageGenError(null);
    setGeneratedImageData(null);
  }, [resetGeneration, resetMindMap, resetPodcast]);

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
    if (isPodcast) {
      if (podcastState === "generating") return "generating";
      if (podcastState === "error") return "error";
      if (podcastState === "complete") return "success";
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
    return generationStatus;
  };

  const getCurrentError = (): string | null => {
    if (isImageType) return imageGenError;
    if (isMindMap) return mindMapError;
    if (isPodcast) return podcastError;
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

  const keysStatusLabel = hasRequiredApiKeys ? "Keys set" : "Keys required";
  const keysActionLabel = hasRequiredApiKeys ? "Change" : "Add keys";

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 scroll-smooth">
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
            <div className={`flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${
              hasRequiredApiKeys
                ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                : "border-amber-200 bg-amber-50 text-amber-700"
            }`}>
              <span className={`h-2 w-2 rounded-full ${
                hasRequiredApiKeys ? "bg-emerald-500" : "bg-amber-500"
              }`} />
              <span>{keysStatusLabel}</span>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-[11px]"
                onClick={() => setShowApiKeyModal(true)}
              >
                {keysActionLabel}
              </Button>
            </div>
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

      {/* Main Studio Layout - Responsive with stacked mobile, side-by-side desktop */}
      <main className="min-h-[calc(100vh-4rem)] lg:h-[calc(100vh-4rem)] px-4 py-4 lg:px-12 xl:px-20 overflow-x-hidden overflow-y-auto lg:overflow-hidden">
        <div className="h-full max-w-screen-2xl mx-auto grid gap-4 grid-cols-1 lg:grid-cols-2 items-start">
          {/* Left Panel - Inputs with Collapsible Sections */}
          <div className="lg:h-full border border-border/30 rounded-2xl bg-white/60 dark:bg-slate-900/60 lg:overflow-y-auto lg:scroll-smooth p-2 space-y-2">
            {/* Sources Section */}
            <div className="rounded-xl border border-border/50 bg-card/80 backdrop-blur-sm shadow-sm overflow-hidden">
              <button
                type="button"
                onClick={() => toggleSection("sources")}
                className="w-full flex items-center justify-between px-3 py-2 hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  <span className="text-sm font-medium">Sources</span>
                  <span className="text-xs text-muted-foreground">
                    ({uploadedFiles.length + urls.length + (textContent.trim() ? 1 : 0)})
                  </span>
                </div>
                <svg
                  className={`w-4 h-4 text-muted-foreground transition-transform ${expandedSections.sources ? "rotate-180" : ""}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div className={`overflow-hidden transition-all duration-200 ${expandedSections.sources ? "max-h-[9999px]" : "max-h-0"}`}>
                <div className="px-3 pb-3">
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
            <div className="rounded-xl border border-border/50 bg-card/80 backdrop-blur-sm shadow-sm overflow-hidden">
              <button
                type="button"
                onClick={() => toggleSection("outputType")}
                className="w-full flex items-center justify-between px-3 py-2 hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                  </svg>
                  <span className="text-sm font-medium">Output Type</span>
                </div>
                <svg
                  className={`w-4 h-4 text-muted-foreground transition-transform ${expandedSections.outputType ? "rotate-180" : ""}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div className={`overflow-hidden transition-all duration-200 ${expandedSections.outputType ? "max-h-[9999px]" : "max-h-0"}`}>
                <div className="px-3 pb-3">
                  <OutputTypeSelector
                    selectedType={outputType}
                    onTypeChange={setOutputType}
                    geminiKeyAvailable={hasGeminiKey}
                    imageGenerationEnabled={enableImageGeneration}
                    podcastEnabled={provider === "gemini" ? true : (enablePodcast && podcastGeminiApiKey.trim().length > 0)}
                  />
                </div>
              </div>
            </div>

            {/* Settings/Options Section */}
            <div className="rounded-xl border border-border/50 bg-card/80 backdrop-blur-sm shadow-sm overflow-hidden">
              <button
                type="button"
                onClick={() => toggleSection("options")}
                className="w-full flex items-center justify-between px-3 py-2 hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span className="text-sm font-medium">Settings</span>
                </div>
                <svg
                  className={`w-4 h-4 text-muted-foreground transition-transform ${expandedSections.options ? "rotate-180" : ""}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div className={`overflow-hidden transition-all duration-200 ${expandedSections.options ? "max-h-[9999px]" : "max-h-0"}`}>
                <div className="px-3 pb-3">
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

            {/* Spacer to prevent content from being hidden behind sticky button */}
            <div className="h-16" />

            {/* Generate Button - Now sticky at bottom */}
            <div className="sticky bottom-0 pt-2 pb-1 bg-gradient-to-t from-white/90 dark:from-slate-900/90 via-white/80 dark:via-slate-900/80 to-transparent">
              <Button
                size="lg"
                className="w-full h-11 text-base font-semibold shadow-lg hover:shadow-xl transition-all bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700"
                disabled={!canGenerate || getCurrentState() === "generating"}
                onClick={handleGenerateClick}
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
                    {hasRequiredApiKeys ? "Generate" : "Configure & Generate"}
                  </>
                )}
              </Button>
            </div>
          </div>


          {/* Right Panel - Output (responsive height) */}
          <div className="min-h-[400px] lg:h-full overflow-hidden p-4 rounded-2xl border border-border/30 bg-white/60 dark:bg-slate-900/60">
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
                  pdfBase64={pdfBase64}
                  markdownContent={markdownContent}
                  downloadUrl={downloadUrl}
                  mindMapTree={mindMapTree}
                  podcastResult={podcastResult}
                  metadata={metadata}
                  imageData={generatedImageData}
                  imageFormat={generatedImageFormat}
                  onReset={handleReset}
                  onDownload={handleDownload}
                  userId={user?.id}
                  imageApiKey={effectiveImageKey}
                />
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
