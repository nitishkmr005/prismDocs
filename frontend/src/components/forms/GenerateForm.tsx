"use client";

import { useState, useCallback } from "react";
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
import {
  OutputFormat,
  Provider,
  Audience,
  ImageStyle,
  SourceItem,
} from "@/lib/types/requests";
import { useUpload, UploadedFile } from "@/hooks/useUpload";

interface GenerateFormProps {
  onSubmit: (
    sources: SourceItem[],
    options: {
      outputFormat: OutputFormat;
      provider: Provider;
      audience: Audience;
      imageStyle: ImageStyle;
    },
    apiKey: string
  ) => void;
  isGenerating?: boolean;
}

export function GenerateForm({ onSubmit, isGenerating = false }: GenerateFormProps) {
  const [sourceTab, setSourceTab] = useState<"upload" | "url" | "text">("url");
  const [urlInput, setUrlInput] = useState("");
  const [urls, setUrls] = useState<string[]>([]);
  const [textContent, setTextContent] = useState("");
  const { uploading, uploadedFiles, error: uploadError, uploadFiles, removeFile } = useUpload();

  const [outputFormat, setOutputFormat] = useState<OutputFormat>("pdf");
  const [provider, setProvider] = useState<Provider>("gemini");
  const [audience, setAudience] = useState<Audience>("technical");
  const [imageStyle, setImageStyle] = useState<ImageStyle>("auto");
  const [apiKey, setApiKey] = useState("");

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
    if (urlInput.trim() && !urls.includes(urlInput.trim())) {
      setUrls((prev) => [...prev, urlInput.trim()]);
      setUrlInput("");
    }
  }, [urlInput, urls]);

  const handleRemoveUrl = useCallback((url: string) => {
    setUrls((prev) => prev.filter((u) => u !== url));
  }, []);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();

      if (!apiKey.trim()) {
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

      onSubmit(sources, { outputFormat, provider, audience, imageStyle }, apiKey);
    },
    [
      apiKey,
      uploadedFiles,
      urls,
      textContent,
      outputFormat,
      provider,
      audience,
      imageStyle,
      onSubmit,
    ]
  );

  const hasSources = uploadedFiles.length > 0 || urls.length > 0 || textContent.trim().length > 0;

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
                <SelectItem value="pdf">PDF Document</SelectItem>
                <SelectItem value="pptx">PowerPoint Presentation</SelectItem>
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
            <Label htmlFor="image-style">Image Style</Label>
            <Select value={imageStyle} onValueChange={(v) => setImageStyle(v as ImageStyle)}>
              <SelectTrigger id="image-style">
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
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>API Key</CardTitle>
          <CardDescription>
            Enter your API key for the selected provider. Your key is only sent directly to
            the backend and is never stored.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Input
            type="password"
            placeholder={`Enter your ${provider === "gemini" ? "Gemini" : provider === "openai" ? "OpenAI" : "Anthropic"} API key`}
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
        {isGenerating ? "Generating..." : "Generate Document"}
      </Button>
    </form>
  );
}
