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

// Mind map mode options
const mindMapModeOptions: { value: MindMapMode; label: string; icon: string }[] = [
  { value: "summarize", label: "Summarize", icon: "📝" },
  { value: "brainstorm", label: "Brainstorm", icon: "💡" },
  { value: "structure", label: "Structure", icon: "🏗️" },
  { value: "goal_planning", label: "Goals", icon: "🎯" },
  { value: "pros_cons", label: "Pros & Cons", icon: "⚖️" },
  { value: "presentation_structure", label: "Presentation", icon: "📊" },
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

  // Determine which API key sections to show
  const showContentApiKey = isContentType || isMindMap;
  const showImageApiKey = isImageType || (isContentType && enableImageGeneration);

  // Get styles for selected category
  const availableStyles = imageCategory ? getStylesByCategory(imageCategory) : [];

  return (
    <div className="space-y-4">
      {/* API Keys Section */}
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

      {/* Provider & Model Selection - for content types */}
      {(isContentType || isMindMap) && (
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
        <div className="flex items-center space-x-2 py-1">
          <Checkbox
            id="enable-images"
            checked={enableImageGeneration}
            onCheckedChange={(checked: boolean) => onEnableImageGenerationChange(checked)}
          />
          <Label htmlFor="enable-images" className="text-xs cursor-pointer">
            Enable image generation in document
          </Label>
        </div>
      )}

      {/* Image Style & Model - for content with images enabled (NOT for standalone image generation) */}
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

          <div className="space-y-1.5">
            <Label htmlFor="image-model" className="text-xs">Image Model</Label>
            <Select value={imageModel} onValueChange={onImageModelChange}>
              <SelectTrigger id="image-model" className="h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {imageModelOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      )}

      {/* Mind Map Mode - TILES for mindmap type */}
      {isMindMap && (
        <div className="space-y-2">
          <Label className="text-xs font-medium">Mind Map Mode</Label>
          <div className="grid grid-cols-3 gap-1.5">
            {mindMapModeOptions.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => onMindMapModeChange(opt.value)}
                className={`flex flex-col items-center gap-1 p-2.5 rounded-lg border text-center transition-all ${
                  mindMapMode === opt.value
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

      {/* Image Generation Options - for image types */}
      {isImageType && (
        <div className="space-y-5">

          {/* Style Category - Clean wide tiles */}
          <div className="space-y-2.5">
            <Label className="text-sm font-medium text-muted-foreground">Style Category</Label>
            <div className="grid grid-cols-2 gap-2">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => {
                    onImageCategoryChange?.(cat.id);
                    onSelectedStyleIdChange?.(null);
                  }}
                  className={`px-4 py-3 rounded-xl border text-left transition-all ${
                    imageCategory === cat.id
                      ? "border-primary/60 bg-primary/5 text-foreground shadow-sm"
                      : "border-border/60 bg-background hover:bg-muted/30 text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <span className="text-sm font-medium">{cat.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Specific Style - Clean tiles (only when category is selected) */}
          {imageCategory && availableStyles.length > 0 && (
            <div className="space-y-2.5">
              <Label className="text-sm font-medium text-muted-foreground">Style</Label>
              <div className="grid grid-cols-2 gap-2">
                {availableStyles.map((style) => (
                  <button
                    key={style.id}
                    type="button"
                    onClick={() => onSelectedStyleIdChange?.(style.id)}
                    className={`px-4 py-3 rounded-xl border text-left transition-all ${
                      selectedStyleId === style.id
                        ? "border-primary/60 bg-primary/5 text-foreground shadow-sm"
                        : "border-border/60 bg-background hover:bg-muted/30 text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <span className="text-sm font-medium">{style.name}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Output Format - Clean tile buttons */}
          <div className="space-y-2.5">
            <Label className="text-sm font-medium text-muted-foreground">Output Format</Label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => onImageOutputFormatChange?.("raster")}
                className={`flex items-center justify-center gap-2.5 px-4 py-3.5 rounded-xl border transition-all ${
                  imageOutputFormat === "raster"
                    ? "border-primary/60 bg-primary/5 text-foreground shadow-sm"
                    : "border-border/60 bg-background hover:bg-muted/30 text-muted-foreground hover:text-foreground"
                }`}
              >
                <span className="text-base">🖼️</span>
                <span className="text-sm font-medium">PNG (Raster)</span>
              </button>
              <button
                type="button"
                onClick={() => onImageOutputFormatChange?.("svg")}
                className={`flex items-center justify-center gap-2.5 px-4 py-3.5 rounded-xl border transition-all ${
                  imageOutputFormat === "svg"
                    ? "border-primary/60 bg-primary/5 text-foreground shadow-sm"
                    : "border-border/60 bg-background hover:bg-muted/30 text-muted-foreground hover:text-foreground"
                }`}
              >
                <span className="text-base">📐</span>
                <span className="text-sm font-medium">SVG (Vector)</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export { contentModelOptions, imageModelOptions };
