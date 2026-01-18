// frontend/src/components/mindmap/MindMapForm.tsx

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
import { Provider, SourceItem } from "@/lib/types/requests";
import { MindMapMode } from "@/lib/types/mindmap";
import { useUpload, UploadedFile } from "@/hooks/useUpload";

interface MindMapFormProps {
  onSubmit: (
    sources: SourceItem[],
    options: {
      mode: MindMapMode;
      provider: Provider;
      model: string;
      maxDepth: number;
    },
    apiKey: string
  ) => void;
  isGenerating?: boolean;
}

const contentModelOptions: Record<Provider, { value: string; label: string }[]> = {
  gemini: [
    { value: "gemini-2.5-flash", label: "gemini-2.5-flash" },
    { value: "gemini-2.5-flash-lite", label: "gemini-2.5-flash-lite" },
    { value: "gemini-2.5-pro", label: "gemini-2.5-pro" },
  ],
  openai: [
    { value: "gpt-4.1-mini", label: "gpt-4.1-mini" },
    { value: "gpt-4.1", label: "gpt-4.1" },
  ],
  anthropic: [
    { value: "claude-haiku-4-5-20251001", label: "claude-haiku-4-5" },
    { value: "claude-sonnet-4-5-20250929", label: "claude-sonnet-4-5" },
  ],
  google: [
    { value: "gemini-2.5-flash", label: "gemini-2.5-flash" },
  ],
};

export function MindMapForm({ onSubmit, isGenerating = false }: MindMapFormProps) {
  const [sourceTab, setSourceTab] = useState<"url" | "upload" | "text">("url");
  const [urlInput, setUrlInput] = useState("");
  const [urls, setUrls] = useState<string[]>([]);
  const [textContent, setTextContent] = useState("");
  const { uploading, uploadedFiles, error: uploadError, uploadFiles, removeFile } = useUpload();

  const [mode, setMode] = useState<MindMapMode>("summarize");
  const [provider, setProvider] = useState<Provider>("gemini");
  const [model, setModel] = useState("gemini-2.5-flash");
  const [maxDepth, setMaxDepth] = useState(5);
  const [apiKey, setApiKey] = useState("");

  // Update model when provider changes
  useEffect(() => {
    const options = contentModelOptions[provider] || [];
    if (options.length > 0 && !options.some(opt => opt.value === model)) {
      setModel(options[0].value);
    }
  }, [provider, model]);

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

      if (!apiKey.trim()) return;

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

      if (sources.length === 0) return;

      onSubmit(sources, { mode, provider, model, maxDepth }, apiKey);
    },
    [apiKey, uploadedFiles, urls, textContent, mode, provider, model, maxDepth, onSubmit]
  );

  const hasSources = uploadedFiles.length > 0 || urls.length > 0 || textContent.trim().length > 0;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Sources</CardTitle>
          <CardDescription>
            Add content to generate a mind map from
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
              <div className="flex gap-2">
                <Input
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
                accept=".pdf,.md,.txt,.docx"
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
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(f.fileId)}
                      >
                        ×
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="text" className="space-y-3">
              <Textarea
                placeholder="Paste your content here..."
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
          <CardDescription>Configure mind map generation</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Generation Mode</Label>
            <Select value={mode} onValueChange={(v) => setMode(v as MindMapMode)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="summarize">Summarize Content</SelectItem>
                <SelectItem value="brainstorm">Brainstorm Ideas</SelectItem>
                <SelectItem value="structure">Document Structure</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>AI Provider</Label>
            <Select value={provider} onValueChange={(v) => setProvider(v as Provider)}>
              <SelectTrigger>
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
            <Label>Model</Label>
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(contentModelOptions[provider] || []).map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Max Depth (2-5)</Label>
            <Select value={String(maxDepth)} onValueChange={(v) => setMaxDepth(Number(v))}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="2">2 levels</SelectItem>
                <SelectItem value="3">3 levels</SelectItem>
                <SelectItem value="4">4 levels</SelectItem>
                <SelectItem value="5">5 levels (default)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>API Key</CardTitle>
          <CardDescription>
            Enter your API key for the selected provider
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Input
            type="password"
            placeholder={`Enter your ${provider === "gemini" ? "Gemini" : provider === "openai" ? "OpenAI" : "Claude"} API key`}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            autoComplete="off"
          />
        </CardContent>
      </Card>

      <Button
        type="submit"
        size="lg"
        className="w-full"
        disabled={isGenerating || !hasSources || !apiKey.trim()}
      >
        {isGenerating ? "Generating..." : "Generate Mind Map"}
      </Button>
    </form>
  );
}
