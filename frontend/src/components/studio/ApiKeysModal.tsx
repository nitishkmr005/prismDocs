"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Provider } from "@/lib/types/requests";
import { contentModelOptions } from "./DynamicOptions";

const PROVIDER_LABELS: Record<Provider, string> = {
  gemini: "Gemini",
  google: "Gemini",
  openai: "OpenAI",
  anthropic: "Anthropic",
};

const PROVIDER_KEY_URLS: Record<Provider, string> = {
  gemini: "https://aistudio.google.com/apikey",
  google: "https://aistudio.google.com/apikey",
  openai: "https://platform.openai.com/api-keys",
  anthropic: "https://console.anthropic.com/settings/keys",
};

interface ApiKeysModalProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  provider: Provider;
  contentModel: string;
  onProviderChange: (provider: Provider) => void;
  onContentModelChange: (model: string) => void;
  contentApiKey: string;
  onContentApiKeyChange: (key: string) => void;
  enableImageGeneration: boolean;
  onEnableImageGenerationChange: (enabled: boolean) => void;
  allowImageGenerationToggle: boolean;
  requireImageKey: boolean;
  imageApiKey: string;
  onImageApiKeyChange: (key: string) => void;
  canClose: boolean;
}

export function ApiKeysModal({
  isOpen,
  onOpenChange,
  provider,
  contentModel,
  onProviderChange,
  onContentModelChange,
  contentApiKey,
  onContentApiKeyChange,
  enableImageGeneration,
  onEnableImageGenerationChange,
  allowImageGenerationToggle,
  requireImageKey,
  imageApiKey,
  onImageApiKeyChange,
  canClose,
}: ApiKeysModalProps) {
  const providerLabel = PROVIDER_LABELS[provider];
  const keyUrl = PROVIDER_KEY_URLS[provider];

  const handleOpenChange = (open: boolean) => {
    if (!open && !canClose) return;
    onOpenChange(open);
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[560px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
            </svg>
            Configure API Keys
          </DialogTitle>
          <DialogDescription>
            Set up your API keys once - they'll be used for all generation types.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-2">
          {/* Content API Section */}
          <div className="space-y-3 p-4 rounded-xl border border-border/60 bg-gradient-to-br from-violet-50/50 to-fuchsia-50/30 dark:from-violet-950/30 dark:to-fuchsia-950/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  contentApiKey ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/50 dark:text-emerald-400" : "bg-primary/10 text-primary"
                }`}>
                  {contentApiKey ? (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : "1"}
                </div>
                <span className="font-medium text-sm">Content Generation</span>
              </div>
              {contentApiKey && (
                <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">Key set ✓</span>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label htmlFor="api-provider" className="text-xs font-medium">
                  Provider
                </Label>
                <Select
                  value={provider}
                  onValueChange={(value) => onProviderChange(value as Provider)}
                >
                  <SelectTrigger id="api-provider" className="h-9 text-xs bg-white/80 dark:bg-slate-900/80">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gemini">Google Gemini</SelectItem>
                    <SelectItem value="openai">OpenAI</SelectItem>
                    <SelectItem value="anthropic">Anthropic</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1">
                <Label htmlFor="api-model" className="text-xs font-medium">
                  Model
                </Label>
                <Select value={contentModel} onValueChange={onContentModelChange}>
                  <SelectTrigger id="api-model" className="h-9 text-xs bg-white/80 dark:bg-slate-900/80">
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

            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <Label htmlFor="content-api-key" className="text-xs font-medium">
                  {providerLabel} API Key <span className="text-red-500">*</span>
                </Label>
                <a
                  href={keyUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[10px] text-primary hover:underline flex items-center gap-0.5"
                >
                  Get {providerLabel} Key
                  <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              </div>
              <Input
                id="content-api-key"
                type="password"
                placeholder={`Enter ${providerLabel} API key`}
                value={contentApiKey}
                onChange={(e) => onContentApiKeyChange(e.target.value)}
                autoComplete="off"
                className="bg-white/80 dark:bg-slate-900/80"
              />
            </div>
          </div>

          {/* Image API Section - Always visible with option to use same key for Gemini */}
          <div className="space-y-3 p-4 rounded-xl border transition-all border-border/60 bg-gradient-to-br from-amber-50/50 to-orange-50/30 dark:from-amber-950/30 dark:to-orange-950/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  imageApiKey || (provider === "gemini" && contentApiKey) 
                    ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/50 dark:text-emerald-400" 
                    : "bg-amber-100 text-amber-600 dark:bg-amber-900/50 dark:text-amber-400"
                }`}>
                  {imageApiKey || (provider === "gemini" && contentApiKey) ? (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : "2"}
                </div>
                <span className="font-medium text-sm">Image Generation</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300">
                  Gemini Only
                </span>
              </div>
              {(imageApiKey || (provider === "gemini" && contentApiKey)) && (
                <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                  {provider === "gemini" && contentApiKey && !imageApiKey ? "Using content key ✓" : "Key set ✓"}
                </span>
              )}
            </div>

            {allowImageGenerationToggle && (
              <div className="flex items-start gap-2 rounded-lg border border-border/30 bg-white/50 dark:bg-slate-900/50 p-2.5">
                <Checkbox
                  id="enable-image-generation"
                  checked={enableImageGeneration}
                  onCheckedChange={(checked: boolean) => onEnableImageGenerationChange(checked)}
                />
                <div className="space-y-0.5">
                  <Label htmlFor="enable-image-generation" className="text-xs font-medium cursor-pointer">
                    Enable AI images in documents
                  </Label>
                  <p className="text-[10px] text-muted-foreground">
                    Auto-generate relevant images for your content
                  </p>
                </div>
              </div>
            )}

            {/* Gemini same-key option */}
            {provider === "gemini" && contentApiKey && (
              <div className="flex items-center gap-2 rounded-lg border border-emerald-200/50 dark:border-emerald-800/50 bg-emerald-50/50 dark:bg-emerald-950/30 p-2.5">
                <svg className="w-4 h-4 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <p className="text-xs text-emerald-700 dark:text-emerald-300">
                  Your Gemini content key will be used for image generation automatically.
                </p>
              </div>
            )}

            {/* Show image key input only if not using Gemini or want to override */}
            {(provider !== "gemini" || !contentApiKey) && (
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <Label htmlFor="image-api-key" className="text-xs font-medium">
                    Gemini Image API Key {requireImageKey && <span className="text-red-500">*</span>}
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
                  autoComplete="off"
                  className="bg-white/80 dark:bg-slate-900/80"
                />
                <p className="text-[10px] text-muted-foreground">
                  {provider !== "gemini" 
                    ? "Image generation requires a separate Gemini API key" 
                    : "Enter a key, or add a content key above to use it for images too"}
                </p>
              </div>
            )}

            {/* No image key warning - only if no key available */}
            {!imageApiKey && !(provider === "gemini" && contentApiKey) && (
              <p className="text-[10px] text-muted-foreground">
                Without an image key, image generation tasks will be disabled.
              </p>
            )}
          </div>
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2 sm:gap-3">
          <div className="flex-1 text-xs text-muted-foreground">
            {!canClose && (
              <span className="text-amber-600 dark:text-amber-400">
                ⚠ Content API key is required to continue
              </span>
            )}
          </div>
          <Button 
            onClick={() => onOpenChange(false)} 
            disabled={!canClose}
            className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700"
          >
            {canClose ? "Start Generating" : "Enter API Key"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
