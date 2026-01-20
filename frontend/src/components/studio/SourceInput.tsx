"use client";

import { useState, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { useUpload, UploadedFile } from "@/hooks/useUpload";
import { SourceItem } from "@/lib/types/requests";

interface SourceInputProps {
  onSourcesChange: (sources: SourceItem[]) => void;
  uploadedFiles: UploadedFile[];
  urls: string[];
  textContent: string;
  onFilesChange: (files: UploadedFile[]) => void;
  onUrlsChange: (urls: string[]) => void;
  onTextChange: (text: string) => void;
}

export function SourceInput({
  uploadedFiles,
  urls,
  textContent,
  onFilesChange,
  onUrlsChange,
  onTextChange,
}: SourceInputProps) {
  const [sourceTab, setSourceTab] = useState<"upload" | "url" | "text">("url");
  const [urlInput, setUrlInput] = useState("");
  const { uploading, error: uploadError, uploadFiles, removeFile } = useUpload();

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        const newFiles = await uploadFiles(Array.from(files));
        if (newFiles.length > 0) {
          onFilesChange([...uploadedFiles, ...newFiles]);
        }
      }
    },
    [uploadFiles, uploadedFiles, onFilesChange]
  );

  const handleRemoveFile = useCallback(
    (fileId: string) => {
      removeFile(fileId);
      onFilesChange(uploadedFiles.filter((f) => f.fileId !== fileId));
    },
    [removeFile, uploadedFiles, onFilesChange]
  );

  const handleAddUrl = useCallback(() => {
    const trimmed = urlInput.trim();
    if (trimmed && !urls.includes(trimmed)) {
      onUrlsChange([...urls, trimmed]);
      setUrlInput("");
    }
  }, [urlInput, urls, onUrlsChange]);

  const handleRemoveUrl = useCallback(
    (url: string) => {
      onUrlsChange(urls.filter((u) => u !== url));
    },
    [urls, onUrlsChange]
  );

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Label className="text-sm font-semibold">Sources</Label>
        <span className="text-xs text-muted-foreground">
          {uploadedFiles.length + urls.length + (textContent.trim() ? 1 : 0)} source(s)
        </span>
      </div>

      <Tabs value={sourceTab} onValueChange={(v) => setSourceTab(v as typeof sourceTab)}>
        <TabsList className="grid w-full grid-cols-3 h-9">
          <TabsTrigger value="url" className="text-xs">
            <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            URL
          </TabsTrigger>
          <TabsTrigger value="upload" className="text-xs">
            <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            Upload
          </TabsTrigger>
          <TabsTrigger value="text" className="text-xs">
            <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Text
          </TabsTrigger>
        </TabsList>

        <TabsContent value="url" className="mt-3 space-y-3">
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
              className="h-9 text-sm"
            />
            <Button type="button" variant="secondary" size="sm" onClick={handleAddUrl}>
              Add
            </Button>
          </div>
          {urls.length > 0 && (
            <div className="space-y-1.5 max-h-28 overflow-y-auto">
              {urls.map((url) => (
                <div
                  key={url}
                  className="flex items-center justify-between rounded-md border px-2.5 py-1.5 text-xs bg-muted/30"
                >
                  <span className="truncate max-w-[200px]">{url}</span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-5 w-5 p-0"
                    onClick={() => handleRemoveUrl(url)}
                  >
                    ×
                  </Button>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="upload" className="mt-3 space-y-3">
          <div className="rounded-lg border-2 border-dashed p-4 text-center transition-colors hover:border-primary/50 cursor-pointer">
            <input
              type="file"
              multiple
              onChange={handleFileChange}
              disabled={uploading}
              accept=".pdf,.md,.txt,.docx,.pptx,.png,.jpg,.jpeg"
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <svg className="w-8 h-8 mx-auto text-muted-foreground mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-xs text-muted-foreground">
                {uploading ? "Uploading..." : "Drop files or click to upload"}
              </p>
              <p className="text-[10px] text-muted-foreground/70 mt-1">
                PDF, MD, TXT, DOCX, PPTX, Images
              </p>
            </label>
          </div>
          {uploadError && <p className="text-xs text-red-500">{uploadError}</p>}
          {uploadedFiles.length > 0 && (
            <div className="space-y-1.5 max-h-28 overflow-y-auto">
              {uploadedFiles.map((f) => (
                <div
                  key={f.fileId}
                  className="flex items-center justify-between rounded-md border px-2.5 py-1.5 text-xs bg-muted/30"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <svg className="w-3.5 h-3.5 text-muted-foreground shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span className="truncate">{f.filename}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-muted-foreground text-[10px]">
                      {(f.size / 1024).toFixed(1)} KB
                    </span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-5 w-5 p-0"
                      onClick={() => handleRemoveFile(f.fileId)}
                    >
                      ×
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="text" className="mt-3">
          <Textarea
            placeholder="Paste your text content here..."
            rows={4}
            value={textContent}
            onChange={(e) => onTextChange(e.target.value)}
            className="text-sm resize-none"
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
