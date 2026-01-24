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
  const { uploading, error: uploadError, uploadFile, removeFile } = useUpload();
  const hasFile = uploadedFiles.length > 0;
  const hasUrl = urls.length > 0;
  const hasText = textContent.trim().length > 0;
  const hasSource = hasFile || hasUrl || hasText;

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      if (hasSource) {
        return;
      }
      const file = e.target.files?.[0];
      if (!file) {
        return;
      }
      const uploaded = await uploadFile(file);
      if (uploaded) {
        onFilesChange([uploaded]);
      }
    },
    [hasSource, uploadFile, onFilesChange]
  );

  const handleRemoveFile = useCallback(
    (fileId: string) => {
      removeFile(fileId);
      onFilesChange(uploadedFiles.filter((f) => f.fileId !== fileId));
    },
    [removeFile, uploadedFiles, onFilesChange]
  );

  const handleAddUrl = useCallback(() => {
    if (hasSource) {
      return;
    }
    const trimmed = urlInput.trim();
    if (trimmed) {
      onUrlsChange([trimmed]);
      setUrlInput("");
    }
  }, [hasSource, urlInput, onUrlsChange]);

  const handleRemoveUrl = useCallback(
    (url: string) => {
      onUrlsChange(urls.filter((u) => u !== url));
    },
    [urls, onUrlsChange]
  );

  return (
    <div className="space-y-4 pt-3">
      {/* Source Type Tabs */}
      <Tabs value={sourceTab} onValueChange={(v) => setSourceTab(v as typeof sourceTab)}>
        <TabsList className="grid w-full grid-cols-3 h-10 bg-slate-100 dark:bg-slate-800/50 p-1 rounded-lg">
          <TabsTrigger
            value="url"
            className="text-xs font-medium data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700 data-[state=active]:shadow-sm rounded-md transition-all"
          >
            <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            URL
          </TabsTrigger>
          <TabsTrigger
            value="upload"
            className="text-xs font-medium data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700 data-[state=active]:shadow-sm rounded-md transition-all"
          >
            <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            Upload
          </TabsTrigger>
          <TabsTrigger
            value="text"
            className="text-xs font-medium data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700 data-[state=active]:shadow-sm rounded-md transition-all"
          >
            <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Text
          </TabsTrigger>
        </TabsList>

        <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-3 flex items-center gap-1.5">
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          One source at a time. Remove current to add another.
        </p>

        {/* URL Tab */}
        <TabsContent value="url" className="mt-4 space-y-3">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
              </div>
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
                disabled={hasSource}
                className="h-10 pl-10 text-sm bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 focus:border-amber-500 dark:focus:border-amber-500 focus:ring-amber-500/20"
              />
            </div>
            <Button
              type="button"
              size="sm"
              onClick={handleAddUrl}
              disabled={hasSource || !urlInput.trim()}
              className="h-10 px-4 bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-slate-100 font-medium"
            >
              Add
            </Button>
          </div>
          {urls.length > 0 && (
            <div className="space-y-2">
              {urls.map((url) => (
                <div
                  key={url}
                  className="group flex items-center gap-3 rounded-lg border border-emerald-200 dark:border-emerald-800/50 bg-emerald-50/50 dark:bg-emerald-950/20 px-3 py-2.5"
                >
                  <div className="w-8 h-8 rounded-md bg-emerald-100 dark:bg-emerald-900/50 flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="flex-1 text-sm text-slate-700 dark:text-slate-300 truncate font-medium">{url}</span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-100 dark:hover:bg-red-900/50 hover:text-red-600 dark:hover:text-red-400"
                    onClick={() => handleRemoveUrl(url)}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </Button>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Upload Tab */}
        <TabsContent value="upload" className="mt-4 space-y-3">
          <div className={`relative rounded-xl border-2 border-dashed p-6 text-center transition-all ${
            hasSource
              ? "border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/30 cursor-not-allowed"
              : "border-slate-300 dark:border-slate-600 hover:border-amber-400 dark:hover:border-amber-500 hover:bg-amber-50/50 dark:hover:bg-amber-950/20 cursor-pointer"
          }`}>
            <input
              type="file"
              onChange={handleFileChange}
              disabled={uploading || hasSource}
              accept=".pdf,.md,.txt,.docx,.pptx,.png,.jpg,.jpeg"
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className={hasSource ? "cursor-not-allowed" : "cursor-pointer"}>
              <div className={`w-12 h-12 mx-auto rounded-xl flex items-center justify-center mb-3 ${
                hasSource
                  ? "bg-slate-200 dark:bg-slate-700"
                  : "bg-gradient-to-br from-amber-100 to-orange-100 dark:from-amber-900/50 dark:to-orange-900/50"
              }`}>
                {uploading ? (
                  <div className="w-5 h-5 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <svg className={`w-6 h-6 ${hasSource ? "text-slate-400 dark:text-slate-500" : "text-amber-600 dark:text-amber-400"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                )}
              </div>
              <p className={`text-sm font-medium ${hasSource ? "text-slate-400 dark:text-slate-500" : "text-slate-700 dark:text-slate-300"}`}>
                {uploading ? "Uploading..." : hasSource ? "Source already added" : "Drop a file or click to upload"}
              </p>
              <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1.5">
                PDF, MD, TXT, DOCX, PPTX, Images
              </p>
            </label>
          </div>
          {uploadError && (
            <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 px-3 py-2 rounded-lg">
              <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {uploadError}
            </div>
          )}
          {uploadedFiles.length > 0 && (
            <div className="space-y-2">
              {uploadedFiles.map((f) => (
                <div
                  key={f.fileId}
                  className="group flex items-center gap-3 rounded-lg border border-emerald-200 dark:border-emerald-800/50 bg-emerald-50/50 dark:bg-emerald-950/20 px-3 py-2.5"
                >
                  <div className="w-8 h-8 rounded-md bg-emerald-100 dark:bg-emerald-900/50 flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-sm text-slate-700 dark:text-slate-300 truncate block font-medium">{f.filename}</span>
                    <span className="text-[11px] text-slate-400 dark:text-slate-500">{(f.size / 1024).toFixed(1)} KB</span>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-100 dark:hover:bg-red-900/50 hover:text-red-600 dark:hover:text-red-400"
                    onClick={() => handleRemoveFile(f.fileId)}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </Button>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Text Tab */}
        <TabsContent value="text" className="mt-4">
          <div className="relative">
            <Textarea
              placeholder="Paste your text content here..."
              rows={5}
              value={textContent}
              onChange={(e) => onTextChange(e.target.value)}
              disabled={hasSource && !hasText}
              className="text-sm resize-none bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 focus:border-amber-500 dark:focus:border-amber-500 focus:ring-amber-500/20 placeholder:text-slate-400 dark:placeholder:text-slate-500"
            />
            {textContent.trim() && (
              <div className="absolute bottom-2 right-2 flex items-center gap-1.5 text-[10px] text-slate-400 dark:text-slate-500 bg-white/80 dark:bg-slate-800/80 px-2 py-1 rounded">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                </svg>
                {textContent.trim().split(/\s+/).length} words
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
