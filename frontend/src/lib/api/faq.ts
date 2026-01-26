// frontend/src/lib/api/faq.ts

import { getApiUrl } from "@/config/api";
import { FAQRequest, FAQEvent } from "@/lib/types/faq";
import { Provider } from "@/lib/types/requests";

export interface GenerateFAQOptions {
  request: FAQRequest;
  apiKey: string;
  userId?: string;
  onEvent: (event: FAQEvent) => void;
  onError: (error: Error) => void;
}

function getApiKeyHeader(provider: Provider): string {
  switch (provider) {
    case "gemini":
    case "google":
      return "X-Google-Key";
    case "openai":
      return "X-OpenAI-Key";
    case "anthropic":
      return "X-Anthropic-Key";
    default:
      return "X-Google-Key";
  }
}

export async function generateFAQ(options: GenerateFAQOptions): Promise<void> {
  const { request, apiKey, userId, onEvent, onError } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    [getApiKeyHeader(request.provider)]: apiKey,
  };

  if (userId) {
    headers["X-User-Id"] = userId;
  }

  const url = getApiUrl("/api/unified/generate/faq");

  try {
    const response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`FAQ generation failed: ${errorText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("No response body");
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6).trim();
          if (data && data !== "[DONE]") {
            try {
              const event = JSON.parse(data) as FAQEvent;
              onEvent(event);
            } catch {
              // Ignore parse errors for partial data
            }
          }
        }
      }
    }
  } catch (error) {
    onError(error instanceof Error ? error : new Error(String(error)));
  }
}
