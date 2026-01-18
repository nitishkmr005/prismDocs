// frontend/src/lib/types/mindmap.ts

export type MindMapMode = "summarize" | "brainstorm" | "structure";

export interface MindMapNode {
  id: string;
  label: string;
  children?: MindMapNode[];
}

export interface MindMapTree {
  title: string;
  summary: string;
  source_count: number;
  mode: MindMapMode;
  nodes: MindMapNode;
}

export interface MindMapRequest {
  sources: import("./requests").SourceItem[];
  mode: MindMapMode;
  provider: import("./requests").Provider;
  model: string;
  max_depth?: number;
}

export interface MindMapProgressEvent {
  status: "parsing" | "generating" | "complete" | "error";
  progress: number;
  message?: string;
}

export interface MindMapCompleteEvent {
  status: "complete";
  progress: 100;
  tree: MindMapTree;
}

export interface MindMapErrorEvent {
  status: "error";
  error: string;
  code?: string;
}

export type MindMapEvent = MindMapProgressEvent | MindMapCompleteEvent | MindMapErrorEvent;

export function isCompleteEvent(event: MindMapEvent): event is MindMapCompleteEvent {
  return event.status === "complete" && "tree" in event;
}

export function isErrorEvent(event: MindMapEvent): event is MindMapErrorEvent {
  return event.status === "error" && "error" in event;
}
