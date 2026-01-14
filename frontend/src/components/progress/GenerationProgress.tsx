"use client";

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
  if (state === "idle") {
    return null;
  }

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

            <div className="flex gap-2">
              {downloadUrl && (
                <Button asChild>
                  <a href={downloadUrl} download target="_blank" rel="noopener noreferrer">
                    Download Document
                  </a>
                </Button>
              )}
              {onReset && (
                <Button variant="outline" onClick={onReset}>
                  Generate Another
                </Button>
              )}
            </div>
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
