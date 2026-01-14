"use client";

import { useState, useCallback } from "react";
import { generateDocument, GenerateOptions } from "@/lib/api/generate";
import {
  GenerateRequest,
  DEFAULT_PREFERENCES,
  DEFAULT_CACHE_OPTIONS,
} from "@/lib/types/requests";
import {
  GenerationEvent,
  isCompleteEvent,
  isCacheHitEvent,
  isErrorEvent,
} from "@/lib/types/responses";

export type GenerationState =
  | "idle"
  | "generating"
  | "complete"
  | "cache_hit"
  | "error";

export interface UseGenerationResult {
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
  generate: (request: Partial<GenerateRequest>, apiKey: string) => Promise<void>;
  reset: () => void;
}

export function useGeneration(): UseGenerationResult {
  const [state, setState] = useState<GenerationState>("idle");
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("");
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<UseGenerationResult["metadata"]>(null);

  const reset = useCallback(() => {
    setState("idle");
    setProgress(0);
    setStatus("");
    setDownloadUrl(null);
    setError(null);
    setMetadata(null);
  }, []);

  const handleEvent = useCallback((event: GenerationEvent) => {
    if ("progress" in event && typeof event.progress === "number") {
      setProgress(event.progress);
    }

    if (isCompleteEvent(event)) {
      setState("complete");
      setDownloadUrl(event.download_url);
      setMetadata({
        title: event.metadata.title,
        pages: event.metadata.pages,
        slides: event.metadata.slides,
        imagesGenerated: event.metadata.images_generated,
      });
      setStatus("Document generated successfully");
    } else if (isCacheHitEvent(event)) {
      setState("cache_hit");
      setDownloadUrl(event.download_url);
      setStatus(`Retrieved from cache (${event.cached_at})`);
    } else if (isErrorEvent(event)) {
      setState("error");
      setError(event.error);
      setStatus("Generation failed");
    } else {
      // Progress event - map status to user-friendly message
      const statusMessages: Record<string, string> = {
        parsing: "Parsing source documents...",
        transforming: "Transforming content...",
        generating_images: "Generating images...",
        generating_output: "Creating document...",
        uploading: "Finalizing...",
      };
      
      // Use custom message if provided, otherwise use status mapping
      const displayMessage = event.message || statusMessages[event.status] || event.status;
      setStatus(displayMessage);
    }
  }, []);

  const generate = useCallback(
    async (partialRequest: Partial<GenerateRequest>, apiKey: string) => {
      reset();
      setState("generating");

      const request: GenerateRequest = {
        output_format: partialRequest.output_format || "pdf",
        sources: partialRequest.sources || [],
        provider: partialRequest.provider || "gemini",
        model: partialRequest.model || "gemini-2.5-pro",
        image_model: partialRequest.image_model || "gemini-3-pro-image-preview",
        preferences: { ...DEFAULT_PREFERENCES, ...partialRequest.preferences },
        cache: { ...DEFAULT_CACHE_OPTIONS, ...partialRequest.cache },
      };

      const options: GenerateOptions = {
        request,
        apiKey,
        onEvent: handleEvent,
        onError: (err) => {
          setState("error");
          setError(err.message);
        },
      };

      try {
        await generateDocument(options);
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
    status,
    downloadUrl,
    error,
    metadata,
    generate,
    reset,
  };
}
