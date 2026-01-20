// Podcast generation types

export type PodcastStyle = 
  | "conversational" 
  | "interview" 
  | "educational" 
  | "debate" 
  | "storytelling";

export type VoiceName = 
  | "Kore"    // Male voice
  | "Puck"    // Female voice
  | "Charon"  // Deep male voice
  | "Fenrir"  // Energetic male voice
  | "Aoede"   // Warm female voice
  | "Leda";   // Professional female voice

export interface SpeakerConfig {
  name: string;
  voice: VoiceName;
  role: string;
}

export interface PodcastRequest {
  sources: Array<
    | { type: "file"; file_id: string }
    | { type: "url"; url: string }
    | { type: "text"; content: string }
  >;
  style: PodcastStyle;
  provider: "gemini" | "google" | "openai" | "anthropic";
  model: string;
  speakers: SpeakerConfig[];
  duration_minutes: number;
}

// SSE Event types
export interface PodcastProgressEvent {
  type: "progress";
  stage: string;
  percent: number;
  message?: string;
}

export interface PodcastCompleteEvent {
  type: "complete";
  title: string;
  description: string;
  audio_base64: string;
  script: Array<{ speaker: string; text: string }>;
  duration_seconds: number;
}

export interface PodcastErrorEvent {
  type: "error";
  message: string;
  code?: string;
}

export type PodcastEvent = PodcastProgressEvent | PodcastCompleteEvent | PodcastErrorEvent;

// Type guards
export function isPodcastProgressEvent(event: PodcastEvent): event is PodcastProgressEvent {
  return event.type === "progress";
}

export function isPodcastCompleteEvent(event: PodcastEvent): event is PodcastCompleteEvent {
  return event.type === "complete";
}

export function isPodcastErrorEvent(event: PodcastEvent): event is PodcastErrorEvent {
  return event.type === "error";
}

// Voice options for UI
export const VOICE_OPTIONS: Array<{ value: VoiceName; label: string; description: string }> = [
  { value: "Kore", label: "Kore", description: "Male voice" },
  { value: "Puck", label: "Puck", description: "Female voice" },
  { value: "Charon", label: "Charon", description: "Deep male voice" },
  { value: "Fenrir", label: "Fenrir", description: "Energetic male voice" },
  { value: "Aoede", label: "Aoede", description: "Warm female voice" },
  { value: "Leda", label: "Leda", description: "Professional female voice" },
];

// Style options for UI
export const PODCAST_STYLE_OPTIONS: Array<{
  value: PodcastStyle;
  label: string;
  icon: string;
  description: string;
}> = [
  {
    value: "conversational",
    label: "Casual Chat",
    icon: "💬",
    description: "Friendly discussion between hosts",
  },
  {
    value: "interview",
    label: "Interview",
    icon: "🎤",
    description: "Host interviewing an expert",
  },
  {
    value: "educational",
    label: "Educational",
    icon: "📚",
    description: "Teaching/explaining the topic",
  },
  {
    value: "debate",
    label: "Debate",
    icon: "⚖️",
    description: "Two opposing viewpoints",
  },
  {
    value: "storytelling",
    label: "Storytelling",
    icon: "📖",
    description: "Narrative-driven discussion",
  },
];

// Default speakers
export const DEFAULT_SPEAKERS: SpeakerConfig[] = [
  { name: "Alex", voice: "Kore", role: "host" },
  { name: "Sam", voice: "Puck", role: "co-host" },
];
