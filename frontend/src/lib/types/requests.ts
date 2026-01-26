// API request types matching FastAPI schemas

export type OutputFormat = "pdf" | "pptx" | "markdown" | "pdf_from_pptx";

export type Provider = "gemini" | "google" | "openai" | "anthropic";

export type Audience = "technical" | "executive" | "client" | "educational" | "creator";

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

export type UrlParser = "markitdown" | "firecrawl" | "auto";

export interface FileSource {
  type: "file";
  file_id: string;
}

export interface UrlSource {
  type: "url";
  url: string;
  parser?: UrlParser;
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
  enable_image_generation: boolean;
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
  image_style: "handwritten",
  temperature: 0.4,
  max_tokens: 12000,
  max_slides: 25,
  max_summary_points: 5,
  enable_image_generation: true,
};

export const DEFAULT_CACHE_OPTIONS: CacheOptions = {
  reuse: true,
};
