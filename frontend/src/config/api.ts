export const API_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  endpoints: {
    health: "/api/health",
    upload: "/api/upload",
    generate: "/api/generate",
    download: (filePath: string) => `/api/download/${filePath}`,
  },
} as const;

export function getApiUrl(endpoint: string): string {
  return `${API_CONFIG.baseUrl}${endpoint}`;
}

export function getDownloadUrl(filePath: string): string {
  return getApiUrl(API_CONFIG.endpoints.download(filePath));
}
