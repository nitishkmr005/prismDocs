// frontend/src/hooks/useFAQGeneration.ts

"use client";

import { useState, useCallback } from "react";
import { generateFAQ, GenerateFAQOptions } from "@/lib/api/faq";
import {
  FAQRequest,
  FAQEvent,
  FAQDocument,
  isFAQCompleteEvent,
  isFAQErrorEvent,
  isFAQProgressEvent,
} from "@/lib/types/faq";

export type FAQGenerationState = "idle" | "generating" | "complete" | "error";

export interface FAQProgressState {
  stage: string;
  percent: number;
  message?: string;
}

export interface FAQResult {
  document: FAQDocument;
  downloadUrl: string;
  filePath: string;
}

export interface UseFAQGenerationResult {
  state: FAQGenerationState;
  progress: FAQProgressState;
  result: FAQResult | null;
  error: string | null;
  generate: (request: FAQRequest, apiKey: string, userId?: string) => Promise<void>;
  reset: () => void;
}

const initialProgress: FAQProgressState = {
  stage: "extracting",
  percent: 0,
  message: undefined,
};

export function useFAQGeneration(): UseFAQGenerationResult {
  const [state, setState] = useState<FAQGenerationState>("idle");
  const [progress, setProgress] = useState<FAQProgressState>(initialProgress);
  const [result, setResult] = useState<FAQResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setState("idle");
    setProgress(initialProgress);
    setResult(null);
    setError(null);
  }, []);

  const handleEvent = useCallback((event: FAQEvent) => {
    if (isFAQCompleteEvent(event)) {
      setState("complete");
      setResult({
        document: event.document,
        downloadUrl: event.download_url,
        filePath: event.file_path,
      });
      setProgress({
        stage: "complete",
        percent: 100,
        message: "FAQ generated successfully",
      });
    } else if (isFAQErrorEvent(event)) {
      setState("error");
      setError(event.message);
    } else if (isFAQProgressEvent(event)) {
      setProgress({
        stage: event.stage,
        percent: event.percent,
        message: event.message,
      });
    }
  }, []);

  const generate = useCallback(
    async (request: FAQRequest, apiKey: string, userId?: string) => {
      reset();
      setState("generating");

      const options: GenerateFAQOptions = {
        request,
        apiKey,
        userId,
        onEvent: handleEvent,
        onError: (err) => {
          setState("error");
          setError(err.message);
        },
      };

      try {
        await generateFAQ(options);
      } catch (err) {
        setState("error");
        setError(err instanceof Error ? err.message : "Unknown error occurred");
      }
    },
    [handleEvent, reset]
  );

  return {
    state,
    progress,
    result,
    error,
    generate,
    reset,
  };
}
