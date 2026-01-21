/**
 * Shared SSE streaming utilities for generation hooks.
 * 
 * This module provides common patterns for SSE-based generation hooks,
 * eliminating duplication across useGeneration, useMindMapGeneration,
 * and usePodcastGeneration.
 */

import { useState, useCallback, useRef } from "react";

/**
 * Base state for any SSE generation hook.
 */
export type GenerationState = "idle" | "generating" | "complete" | "error";

/**
 * Progress state for streaming operations.
 */
export interface ProgressState {
  stage: string;
  percent: number;
  message?: string;
}

/**
 * Initial progress state constant.
 */
export const INITIAL_PROGRESS: ProgressState = {
  stage: "idle",
  percent: 0,
  message: undefined,
};

/**
 * Base interface for generation hook results.
 * Extend this interface for specific generation types.
 */
export interface BaseGenerationResult<TResult> {
  state: GenerationState;
  progress: ProgressState;
  result: TResult | null;
  error: string | null;
  reset: () => void;
}

/**
 * Options for creating a generation hook.
 */
export interface UseGenerationOptions<TEvent, TResult> {
  /**
   * Handle a complete event and extract the result.
   */
  onComplete: (event: TEvent) => TResult;
  
  /**
   * Check if an event is a complete event.
   */
  isComplete: (event: TEvent) => boolean;
  
  /**
   * Check if an event is an error event.
   */
  isError: (event: TEvent) => boolean;
  
  /**
   * Check if an event is a progress event.
   */
  isProgress: (event: TEvent) => boolean;
  
  /**
   * Extract error message from error event.
   */
  getErrorMessage: (event: TEvent) => string;
  
  /**
   * Extract progress from progress event.
   */
  getProgress: (event: TEvent) => ProgressState;
}

/**
 * Create state management for an SSE generation hook.
 * 
 * This factory function creates the common state management logic
 * shared across all generation hooks.
 * 
 * @param options Configuration options for event handling
 * @returns State and handlers for the generation hook
 * 
 * @example
 * ```typescript
 * const { state, progress, result, error, reset, handleEvent, setGenerating, setError } = 
 *   useGenerationState<MindMapEvent, MindMapTree>({
 *     onComplete: (event) => event.tree,
 *     isComplete: isMindMapCompleteEvent,
 *     isError: isMindMapErrorEvent,
 *     isProgress: isMindMapProgressEvent,
 *     getErrorMessage: (event) => event.message,
 *     getProgress: (event) => ({ stage: event.stage, percent: event.percent, message: event.message }),
 *   });
 * ```
 */
export function useGenerationState<TEvent, TResult>(
  options: UseGenerationOptions<TEvent, TResult>
) {
  const [state, setState] = useState<GenerationState>("idle");
  const [progress, setProgress] = useState<ProgressState>(INITIAL_PROGRESS);
  const [result, setResult] = useState<TResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setState("idle");
    setProgress(INITIAL_PROGRESS);
    setResult(null);
    setError(null);
  }, []);

  const handleEvent = useCallback((event: TEvent) => {
    if (options.isComplete(event)) {
      setState("complete");
      setResult(options.onComplete(event));
      setProgress({ 
        stage: "complete", 
        percent: 100, 
        message: "Generation complete" 
      });
    } else if (options.isError(event)) {
      setState("error");
      setError(options.getErrorMessage(event));
    } else if (options.isProgress(event)) {
      setProgress(options.getProgress(event));
    }
  }, [options]);

  const setGenerating = useCallback(() => {
    reset();
    setState("generating");
  }, [reset]);

  const setErrorState = useCallback((errorMessage: string) => {
    setState("error");
    setError(errorMessage);
  }, []);

  return {
    // State
    state,
    progress,
    result,
    error,
    // Handlers
    reset,
    handleEvent,
    setGenerating,
    setError: setErrorState,
  };
}

/**
 * Convert snake_case keys to camelCase.
 * Useful for converting backend responses to frontend conventions.
 * 
 * @param obj Object with snake_case keys
 * @returns Object with camelCase keys
 * 
 * @example
 * ```typescript
 * const input = { audio_base64: "...", duration_seconds: 120 };
 * const output = toCamelCase(input);
 * // { audioBase64: "...", durationSeconds: 120 }
 * ```
 */
export function toCamelCase<T extends Record<string, unknown>>(
  obj: T
): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  
  for (const key of Object.keys(obj)) {
    const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
    const value = obj[key];
    
    if (value !== null && typeof value === "object" && !Array.isArray(value)) {
      result[camelKey] = toCamelCase(value as Record<string, unknown>);
    } else if (Array.isArray(value)) {
      result[camelKey] = value.map((item) => 
        item !== null && typeof item === "object" 
          ? toCamelCase(item as Record<string, unknown>) 
          : item
      );
    } else {
      result[camelKey] = value;
    }
  }
  
  return result;
}

/**
 * Standard error handler for async generation functions.
 * Normalizes different error types to a string message.
 * 
 * @param err The caught error
 * @returns Normalized error message
 */
export function normalizeError(err: unknown): string {
  if (err instanceof Error) {
    return err.message;
  }
  return "Unknown error occurred";
}

/**
 * Type guard creator for event type checking.
 * Creates a type guard function from an event type string.
 * 
 * @param eventType The event type string to check for
 * @returns Type guard function
 * 
 * @example
 * ```typescript
 * interface ProgressEvent { event: "progress"; percent: number; }
 * const isProgressEvent = createEventTypeGuard<ProgressEvent>("progress");
 * ```
 */
export function createEventTypeGuard<T extends { event: string }>(
  eventType: string
): (event: T) => boolean {
  return (event: T): boolean => event.event === eventType;
}
