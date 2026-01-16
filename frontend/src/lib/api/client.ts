import { API_CONFIG, getApiUrl } from "@/config/api";

export class ApiClientError extends Error {
  constructor(
    message: string,
    public code?: string,
    public status?: number
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

export interface RequestOptions extends RequestInit {
  apiKey?: string;
  provider?: string;
}

export function formatErrorDetail(detail: unknown): string | undefined {
  if (!detail) {
    return undefined;
  }
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!item || typeof item !== "object") {
          return undefined;
        }
        const record = item as { loc?: unknown; msg?: unknown };
        const loc =
          Array.isArray(record.loc) && record.loc.length > 0
            ? record.loc.join(".")
            : undefined;
        const msg = typeof record.msg === "string" ? record.msg : undefined;
        if (loc && msg) {
          return `${loc}: ${msg}`;
        }
        if (msg) {
          return msg;
        }
        return undefined;
      })
      .filter((message): message is string => Boolean(message));

    if (messages.length > 0) {
      return messages.join("; ");
    }
  }
  if (typeof detail === "object") {
    try {
      return JSON.stringify(detail);
    } catch {
      return "Request failed with an unknown error.";
    }
  }
  return String(detail);
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { apiKey, provider, ...fetchOptions } = options;

  const headers: HeadersInit = {
    ...(options.headers || {}),
  };

  if (apiKey && provider) {
    const headerKey = getApiKeyHeader(provider);
    (headers as Record<string, string>)[headerKey] = apiKey;
  }

  if (options.body && !(options.body instanceof FormData)) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
  }

  const response = await fetch(getApiUrl(endpoint), {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage =
      formatErrorDetail(errorData.detail) ||
      `API request failed: ${response.statusText}`;
    throw new ApiClientError(
      errorMessage,
      errorData.code,
      response.status
    );
  }

  return response.json();
}

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

export async function checkHealth() {
  return apiRequest<{ status: string; version: string }>(
    API_CONFIG.endpoints.health
  );
}
