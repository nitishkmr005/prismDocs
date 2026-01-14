import { API_CONFIG, getApiUrl } from "@/config/api";
import { UploadResponse } from "@/lib/types/responses";
import { ApiClientError } from "./client";

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(getApiUrl(API_CONFIG.endpoints.upload), {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiClientError(
      errorData.detail || `Upload failed: ${response.statusText}`,
      errorData.code,
      response.status
    );
  }

  return response.json();
}

export async function uploadMultipleFiles(
  files: File[]
): Promise<UploadResponse[]> {
  return Promise.all(files.map(uploadFile));
}
