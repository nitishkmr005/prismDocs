import { API_CONFIG, getApiUrl } from "@/config/api";
import { UploadResponse } from "@/lib/types/responses";
import { ApiClientError, formatErrorDetail } from "./client";

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(getApiUrl(API_CONFIG.endpoints.upload), {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage =
      formatErrorDetail(errorData.detail) ||
      `Upload failed: ${response.statusText}`;
    throw new ApiClientError(
      errorMessage,
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
