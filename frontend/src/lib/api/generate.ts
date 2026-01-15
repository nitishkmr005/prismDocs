import { API_CONFIG, getApiUrl } from "@/config/api";
import { GenerateRequest } from "@/lib/types/requests";
import { GenerationEvent } from "@/lib/types/responses";

function getApiKeyHeader(provider: string): string {
  switch (provider.toLowerCase()) {
    case "gemini":
    case "google":
      return "X-Google-Key";
    case "openai":
      return "X-OpenAI-Key";
    case "anthropic":
      return "X-Anthropic-Key";
    default:
      return "X-Api-Key";
  }
}

export interface GenerateOptions {
  request: GenerateRequest;
  apiKey: string;
  imageApiKey?: string;
  onEvent?: (event: GenerationEvent) => void;
  onError?: (error: Error) => void;
  signal?: AbortSignal;
}

export async function generateDocument(
  options: GenerateOptions
): Promise<GenerationEvent> {
  const { request, apiKey, imageApiKey, onEvent, onError, signal } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
    [getApiKeyHeader(request.provider)]: apiKey,
  };

  if (imageApiKey) {
    headers["X-Image-Key"] = imageApiKey;
  }

  const response = await fetch(getApiUrl(API_CONFIG.endpoints.generate), {
    method: "POST",
    headers,
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const error = new Error(
      errorData.detail || `Generation failed: ${response.statusText}`
    );
    onError?.(error);
    throw error;
  }

  if (!response.body) {
    throw new Error("No response body received");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let lastEvent: GenerationEvent | null = null;

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6).trim();
          if (data) {
            try {
              const event = JSON.parse(data) as GenerationEvent;
              lastEvent = event;
              onEvent?.(event);

              if (
                event.status === "complete" ||
                event.status === "cache_hit" ||
                event.status === "error"
              ) {
                return event;
              }
            } catch (parseError) {
              console.error("Failed to parse SSE data:", parseError);
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  if (!lastEvent) {
    throw new Error("No events received from server");
  }

  return lastEvent;
}
