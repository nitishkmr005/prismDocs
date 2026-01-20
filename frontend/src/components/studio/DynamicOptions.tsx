"use client";

import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { StudioOutputType } from "./OutputTypeSelector";
import { Provider, Audience, ImageStyle } from "@/lib/types/requests";
import { MindMapMode } from "@/lib/types/mindmap";
import { CATEGORIES, getStylesByCategory, StyleCategory } from "@/data/imageStyles";

interface ModelOption {
  value: string;
  label: string;
}

const contentModelOptions: Record<Provider, ModelOption[]> = {
  gemini: [
    { value: "gemini-2.5-flash", label: "gemini-2.5-flash" },
    { value: "gemini-2.5-flash-lite", label: "gemini-2.5-flash-lite" },
    { value: "gemini-2.5-pro", label: "gemini-2.5-pro" },
    { value: "gemini-3-flash-preview", label: "gemini-3-flash-preview" },
    { value: "gemini-3-pro-preview", label: "gemini-3-pro-preview" },
  ],
  openai: [
    { value: "gpt-4.1-mini", label: "gpt-4.1-mini" },
    { value: "gpt-4.1", label: "gpt-4.1" },
    { value: "gpt-5-mini", label: "gpt-5-mini" },
    { value: "gpt-5.2", label: "gpt-5.2" },
  ],
  anthropic: [
    { value: "claude-haiku-4-5-20251001", label: "claude-haiku-4-5-20251001" },
    { value: "claude-sonnet-4-5-20250929", label: "claude-sonnet-4-5-20250929" },
  ],
  google: [
    { value: "gemini-2.5-flash", label: "gemini-2.5-flash" },
    { value: "gemini-2.5-flash-lite", label: "gemini-2.5-flash-lite" },
    { value: "gemini-2.5-pro", label: "gemini-2.5-pro" },
    { value: "gemini-3-flash-preview", label: "gemini-3-flash-preview" },
    { value: "gemini-3-pro-preview", label: "gemini-3-pro-preview" },
  ],
};

const imageModelOptions: ModelOption[] = [
  { value: "gemini-3-pro-image-preview", label: "gemini-3-pro-image-preview" },
  { value: "gemini-2.5-flash-image", label: "gemini-2.5-flash-image" },
];

// Audience options with icons
const audienceOptions: { value: Audience; label: string; icon: string }[] = [
  { value: "technical", label: "Technical", icon: "💻" },
  { value: "executive", label: "Executive", icon: "👔" },
  { value: "client", label: "Client", icon: "🤝" },
  { value: "educational", label: "Educational", icon: "📚" },
  { value: "creator", label: "Creator", icon: "🎨" },
];

// Mind map mode options with descriptions and use cases
const mindMapModeOptions: {
  value: MindMapMode;
  label: string;
  icon: string;
  description: string;
  useCases: string[];
}[] = [
  {
    value: "summarize",
    label: "Understand Fast",
    icon: "📖",
    description: "Turn PDFs, articles, or URLs into a clean map of key ideas",
    useCases: ["Research papers", "Articles"],
  },
  {
    value: "brainstorm",
    label: "Brainstorm Ideas",
    icon: "💡",
    description: "Expand a topic into use cases, variations & possibilities",
    useCases: ["Startup ideas", "Features"],
  },
  {
    value: "goal_planning",
    label: "Create Action Plan",
    icon: "🎯",
    description: "Turn an idea into phases, steps & milestones",
    useCases: ["Projects", "Learning paths"],
  },
  {
    value: "pros_cons",
    label: "Analyze Pros & Cons",
    icon: "⚖️",
    description: "See tradeoffs, benefits & risks for better decisions",
    useCases: ["Tech choices", "Decisions"],
  },
  {
    value: "presentation_structure",
    label: "Presentation Outline",
    icon: "📊",
    description: "Create logical structure for slides or documents",
    useCases: ["Slides", "Articles"],
  },
  {
    value: "structure",
    label: "Document Structure",
    icon: "📋",
    description: "Visualize how a document is organized",
    useCases: ["Documents", "Reports"],
  },
];

interface DynamicOptionsProps {
  outputType: StudioOutputType;
  provider: Provider;
  contentModel: string;
  imageModel: string;
  audience: Audience;
  imageStyle: ImageStyle;
  mindMapMode: MindMapMode;
  enableImageGeneration: boolean;
  contentApiKey: string;
  imageApiKey: string;
  showApiKeys?: boolean;
  showProviderModel?: boolean;
  imageGenerationAvailable?: boolean;
  // Image generation specific
  imagePrompt?: string;
  imageCategory?: StyleCategory | null;
  selectedStyleId?: string | null;
  imageOutputFormat?: "raster" | "svg";
  onProviderChange: (provider: Provider) => void;
  onContentModelChange: (model: string) => void;
  onImageModelChange: (model: string) => void;
  onAudienceChange: (audience: Audience) => void;
  onImageStyleChange: (style: ImageStyle) => void;
  onMindMapModeChange: (mode: MindMapMode) => void;
  onEnableImageGenerationChange: (enabled: boolean) => void;
  onContentApiKeyChange: (key: string) => void;
  onImageApiKeyChange: (key: string) => void;
  // Image generation callbacks
  onImagePromptChange?: (prompt: string) => void;
  onImageCategoryChange?: (category: StyleCategory | null) => void;
  onSelectedStyleIdChange?: (styleId: string | null) => void;
  onImageOutputFormatChange?: (format: "raster" | "svg") => void;
}

export function DynamicOptions({
  outputType,
  provider,
  contentModel,
  imageModel,
  audience,
  imageStyle,
  mindMapMode,
  enableImageGeneration,
  contentApiKey,
  imageApiKey,
  showApiKeys = true,
  showProviderModel = true,
  imageGenerationAvailable = true,
  imagePrompt,
  imageCategory,
  selectedStyleId,
  imageOutputFormat,
  onProviderChange,
  onContentModelChange,
  onImageModelChange,
  onAudienceChange,
  onImageStyleChange,
  onMindMapModeChange,
  onEnableImageGenerationChange,
  onContentApiKeyChange,
  onImageApiKeyChange,
  onImagePromptChange,
  onImageCategoryChange,
  onSelectedStyleIdChange,
  onImageOutputFormatChange,
}: DynamicOptionsProps) {
  const isContentType = ["article_pdf", "article_markdown", "slide_deck_pdf", "presentation_pptx"].includes(outputType);
  const isImageType = outputType === "image_generate";
  const isMindMap = outputType === "mindmap";
  const isImageGenLocked = isContentType && !imageGenerationAvailable;

  // Determine which API key sections to show
  // Content API key is always shown at top since it's needed for processing/parsing
  const showContentApiKey = true;  // Always show content key at top
  const showImageApiKey = isImageType || (isContentType && enableImageGeneration);

  // Get styles for selected category
  const availableStyles = imageCategory ? getStylesByCategory(imageCategory) : [];
  const isFreeTextMode = !imageCategory;

  return (
    <div className="space-y-4">
      {/* API Keys Section */}
      {showApiKeys && (
        <div className="space-y-3 p-3 rounded-lg bg-muted/30 border border-border/50">
          <Label className="text-sm font-semibold flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
            </svg>
            API Keys
          </Label>

          {showContentApiKey && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="content-api-key" className="text-xs">
                  Content API Key *
                </Label>
                {provider === "gemini" && (
                  <a
                    href="https://aistudio.google.com/apikey"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[10px] text-primary hover:underline flex items-center gap-0.5"
                  >
                    Get Key
                    <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                )}
                {provider === "openai" && (
                  <a
                    href="https://platform.openai.com/api-keys"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[10px] text-primary hover:underline flex items-center gap-0.5"
                  >
                    Get Key
                    <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                )}
                {provider === "anthropic" && (
                  <a
                    href="https://console.anthropic.com/settings/keys"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[10px] text-primary hover:underline flex items-center gap-0.5"
                  >
                    Get Key
                    <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                )}
              </div>
              <Input
                id="content-api-key"
                type="password"
                placeholder={`Enter ${provider === "gemini" ? "Gemini" : provider === "openai" ? "OpenAI" : "Claude"} API key`}
                value={contentApiKey}
                onChange={(e) => onContentApiKeyChange(e.target.value)}
                className="h-8 text-xs"
                autoComplete="off"
              />
            </div>
          )}

          {showImageApiKey && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="image-api-key" className="text-xs">
                  Image API Key {isContentType ? "(for images)" : ""} *
                </Label>
                <a
                  href="https://aistudio.google.com/apikey"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[10px] text-primary hover:underline flex items-center gap-0.5"
                >
                  Get Gemini Key
                  <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              </div>
              <Input
                id="image-api-key"
                type="password"
                placeholder="Enter Gemini API key for images"
                value={imageApiKey}
                onChange={(e) => onImageApiKeyChange(e.target.value)}
                className="h-8 text-xs"
                autoComplete="off"
              />
            </div>
          )}
        </div>
      )}

      {/* Provider & Model Selection - for content types, mind map, AND image generation */}
      {showProviderModel && (isContentType || isMindMap || isImageType) && (
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="provider" className="text-xs">Provider</Label>
            <Select value={provider} onValueChange={(v) => onProviderChange(v as Provider)}>
              <SelectTrigger id="provider" className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gemini">Google Gemini</SelectItem>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="anthropic">Anthropic</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="content-model" className="text-xs">Model</Label>
            <Select value={contentModel} onValueChange={onContentModelChange}>
              <SelectTrigger id="content-model" className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(contentModelOptions[provider] || []).map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      )}

      {/* Target Audience - TILES for content types */}
      {isContentType && (
        <div className="space-y-2">
          <Label className="text-xs font-medium">Target Audience</Label>
          <div className="grid grid-cols-5 gap-1.5">
            {audienceOptions.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => onAudienceChange(opt.value)}
                className={`flex flex-col items-center gap-1 p-2 rounded-lg border text-center transition-all ${
                  audience === opt.value
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border hover:border-primary/50 hover:bg-muted/50"
                }`}
              >
                <span className="text-lg">{opt.icon}</span>
                <span className="text-[10px] font-medium leading-tight">{opt.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Image Generation Toggle - for content types */}
      {isContentType && (
        <div className="space-y-2">
          <div className="flex items-center space-x-2 py-1">
          <Checkbox
            id="enable-images"
            checked={enableImageGeneration}
            onCheckedChange={(checked: boolean) => onEnableImageGenerationChange(checked)}
            disabled={isImageGenLocked}
          />
          <Label
            htmlFor="enable-images"
            className={`text-xs cursor-pointer ${isImageGenLocked ? "text-muted-foreground" : ""}`}
          >
            Enable image generation in document
          </Label>
          </div>
          {isImageGenLocked && (
            <p className="text-xs text-muted-foreground">
              Add a Gemini image API key to unlock image generation.
            </p>
          )}
        </div>
      )}

      {/* Image Style - for content with images enabled (NOT for standalone image generation) */}
      {isContentType && enableImageGeneration && (
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="image-style" className="text-xs">Image Style</Label>
            <Select value={imageStyle} onValueChange={(v) => onImageStyleChange(v as ImageStyle)}>
              <SelectTrigger id="image-style" className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="auto">Auto</SelectItem>
                <SelectItem value="infographic">Infographic</SelectItem>
                <SelectItem value="minimalist">Minimalist</SelectItem>
                <SelectItem value="corporate">Corporate</SelectItem>
                <SelectItem value="educational">Educational</SelectItem>
                <SelectItem value="diagram">Diagram</SelectItem>
                <SelectItem value="handwritten">Handwritten</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      )}

      {/* Mind Map Mode - Rich cards for mindmap type */}
      {isMindMap && (
        <div className="space-y-3">
          <div className="space-y-1">
            <Label className="text-sm font-semibold">Generation Mode</Label>
            <p className="text-xs text-muted-foreground">Choose how you want to transform your content</p>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {mindMapModeOptions.map((opt) => {
              const isSelected = mindMapMode === opt.value;
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => onMindMapModeChange(opt.value)}
                  className={`flex flex-col items-start gap-2 p-4 rounded-xl border-2 text-left transition-all ${
                    isSelected
                      ? "border-blue-400 bg-blue-50 dark:bg-blue-950/30"
                      : "border-border hover:border-muted-foreground/40 hover:bg-muted/30"
                  }`}
                >
                  <div className="w-10 h-10 rounded-lg bg-muted/50 flex items-center justify-center">
                    <span className="text-xl">{opt.icon}</span>
                  </div>
                  <div className="space-y-1">
                    <h4 className={`text-sm font-semibold ${isSelected ? "text-blue-600 dark:text-blue-400" : ""}`}>
                      {opt.label}
                    </h4>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {opt.description}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-auto">
                    {opt.useCases.map((useCase, i) => (
                      <span
                        key={i}
                        className="text-[10px] px-2 py-0.5 rounded-full bg-muted text-muted-foreground"
                      >
                        {useCase}
                      </span>
                    ))}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Image Generation Options - for image types */}
      {isImageType && (
        <div className="space-y-5">
          <div className="space-y-1">
            <div className="text-sm font-semibold">Image settings</div>
            <p className="text-xs text-muted-foreground">
              Use the Sources panel for your prompt or uploads. Choose a style here.
            </p>
          </div>

          <div className="space-y-2">
            <Label className="text-xs font-medium">Style mode</Label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => {
                  onImageCategoryChange?.(null);
                  onSelectedStyleIdChange?.(null);
                }}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  isFreeTextMode
                    ? "bg-foreground text-background"
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                }`}
              >
                Free text
              </button>
              <button
                type="button"
                onClick={() => {
                  if (imageCategory) return;
                  const nextCategory = CATEGORIES[0]?.id || null;
                  onImageCategoryChange?.(nextCategory);
                  onSelectedStyleIdChange?.(null);
                }}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  !isFreeTextMode
                    ? "bg-foreground text-background"
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                }`}
              >
                Style guided
              </button>
            </div>
            <p className="text-xs text-muted-foreground">
              Free text uses your prompt only. Style guided adds a visual template.
            </p>
          </div>

          {/* Style Category - 4x2 grid with icons */}
          {!isFreeTextMode && (
            <div className="space-y-2">
              <Label className="text-sm font-medium">Style category</Label>
              <div className="grid grid-cols-4 gap-2">
                {CATEGORIES.map((cat) => {
                  const icons: Record<StyleCategory, string> = {
                    handwritten_and_human: "✍️",
                    diagram_and_architecture: "🏗️",
                    developer_and_technical: "💻",
                    teaching_and_presentation: "📊",
                    research_and_academic: "🔬",
                    creative_and_social: "🎨",
                    product_and_business: "💼",
                    comparison_and_table: "📋",
                  };
                  const shortNames: Record<StyleCategory, string> = {
                    handwritten_and_human: "Handwritten",
                    diagram_and_architecture: "Diagram",
                    developer_and_technical: "Developer",
                    teaching_and_presentation: "Teaching",
                    research_and_academic: "Research",
                    creative_and_social: "Creative",
                    product_and_business: "Product",
                    comparison_and_table: "Comparison",
                  };
                  const isSelected = imageCategory === cat.id;
                  return (
                    <button
                      key={cat.id}
                      type="button"
                      onClick={() => {
                        onImageCategoryChange?.(cat.id);
                        onSelectedStyleIdChange?.(null);
                      }}
                      className={`relative flex flex-col items-center gap-1.5 p-3 rounded-xl border-2 transition-all ${
                        isSelected
                          ? "border-amber-400 bg-amber-50 dark:bg-amber-950/30"
                          : "border-border hover:border-muted-foreground/40 hover:bg-muted/30"
                      }`}
                    >
                      {isSelected && (
                        <div className="absolute top-1 right-1">
                          <svg className="w-4 h-4 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        </div>
                      )}
                      <span className="text-xl">{icons[cat.id]}</span>
                      <span className={`text-xs font-medium ${isSelected ? "text-amber-600 dark:text-amber-400" : "text-muted-foreground"}`}>
                        {shortNames[cat.id]}
                      </span>
                    </button>
                  );
                })}
              </div>
              <p className="text-xs text-muted-foreground">
                Pick a category to browse styles for that visual direction.
              </p>
            </div>
          )}

          {/* Style Dropdown */}
          {imageCategory && availableStyles.length > 0 && (
            <div className="space-y-2">
              <Label className="text-sm font-medium">Style</Label>
              <Select
                value={selectedStyleId || "none"}
                onValueChange={(v) => onSelectedStyleIdChange?.(v === "none" ? null : v)}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a style..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Select a style...</SelectItem>
                  {availableStyles.map((style) => (
                    <SelectItem key={style.id} value={style.id}>
                      <div className="flex items-center gap-2">
                        <span>{style.name}</span>
                        {style.supportsSvg && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-300">
                            SVG
                          </span>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Style Preview Card */}
          {selectedStyleId && availableStyles.length > 0 && (() => {
            const style = availableStyles.find(s => s.id === selectedStyleId);
            if (!style) return null;
            return (
              <div className="p-4 rounded-xl border bg-card space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-base">{style.name}</h4>
                  <span className="text-xs px-2 py-1 rounded-full bg-muted text-muted-foreground">
                    {CATEGORIES.find(c => c.id === imageCategory)?.name}
                  </span>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Looks like</p>
                  <p className="text-sm">{style.looksLike}</p>
                </div>
                <div className="space-y-1.5">
                  <p className="text-xs text-muted-foreground">Best for</p>
                  <div className="flex flex-wrap gap-1.5">
                    {style.useCases.map((useCase, i) => (
                      <span key={i} className="text-xs px-2 py-1 rounded-full bg-muted text-foreground">
                        {useCase}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            );
          })()}

          {/* Output Format Toggle */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Output Format</Label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => onImageOutputFormatChange?.("raster")}
                className={`flex-1 px-4 py-2.5 rounded-lg font-medium text-sm transition-all ${
                  imageOutputFormat === "raster"
                    ? "bg-foreground text-background"
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                }`}
              >
                Raster (PNG)
              </button>
              <button
                type="button"
                onClick={() => onImageOutputFormatChange?.("svg")}
                className={`flex-1 px-4 py-2.5 rounded-lg font-medium text-sm transition-all ${
                  imageOutputFormat === "svg"
                    ? "bg-foreground text-background"
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                }`}
              >
                SVG
              </button>
            </div>
            <p className="text-xs text-muted-foreground">
              SVG is only available for technical diagram styles or free text mode.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export { contentModelOptions, imageModelOptions };
