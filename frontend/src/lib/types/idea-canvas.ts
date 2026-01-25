// frontend/src/lib/types/idea-canvas.ts

import { Provider } from "./requests";

export type CanvasTemplate =
  | "startup"
  | "web_app"
  | "ai_agent"
  | "project_spec"
  | "tech_stack"
  | "custom"
  // Developer-focused templates
  | "implement_feature"
  | "solve_problem"
  | "performance"
  | "scaling"
  | "security_review"
  | "code_architecture";

export type QuestionType = "single_choice" | "multi_choice" | "text_input" | "approach";

export type CanvasNodeType = "root" | "question" | "answer" | "approach" | "option";

// Request types

export interface StartCanvasRequest {
  template: CanvasTemplate;
  idea: string;
  provider: Provider;
  model: string;
}

export interface AnswerRequest {
  session_id: string;
  question_id: string;
  answer: string | string[];
}

// Response types

export interface QuestionOption {
  id: string;
  label: string;
  description?: string;
  recommended?: boolean;
}

export interface ApproachOption {
  id: string;
  title: string;
  description: string;
  pros: string[];
  cons: string[];
  recommended?: boolean;
}

export interface CanvasQuestion {
  id: string;
  question: string;
  type: QuestionType;
  options: QuestionOption[];
  approaches: ApproachOption[];
  allow_skip: boolean;
  context?: string;
}

export interface CanvasNode {
  id: string;
  type: CanvasNodeType;
  label: string;
  description?: string;
  children: CanvasNode[];
  // For answer nodes: all available options and which was selected
  options?: QuestionOption[];
  selected_option_id?: string;
}

export interface CanvasState {
  session_id: string;
  idea: string;
  template: CanvasTemplate;
  nodes: CanvasNode;
  question_count: number;
  is_complete: boolean;
}

// Event types

export interface CanvasReadyEvent {
  type: "ready";
  session_id: string;
  canvas: CanvasState;
}

export interface CanvasQuestionEvent {
  type: "question";
  question: CanvasQuestion;
  canvas: CanvasState;
}

export interface CanvasProgressEvent {
  type: "progress";
  message: string;
}

export interface CanvasCompleteEvent {
  type: "suggest_complete";
  message: string;
  canvas: CanvasState;
}

export interface CanvasErrorEvent {
  type: "error";
  message: string;
  code?: string;
}

export type CanvasEvent =
  | CanvasReadyEvent
  | CanvasQuestionEvent
  | CanvasProgressEvent
  | CanvasCompleteEvent
  | CanvasErrorEvent;

// Type guards

export function isCanvasReadyEvent(event: CanvasEvent): event is CanvasReadyEvent {
  return event.type === "ready";
}

export function isCanvasQuestionEvent(event: CanvasEvent): event is CanvasQuestionEvent {
  return event.type === "question";
}

export function isCanvasProgressEvent(event: CanvasEvent): event is CanvasProgressEvent {
  return event.type === "progress";
}

export function isCanvasCompleteEvent(event: CanvasEvent): event is CanvasCompleteEvent {
  return event.type === "suggest_complete";
}

export function isCanvasErrorEvent(event: CanvasEvent): event is CanvasErrorEvent {
  return event.type === "error";
}

// Template metadata for UI

export interface TemplateInfo {
  id: CanvasTemplate;
  title: string;
  description: string;
  icon: string;
  color: string;
}

export const CANVAS_TEMPLATES: TemplateInfo[] = [
  {
    id: "startup",
    title: "Startup Planning",
    description: "Plan your MVP, GTM strategy, and funding approach",
    icon: "rocket",
    color: "from-orange-500 to-amber-500",
  },
  {
    id: "web_app",
    title: "Web App Architecture",
    description: "Design tech stack, components, and infrastructure",
    icon: "code",
    color: "from-blue-500 to-cyan-500",
  },
  {
    id: "ai_agent",
    title: "AI Agent System",
    description: "Design agents, tools, and orchestration patterns",
    icon: "bot",
    color: "from-purple-500 to-violet-500",
  },
  {
    id: "project_spec",
    title: "Project Spec",
    description: "Define requirements, milestones, and deliverables",
    icon: "clipboard",
    color: "from-green-500 to-emerald-500",
  },
  {
    id: "tech_stack",
    title: "Tech Stack Decisions",
    description: "Compare options and make informed technology choices",
    icon: "layers",
    color: "from-indigo-500 to-blue-500",
  },
  // Developer-focused templates
  {
    id: "implement_feature",
    title: "Implement a Feature",
    description: "Plan implementation from requirements to code",
    icon: "wrench",
    color: "from-teal-500 to-cyan-500",
  },
  {
    id: "solve_problem",
    title: "Solve a Problem",
    description: "Explore different approaches with trade-offs",
    icon: "lightbulb",
    color: "from-yellow-500 to-orange-500",
  },
  {
    id: "performance",
    title: "Performance Optimization",
    description: "Diagnose bottlenecks and plan improvements",
    icon: "zap",
    color: "from-red-500 to-orange-500",
  },
  {
    id: "scaling",
    title: "Scale a System",
    description: "Plan horizontal/vertical scaling strategies",
    icon: "trending-up",
    color: "from-blue-500 to-indigo-500",
  },
  {
    id: "security_review",
    title: "Security Review",
    description: "Audit security posture and plan hardening",
    icon: "shield",
    color: "from-slate-500 to-zinc-600",
  },
  {
    id: "code_architecture",
    title: "Code Architecture",
    description: "Design or refactor codebase structure",
    icon: "folder-tree",
    color: "from-violet-500 to-purple-500",
  },
];

// Report Generation Types

export interface GenerateReportRequest {
  session_id: string;
  output_format: "pdf" | "markdown" | "both";
}

export interface GenerateReportResponse {
  session_id: string;
  title: string;
  pdf_url?: string;
  pdf_base64?: string;  // Base64-encoded PDF data
  markdown_url?: string;
  markdown_content?: string;
}

// Approach Panel Types

export interface ApproachTask {
  id: string;
  name: string;
  description: string;
  techStack: string;
  complexity: 'Low' | 'Medium' | 'High';
}

export interface Approach {
  id: string;
  name: string;
  mermaidCode: string;
  tasks: ApproachTask[];
}

export interface ApproachesResponse {
  approaches: Approach[];
}

export interface RefinementTarget {
  approachIndex: number;
  elementId: string;
  elementType: 'diagram' | 'task';
}

export interface RefinementQuestion {
  id: string;
  question: string;
  options: QuestionOption[];
  targetApproach: number;
  targetElement: string;
}

// Canvas phase type
export type CanvasPhase = 'understanding' | 'approaches' | 'refining';

