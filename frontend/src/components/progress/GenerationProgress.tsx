"use client";

import { useEffect, useState } from "react";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GenerationState } from "@/hooks/useGeneration";

interface GenerationProgressProps {
  state: GenerationState;
  progress: number;
  status: string;
  downloadUrl: string | null;
  error: string | null;
  metadata: {
    title?: string;
    pages?: number;
    slides?: number;
    imagesGenerated?: number;
  } | null;
  onReset?: () => void;
}

export function GenerationProgress({
  state,
  progress,
  status,
  downloadUrl,
  error,
  metadata,
  onReset,
}: GenerationProgressProps) {
  const [showPreview, setShowPreview] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewContent, setPreviewContent] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [activeAction, setActiveAction] = useState<"download" | "preview" | null>(
    null
  );

  if (state === "idle") {
    return null;
  }

  const isPdf =
    downloadUrl?.toLowerCase().includes(".pdf") || downloadUrl?.includes("/pdf/");
  const isPptx = downloadUrl?.toLowerCase().includes(".pptx") || downloadUrl?.includes("/pptx/");
  const isMarkdown =
    downloadUrl?.toLowerCase().includes(".md") || downloadUrl?.includes("/markdown/");

  useEffect(() => {
    if (!showPreview || !downloadUrl || (!isPdf && !isMarkdown)) {
      setPreviewUrl(null);
      setPreviewContent(null);
      setPreviewError(null);
      setPreviewLoading(false);
      return;
    }

    let active = true;
    let objectUrl: string | null = null;
    const controller = new AbortController();
    setPreviewLoading(true);
    setPreviewError(null);
    setPreviewContent(null);

    const loadPreview = async () => {
      try {
        const res = await fetch(downloadUrl, { signal: controller.signal });
        if (!res.ok) {
          throw new Error(`Preview failed (${res.status})`);
        }
        if (!active) return;

        if (isPdf) {
          const blob = await res.blob();
          if (!active) return;
          objectUrl = URL.createObjectURL(blob);
          setPreviewUrl(objectUrl);
          return;
        }

        const text = await res.text();
        if (!active) return;
        setPreviewContent(text);
      } catch (err) {
        if (!active || controller.signal.aborted) return;
        setPreviewError(err instanceof Error ? err.message : "Preview failed");
      } finally {
        if (active) setPreviewLoading(false);
      }
    };

    loadPreview();

    return () => {
      active = false;
      controller.abort();
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [downloadUrl, isMarkdown, isPdf, showPreview]);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {state === "generating" && (
            <>
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
              </span>
              Generating Document
            </>
          )}
          {(state === "complete" || state === "cache_hit") && (
            <>
              <span className="inline-flex h-3 w-3 rounded-full bg-green-500"></span>
              {state === "cache_hit" ? "Retrieved from Cache" : "Generation Complete"}
            </>
          )}
          {state === "error" && (
            <>
              <span className="inline-flex h-3 w-3 rounded-full bg-red-500"></span>
              Error
            </>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {state === "generating" && (
          <div className="space-y-2">
            <Progress value={progress} className="h-2" />
            <p className="text-sm text-muted-foreground">{status}</p>
          </div>
        )}

        {(state === "complete" || state === "cache_hit") && (
          <div className="space-y-4">
            <Alert className="border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950">
              <AlertTitle>Success!</AlertTitle>
              <AlertDescription>
                {metadata?.title && <p className="font-medium">{metadata.title}</p>}
                {status && <p className="text-sm text-muted-foreground">{status}</p>}
                {metadata && (
                  <div className="mt-2 flex gap-4 text-sm">
                    {metadata.pages && metadata.pages > 0 && (
                      <span>{metadata.pages} pages</span>
                    )}
                    {metadata.slides && metadata.slides > 0 && (
                      <span>{metadata.slides} slides</span>
                    )}
                    {metadata.imagesGenerated && metadata.imagesGenerated > 0 && (
                      <span>{metadata.imagesGenerated} images</span>
                    )}
                  </div>
                )}
              </AlertDescription>
            </Alert>

            <div className="flex flex-wrap gap-2">
              {downloadUrl && (
                <Button
                  asChild
                  variant={activeAction === "download" ? "default" : "secondary"}
                  onClick={() => setActiveAction("download")}
                >
                  <a href={downloadUrl} download target="_blank" rel="noopener noreferrer">
                    Download Document
                  </a>
                </Button>
              )}
              {downloadUrl && (isPdf || isMarkdown) && (
                <Button
                  variant={activeAction === "preview" ? "default" : "secondary"}
                  onClick={() => {
                    setActiveAction("preview");
                    setShowPreview(!showPreview);
                  }}
                >
                  {showPreview ? "Hide Preview" : "Show Preview"}
                </Button>
              )}
              {downloadUrl && isPptx && (
                <Button
                  variant="secondary"
                  asChild
                >
                  <a href={downloadUrl} target="_blank" rel="noopener noreferrer">
                    Open in New Tab
                  </a>
                </Button>
              )}
              {onReset && (
                <Button variant="outline" onClick={onReset}>
                  Generate Another
                </Button>
              )}
            </div>

            {/* PDF Preview */}
            {downloadUrl && isPdf && showPreview && (
              <div className="mt-4 border rounded-lg overflow-hidden bg-muted">
                <div className="bg-muted px-4 py-2 border-b flex items-center justify-between">
                  <span className="text-sm font-medium">Document Preview</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => window.open(downloadUrl, "_blank")}
                  >
                    Open in New Tab
                  </Button>
                </div>
                {previewLoading && (
                  <div className="p-6 text-sm text-muted-foreground">Loading preview...</div>
                )}
                {previewError && (
                  <div className="p-6 text-sm text-red-500">{previewError}</div>
                )}
                {!previewLoading && !previewError && previewUrl && (
                  <iframe
                    src={previewUrl}
                    className="w-full h-[600px] border-0"
                    title="Document Preview"
                  />
                )}
              </div>
            )}

            {/* Markdown Preview */}
            {downloadUrl && isMarkdown && showPreview && (
              <div className="mt-4 border rounded-lg overflow-hidden bg-muted">
                <div className="bg-muted px-4 py-2 border-b flex items-center justify-between">
                  <span className="text-sm font-medium">Markdown Preview</span>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        if (previewContent) {
                          navigator.clipboard.writeText(previewContent);
                        }
                      }}
                    >
                      Copy
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => window.open(downloadUrl, "_blank")}
                    >
                      Open in New Tab
                    </Button>
                  </div>
                </div>
                {previewLoading && (
                  <div className="p-6 text-sm text-muted-foreground">Loading preview...</div>
                )}
                {previewError && (
                  <div className="p-6 text-sm text-red-500">{previewError}</div>
                )}
                {!previewLoading && !previewError && previewContent && (
                  <pre className="p-6 text-sm whitespace-pre-wrap break-words">
                    {previewContent}
                  </pre>
                )}
              </div>
            )}
          </div>
        )}

        {state === "error" && (
          <div className="space-y-4">
            <Alert variant="destructive">
              <AlertTitle>Generation Failed</AlertTitle>
              <AlertDescription>{error || "An unexpected error occurred."}</AlertDescription>
            </Alert>

            {onReset && (
              <Button variant="outline" onClick={onReset}>
                Try Again
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
