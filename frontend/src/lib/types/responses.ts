// API response types matching FastAPI schemas

export type GenerationStatus =
  | "parsing"
  | "transforming"
  | "generating_images"
  | "generating_output"
  | "uploading"
  | "complete"
  | "cache_hit"
  | "error";

export interface ProgressEvent {
  status: GenerationStatus;
  progress: number;
  message?: string;
}

export interface CompletionMetadata {
  title: string;
  pages: number;
  slides: number;
  images_generated: number;
}

export interface CompleteEvent {
  status: "complete";
  progress: 100;
  download_url: string;
  file_path: string;
  expires_in: number;
  metadata: CompletionMetadata;
}

export interface CacheHitEvent {
  status: "cache_hit";
  progress: 100;
  download_url: string;
  file_path: string;
  expires_in: number;
  cached_at: string;
}

export interface ErrorEvent {
  status: "error";
  error: string;
  code: string;
}

export type GenerationEvent =
  | ProgressEvent
  | CompleteEvent
  | CacheHitEvent
  | ErrorEvent;

export interface UploadResponse {
  file_id: string;
  filename: string;
  size: number;
  mime_type: string;
  expires_in: number;
}

export interface HealthResponse {
  status: string;
  version: string;
}

export function isCompleteEvent(event: GenerationEvent): event is CompleteEvent {
  return event.status === "complete";
}

export function isCacheHitEvent(event: GenerationEvent): event is CacheHitEvent {
  return event.status === "cache_hit";
}

export function isErrorEvent(event: GenerationEvent): event is ErrorEvent {
  return event.status === "error";
}

export function isProgressEvent(event: GenerationEvent): event is ProgressEvent {
  return !isCompleteEvent(event) && !isCacheHitEvent(event) && !isErrorEvent(event);
}
