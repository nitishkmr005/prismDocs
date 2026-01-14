"use client";

import { useState, useCallback } from "react";
import { uploadFile as uploadFileApi } from "@/lib/api/upload";
import { UploadResponse } from "@/lib/types/responses";

export interface UploadedFile {
  file: File;
  fileId: string;
  filename: string;
  size: number;
  mimeType: string;
}

export interface UseUploadResult {
  uploading: boolean;
  uploadedFiles: UploadedFile[];
  error: string | null;
  uploadFile: (file: File) => Promise<UploadedFile | null>;
  uploadFiles: (files: File[]) => Promise<UploadedFile[]>;
  removeFile: (fileId: string) => void;
  reset: () => void;
}

export function useUpload(): UseUploadResult {
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setUploading(false);
    setUploadedFiles([]);
    setError(null);
  }, []);

  const uploadFile = useCallback(async (file: File): Promise<UploadedFile | null> => {
    setUploading(true);
    setError(null);

    try {
      const response: UploadResponse = await uploadFileApi(file);
      const uploaded: UploadedFile = {
        file,
        fileId: response.file_id,
        filename: response.filename,
        size: response.size,
        mimeType: response.mime_type,
      };
      setUploadedFiles((prev) => [...prev, uploaded]);
      return uploaded;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      return null;
    } finally {
      setUploading(false);
    }
  }, []);

  const uploadFiles = useCallback(
    async (files: File[]): Promise<UploadedFile[]> => {
      setUploading(true);
      setError(null);

      const results: UploadedFile[] = [];

      for (const file of files) {
        try {
          const response: UploadResponse = await uploadFileApi(file);
          const uploaded: UploadedFile = {
            file,
            fileId: response.file_id,
            filename: response.filename,
            size: response.size,
            mimeType: response.mime_type,
          };
          results.push(uploaded);
          setUploadedFiles((prev) => [...prev, uploaded]);
        } catch (err) {
          setError(err instanceof Error ? err.message : `Failed to upload ${file.name}`);
        }
      }

      setUploading(false);
      return results;
    },
    []
  );

  const removeFile = useCallback((fileId: string) => {
    setUploadedFiles((prev) => prev.filter((f) => f.fileId !== fileId));
  }, []);

  return {
    uploading,
    uploadedFiles,
    error,
    uploadFile,
    uploadFiles,
    removeFile,
    reset,
  };
}
