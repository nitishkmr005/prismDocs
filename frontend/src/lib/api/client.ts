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
    throw new ApiClientError(
      errorData.detail || `API request failed: ${response.statusText}`,
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
      return "X-Gemini-Api-Key";
    case "openai":
      return "X-OpenAI-Api-Key";
    case "anthropic":
      return "X-Anthropic-Api-Key";
    default:
      return "X-Api-Key";
  }
}

export async function checkHealth() {
  return apiRequest<{ status: string; version: string }>(
    API_CONFIG.endpoints.health
  );
}
