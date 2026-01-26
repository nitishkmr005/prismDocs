// FAQ document types for the frontend.

import type { Provider, SourceItem } from "./requests";

export interface FAQRequest {
  sources: SourceItem[];
  provider: Provider;
  model: string;
}

export interface FAQItem {
  id: string;
  question: string;
  answer: string;
  tags: string[];
}

export interface FAQMetadata {
  source_count: number;
  generated_at: string;
  tag_colors: Record<string, string>;
}

export interface FAQDocument {
  title: string;
  description?: string | null;
  items: FAQItem[];
  metadata: FAQMetadata;
}

export interface FAQProgressEvent {
  type: "progress";
  stage: string;
  percent: number;
  message?: string;
}

export interface FAQCompleteEvent {
  type: "complete";
  document: FAQDocument;
  download_url: string;
  file_path: string;
  session_id?: string | null;
}

export interface FAQErrorEvent {
  type: "error";
  message: string;
  code?: string;
}

export type FAQEvent = FAQProgressEvent | FAQCompleteEvent | FAQErrorEvent;

export function isFAQProgressEvent(event: FAQEvent): event is FAQProgressEvent {
  return event.type === "progress";
}

export function isFAQCompleteEvent(event: FAQEvent): event is FAQCompleteEvent {
  return event.type === "complete";
}

export function isFAQErrorEvent(event: FAQEvent): event is FAQErrorEvent {
  return event.type === "error";
}

export const TAG_GRADIENTS: Record<string, string> = {
  "blue-cyan": "from-blue-500 to-cyan-400",
  "purple-pink": "from-purple-500 to-pink-400",
  "orange-amber": "from-orange-500 to-amber-400",
  "green-teal": "from-emerald-500 to-teal-400",
  "rose-red": "from-rose-500 to-red-400",
  "indigo-violet": "from-indigo-500 to-violet-400",
  "yellow-lime": "from-yellow-400 to-lime-400",
  "slate-gray": "from-slate-500 to-gray-400",
};
