"use client";

import { useState, useCallback, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import {
  OutputFormat,
  Provider,
  Audience,
  ImageStyle,
  SourceItem,
} from "@/lib/types/requests";
import { useUpload, UploadedFile } from "@/hooks/useUpload";

interface OutputOption {
  value: OutputFormat;
  label: string;
}

interface ModelOption {
  value: string;
  label: string;
}

interface GenerateFormProps {
  onSubmit: (
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
  ) => void;
  isGenerating?: boolean;
  defaultOutputFormat?: OutputFormat;
  outputOptions?: OutputOption[];
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
    {
      value: "anthropic.claude-haiku-4-5-20251001-v1:0",
      label: "anthropic.claude-haiku-4-5-20251001-v1:0",
    },
    {
      value: "anthropic.claude-sonnet-4-5-20250929-v1:0",
      label: "anthropic.claude-sonnet-4-5-20250929-v1:0",
    },
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

const defaultOutputOptions: OutputOption[] = [
  { value: "pdf", label: "PDF Document" },
  { value: "pptx", label: "PowerPoint Presentation" },
];

export function GenerateForm({
  onSubmit,
  isGenerating = false,
  defaultOutputFormat = "pdf",
  outputOptions = defaultOutputOptions,
}: GenerateFormProps) {
  const [sourceTab, setSourceTab] = useState<"upload" | "url" | "text">("url");
  const [urlInput, setUrlInput] = useState("");
  const [urls, setUrls] = useState<string[]>([]);
  const [textContent, setTextContent] = useState("");
  const { uploading, uploadedFiles, error: uploadError, uploadFiles, removeFile } = useUpload();

  const [outputFormat, setOutputFormat] = useState<OutputFormat>(defaultOutputFormat);
  const [provider, setProvider] = useState<Provider>("gemini");
  const [contentModel, setContentModel] = useState<string>("gemini-2.5-flash");
  const [imageModel, setImageModel] = useState<string>("gemini-3-pro-image-preview");
  const [audience, setAudience] = useState<Audience>("technical");
  const [imageStyle, setImageStyle] = useState<ImageStyle>("auto");
  const [enableImageGeneration, setEnableImageGeneration] = useState(false);
  const [contentApiKey, setContentApiKey] = useState("");
  const [imageApiKey, setImageApiKey] = useState("");

  useEffect(() => {
    const options = contentModelOptions[provider] || [];
    if (!options.length) {
      return;
    }
    if (!options.some((option) => option.value === contentModel)) {
      const defaultByProvider: Partial<Record<Provider, string>> = {
        gemini: "gemini-2.5-flash",
        google: "gemini-2.5-flash",
        openai: "gpt-4.1-mini",
        anthropic: "anthropic.claude-haiku-4-5-20251001-v1:0",
      };
      const fallback = defaultByProvider[provider] || options[0].value;
      setContentModel(fallback);
    }
  }, [provider, contentModel]);

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        await uploadFiles(Array.from(files));
      }
    },
    [uploadFiles]
  );

  const handleAddUrl = useCallback(() => {
    const trimmed = urlInput.trim();
    if (trimmed && !urls.includes(trimmed)) {
      setUrls((prev) => [...prev, trimmed]);
      setUrlInput("");
    }
  }, [urlInput, urls]);

  const handleRemoveUrl = useCallback((url: string) => {
    setUrls((prev) => prev.filter((u) => u !== url));
  }, []);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();

      if (!contentApiKey.trim()) {
        return;
      }

      // If image generation is enabled, image API key is required
      if (enableImageGeneration && !imageApiKey.trim()) {
        return;
      }

      const sources: SourceItem[] = [];

      uploadedFiles.forEach((f: UploadedFile) => {
        sources.push({ type: "file", file_id: f.fileId });
      });

      urls.forEach((url) => {
        sources.push({ type: "url", url });
      });

      if (textContent.trim()) {
        sources.push({ type: "text", content: textContent.trim() });
      }

      if (sources.length === 0) {
        return;
      }

      onSubmit(
        sources,
        {
          outputFormat,
          provider,
          contentModel,
          imageModel,
          audience,
          imageStyle,
          enableImageGeneration,
        },
        contentApiKey,
        enableImageGeneration ? imageApiKey : undefined
      );
    },
    [
      contentApiKey,
      imageApiKey,
      enableImageGeneration,
      uploadedFiles,
      urls,
      textContent,
      outputFormat,
      provider,
      contentModel,
      imageModel,
      audience,
      imageStyle,
      onSubmit,
    ]
  );

  const hasSources = uploadedFiles.length > 0 || urls.length > 0 || textContent.trim().length > 0;
  const hasRequiredApiKeys = contentApiKey.trim() && (!enableImageGeneration || imageApiKey.trim());

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Sources</CardTitle>
          <CardDescription>
            Add sources to generate your document from. You can mix files, URLs, and text.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Tabs value={sourceTab} onValueChange={(v) => setSourceTab(v as typeof sourceTab)}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="url">URL</TabsTrigger>
              <TabsTrigger value="upload">Upload</TabsTrigger>
              <TabsTrigger value="text">Text</TabsTrigger>
            </TabsList>

            <TabsContent value="url" className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor="url-input">URL</Label>
                <div className="flex gap-2">
                  <Input
                    id="url-input"
                    type="url"
                    placeholder="https://example.com/article"
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handleAddUrl();
                      }
                    }}
                  />
                  <Button type="button" variant="secondary" onClick={handleAddUrl}>
                    Add
                  </Button>
                </div>
              </div>
              {urls.length > 0 && (
                <div className="space-y-2">
                  {urls.map((url) => (
                    <div
                      key={url}
                      className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
                    >
                      <span className="truncate max-w-[300px]">{url}</span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveUrl(url)}
                      >
                        ×
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="upload" className="space-y-3">
              <Input
                type="file"
                multiple
                onChange={handleFileChange}
                disabled={uploading}
                accept=".pdf,.md,.txt,.docx,.pptx,.xlsx,.png,.jpg,.jpeg"
              />
              {uploading && <p className="text-sm text-muted-foreground">Uploading...</p>}
              {uploadError && <p className="text-sm text-red-500">{uploadError}</p>}
              {uploadedFiles.length > 0 && (
                <div className="space-y-2">
                  {uploadedFiles.map((f) => (
                    <div
                      key={f.fileId}
                      className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
                    >
                      <span className="truncate max-w-[300px]">{f.filename}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">
                          {(f.size / 1024).toFixed(1)} KB
                        </span>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFile(f.fileId)}
                        >
                          ×
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="text" className="space-y-3">
              <Textarea
                placeholder="Paste your text content here..."
                rows={6}
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Options</CardTitle>
          <CardDescription>Configure generation settings</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="output-format">Output Format</Label>
            <Select value={outputFormat} onValueChange={(v) => setOutputFormat(v as OutputFormat)}>
              <SelectTrigger id="output-format">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {outputOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="provider">AI Provider</Label>
            <Select value={provider} onValueChange={(v) => setProvider(v as Provider)}>
              <SelectTrigger id="provider">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gemini">Google Gemini</SelectItem>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="anthropic">Anthropic</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="content-model">Content Model</Label>
            <Select value={contentModel} onValueChange={setContentModel}>
              <SelectTrigger id="content-model">
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

          <div className="space-y-2">
            <Label htmlFor="audience">Target Audience</Label>
            <Select value={audience} onValueChange={(v) => setAudience(v as Audience)}>
              <SelectTrigger id="audience">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="technical">Technical</SelectItem>
                <SelectItem value="executive">Executive</SelectItem>
                <SelectItem value="client">Client</SelectItem>
                <SelectItem value="educational">Educational</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="image-style" className={!enableImageGeneration ? "text-muted-foreground" : ""}>
              Image Style {!enableImageGeneration && <span className="text-xs">(enable images first)</span>}
            </Label>
            <Select 
              value={imageStyle} 
              onValueChange={(v) => setImageStyle(v as ImageStyle)}
              disabled={!enableImageGeneration}
            >
              <SelectTrigger id="image-style" className={!enableImageGeneration ? "opacity-50" : ""}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="auto">Auto</SelectItem>
                <SelectItem value="infographic">Infographic</SelectItem>
                <SelectItem value="minimalist">Minimalist</SelectItem>
                <SelectItem value="corporate">Corporate</SelectItem>
                <SelectItem value="educational">Educational</SelectItem>
                <SelectItem value="diagram">Diagram</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="image-model" className={!enableImageGeneration ? "text-muted-foreground" : ""}>
              Image Model {!enableImageGeneration && <span className="text-xs">(enable images first)</span>}
            </Label>
            <Select
              value={imageModel}
              onValueChange={setImageModel}
              disabled={!enableImageGeneration}
            >
              <SelectTrigger id="image-model" className={!enableImageGeneration ? "opacity-50" : ""}>
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

          <div className="flex items-center space-x-2 sm:col-span-2">
            <Checkbox
              id="enable-images"
              checked={enableImageGeneration}
              onCheckedChange={(checked: boolean) => setEnableImageGeneration(checked)}
            />
            <Label
              htmlFor="enable-images"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
            >
              Enable image generation
            </Label>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
          <CardDescription>
            Enter API keys for content and image generation. Keys are sent directly to the backend and never stored.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="content-api-key">Content Generation API Key *</Label>
              {provider === "gemini" && (
                <a
                  href="https://aistudio.google.com/apikey"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary hover:underline flex items-center gap-1"
                >
                  Get Gemini API Key
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              )}
              {provider === "openai" && (
                <a
                  href="https://platform.openai.com/api-keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary hover:underline flex items-center gap-1"
                >
                  Get OpenAI API Key
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              )}
              {provider === "anthropic" && (
                <a
                  href="https://console.anthropic.com/settings/keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary hover:underline flex items-center gap-1"
                >
                  Get Claude API Key
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              )}
            </div>
            <p className="text-sm text-muted-foreground">
              Supports: {provider === "gemini" ? "Gemini" : provider === "openai" ? "OpenAI" : "Claude"}
            </p>
            <Input
              id="content-api-key"
              type="password"
              placeholder={`Enter your ${provider === "gemini" ? "Gemini" : provider === "openai" ? "OpenAI" : "Claude"} API key`}
              value={contentApiKey}
              onChange={(e) => setContentApiKey(e.target.value)}
              autoComplete="off"
            />
          </div>

          {enableImageGeneration && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="image-api-key">Image Generation API Key *</Label>
                <a
                  href="https://aistudio.google.com/apikey"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary hover:underline flex items-center gap-1"
                >
                  Get Gemini API Key
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              </div>
              <p className="text-sm text-muted-foreground">
                Requires: Gemini API key (image generation only supports Gemini)
              </p>
              <Input
                id="image-api-key"
                type="password"
                placeholder="Enter your Gemini API key for image generation"
                value={imageApiKey}
                onChange={(e) => setImageApiKey(e.target.value)}
                autoComplete="off"
              />
            </div>
          )}
        </CardContent>
      </Card>

      <Button
        type="submit"
        size="lg"
        className="w-full"
        disabled={isGenerating || !hasSources || !hasRequiredApiKeys}
      >
        {isGenerating ? "Generating..." : "Generate Document"}
      </Button>
    </form>
  );
}
