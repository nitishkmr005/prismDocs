import { getSupabase } from "./client";

export interface ContentFeedback {
  content_type: "document" | "image" | "mindmap" | "podcast" | "faq";
  output_format?: string; // pdf, pptx, markdown, png, svg, etc.
  feedback_type: "like" | "dislike" | "comment";
  user_id?: string;
  generation_metadata?: Record<string, any>;
}

/**
 * Log content feedback (like/dislike) to Supabase
 */
export async function logContentFeedback(feedback: ContentFeedback): Promise<boolean> {
  try {
    const supabase = getSupabase();
    if (!supabase) {
      console.warn("Supabase not configured, skipping feedback logging");
      return false;
    }

    const { error } = await supabase.from("content_feedback").insert({
      content_type: feedback.content_type,
      output_format: feedback.output_format || null,
      feedback_type: feedback.feedback_type,
      user_id: feedback.user_id || null,
      generation_metadata: feedback.generation_metadata || {},
      created_at: new Date().toISOString(),
    });

    if (error) {
      console.error("Error logging content feedback:", error);
      return false;
    }

    return true;
  } catch (error) {
    console.error("Exception logging content feedback:", error);
    return false;
  }
}
