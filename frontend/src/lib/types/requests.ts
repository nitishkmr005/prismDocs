// API request types matching FastAPI schemas

export type OutputFormat = "pdf" | "pptx";

export type Provider = "gemini" | "google" | "openai" | "anthropic";

export type Audience = "technical" | "executive" | "client" | "educational";

export type ImageStyle =
  | "auto"
  | "infographic"
  | "handwritten"
  | "minimalist"
  | "corporate"
  | "educational"
  | "diagram"
  | "chart"
  | "mermaid"
  | "decorative";

export interface FileSource {
  type: "file";
  file_id: string;
}

export interface UrlSource {
  type: "url";
  url: string;
}

export interface TextSource {
  type: "text";
  content: string;
}

export type SourceItem = FileSource | UrlSource | TextSource;

export interface Preferences {
  audience: Audience;
  image_style: ImageStyle;
  temperature: number;
  max_tokens: number;
  max_slides: number;
  max_summary_points: number;
  image_alignment_retries: number;
}

export interface CacheOptions {
  reuse: boolean;
}

export interface GenerateRequest {
  output_format: OutputFormat;
  sources: SourceItem[];
  provider: Provider;
  model: string;
  image_model: string;
  preferences: Preferences;
  cache: CacheOptions;
}

export const DEFAULT_PREFERENCES: Preferences = {
  audience: "technical",
  image_style: "auto",
  temperature: 0.4,
  max_tokens: 8000,
  max_slides: 10,
  max_summary_points: 5,
  image_alignment_retries: 2,
};

export const DEFAULT_CACHE_OPTIONS: CacheOptions = {
  reuse: true,
};
