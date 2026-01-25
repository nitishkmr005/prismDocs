// frontend/src/lib/api/idea-canvas.ts

import { getApiUrl } from "@/config/api";
import {
  StartCanvasRequest,
  AnswerRequest,
  CanvasEvent,
} from "@/lib/types/idea-canvas";
import { Provider } from "@/lib/types/requests";

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

export interface StartCanvasOptions {
  request: StartCanvasRequest;
  apiKey: string;
  userId?: string;
  onEvent: (event: CanvasEvent) => void;
  onError: (error: Error) => void;
}

export async function startCanvas(options: StartCanvasOptions): Promise<void> {
  const { request, apiKey, userId, onEvent, onError } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    [getApiKeyHeader(request.provider)]: apiKey,
  };

  if (userId) {
    headers["X-User-Id"] = userId;
  }

  const url = getApiUrl("/api/canvas/start");

  try {
    const response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to start canvas: ${errorText}`);
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
              const event = JSON.parse(data) as CanvasEvent;
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

export interface SubmitAnswerOptions {
  request: AnswerRequest;
  apiKey: string;
  provider: Provider;
  userId?: string;
  onEvent: (event: CanvasEvent) => void;
  onError: (error: Error) => void;
}

export async function submitAnswer(options: SubmitAnswerOptions): Promise<void> {
  const { request, apiKey, provider, userId, onEvent, onError } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    [getApiKeyHeader(provider)]: apiKey,
  };

  if (userId) {
    headers["X-User-Id"] = userId;
  }

  const url = getApiUrl("/api/canvas/answer");

  try {
    const response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to submit answer: ${errorText}`);
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
              const event = JSON.parse(data) as CanvasEvent;
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

export interface GenerateReportOptions {
  sessionId: string;
  outputFormat?: "pdf" | "markdown" | "both";
  provider: Provider;
  apiKey: string;
  imageApiKey?: string;
}

export interface GenerateReportResult {
  session_id: string;
  title: string;
  pdf_url?: string;
  pdf_base64?: string;
  image_base64?: string;
  image_format?: "png" | "svg";
  markdown_url?: string;
  markdown_content?: string;
}

export async function generateCanvasReport(options: GenerateReportOptions): Promise<GenerateReportResult> {
  const { sessionId, outputFormat = "both", provider, apiKey, imageApiKey } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    [getApiKeyHeader(provider)]: apiKey,
  };
  if (imageApiKey) {
    headers["X-Image-Key"] = imageApiKey;
  }

  const url = getApiUrl("/api/canvas/report");

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify({
      session_id: sessionId,
      output_format: outputFormat,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to generate report: ${errorText}`);
  }

  return response.json();
}

export interface GenerateMindmapOptions {
  sessionId: string;
  provider: Provider;
  apiKey: string;
}

export interface CanvasMindmapResult {
  title: string;
  summary: string;
  source_count: number;
  mode: "summarize" | "brainstorm" | "structure";
  nodes: {
    id: string;
    label: string;
    children?: CanvasMindmapResult["nodes"][];
  };
}

export async function generateCanvasMindmap(options: GenerateMindmapOptions): Promise<CanvasMindmapResult> {
  const { sessionId, provider, apiKey } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    [getApiKeyHeader(provider)]: apiKey,
  };

  const url = getApiUrl("/api/canvas/mindmap");

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify({
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to generate mindmap: ${errorText}`);
  }

  return response.json();
}

// Approach Generation API

export interface GenerateApproachesOptions {
  sessionId: string;
  provider: Provider;
  apiKey: string;
}

export interface ApproachTask {
  id: string;
  name: string;
  description: string;
  techStack: string;
  complexity: "Low" | "Medium" | "High";
}

export interface Approach {
  id: string;
  name: string;
  mermaidCode: string;
  tasks: ApproachTask[];
}

export interface ApproachesResult {
  approaches: Approach[];
}

export async function generateApproaches(
  options: GenerateApproachesOptions
): Promise<ApproachesResult> {
  const { sessionId, provider, apiKey } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    [getApiKeyHeader(provider)]: apiKey,
  };

  const url = getApiUrl("/api/canvas/approaches");

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify({ session_id: sessionId }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to generate approaches: ${errorText}`);
  }

  return response.json();
}

export interface RefineApproachOptions {
  sessionId: string;
  provider: Provider;
  apiKey: string;
  approachIndex: number;
  elementId: string;
  elementType: "diagram" | "task";
  refinementAnswer: string;
  currentApproach: Approach;
}

export async function refineApproach(
  options: RefineApproachOptions
): Promise<Approach> {
  const {
    sessionId,
    provider,
    apiKey,
    approachIndex,
    elementId,
    elementType,
    refinementAnswer,
    currentApproach,
  } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    [getApiKeyHeader(provider)]: apiKey,
  };

  const url = getApiUrl("/api/canvas/refine");

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify({
      session_id: sessionId,
      approach_index: approachIndex,
      element_id: elementId,
      element_type: elementType,
      refinement_answer: refinementAnswer,
      current_approach: currentApproach,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to refine approach: ${errorText}`);
  }

  const data = await response.json();
  return data.approach;
}