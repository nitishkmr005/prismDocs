// frontend/src/hooks/usePodcastGeneration.ts

"use client";

import { useState, useCallback } from "react";
import { generatePodcast, GeneratePodcastOptions } from "@/lib/api/podcast";
import {
  PodcastRequest,
  PodcastEvent,
  PodcastCompleteEvent,
  isPodcastCompleteEvent,
  isPodcastErrorEvent,
  isPodcastProgressEvent,
} from "@/lib/types/podcast";

export type PodcastGenerationState = "idle" | "generating" | "complete" | "error";

export interface PodcastProgressState {
  stage: string;
  percent: number;
  message?: string;
}

export interface PodcastResult {
  title: string;
  description: string;
  audioBase64: string;
  script: Array<{ speaker: string; text: string }>;
  durationSeconds: number;
}

export interface UsePodcastGenerationResult {
  state: PodcastGenerationState;
  progress: PodcastProgressState;
  result: PodcastResult | null;
  error: string | null;
  generate: (
    request: PodcastRequest,
    apiKey: string,
    userId?: string
  ) => Promise<void>;
  reset: () => void;
}

const initialProgress: PodcastProgressState = {
  stage: "extracting",
  percent: 0,
  message: undefined,
};

export function usePodcastGeneration(): UsePodcastGenerationResult {
  const [state, setState] = useState<PodcastGenerationState>("idle");
  const [progress, setProgress] = useState<PodcastProgressState>(initialProgress);
  const [result, setResult] = useState<PodcastResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setState("idle");
    setProgress(initialProgress);
    setResult(null);
    setError(null);
  }, []);

  const handleEvent = useCallback((event: PodcastEvent) => {
    if (isPodcastCompleteEvent(event)) {
      setState("complete");
      setResult({
        title: event.title,
        description: event.description,
        audioBase64: event.audio_base64,
        script: event.script,
        durationSeconds: event.duration_seconds,
      });
      setProgress({ 
        stage: "complete", 
        percent: 100, 
        message: "Podcast generated successfully" 
      });
    } else if (isPodcastErrorEvent(event)) {
      setState("error");
      setError(event.message);
    } else if (isPodcastProgressEvent(event)) {
      setProgress({
        stage: event.stage,
        percent: event.percent,
        message: event.message,
      });
    }
  }, []);

  const generate = useCallback(
    async (request: PodcastRequest, apiKey: string, userId?: string) => {
      reset();
      setState("generating");

      const options: GeneratePodcastOptions = {
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
        await generatePodcast(options);
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
