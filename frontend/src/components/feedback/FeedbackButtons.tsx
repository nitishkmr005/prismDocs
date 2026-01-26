"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { FeedbackModal } from "./FeedbackModal";

interface FeedbackButtonsProps {
  contentType: "document" | "image" | "mindmap" | "podcast" | "faq";
  outputFormat?: string;
  userId?: string;
  metadata?: Record<string, any>;
}

export function FeedbackButtons({
  contentType,
  outputFormat,
  userId,
  metadata,
}: FeedbackButtonsProps) {
  const [feedbackGiven, setFeedbackGiven] = useState<"like" | "dislike" | null>(null);
  const [showTextFeedbackModal, setShowTextFeedbackModal] = useState(false);

  const handleFeedback = async (type: "like" | "dislike") => {
    // Import dynamically
    const { logContentFeedback } = await import("@/lib/supabase/feedback");
    
    await logContentFeedback({
      content_type: contentType,
      output_format: outputFormat,
      feedback_type: type,
      user_id: userId,
      generation_metadata: metadata,
    });
    
    setFeedbackGiven(type);
    
    // Reset after 3 seconds
    setTimeout(() => setFeedbackGiven(null), 3000);
  };

  return (
    <>
      <div className="flex items-center gap-2 pt-2 flex-wrap">
        <span className="text-sm text-muted-foreground">Was this helpful?</span>
        <div className="flex gap-1">
          <Button
            size="sm"
            variant={feedbackGiven === "like" ? "default" : "ghost"}
            className={feedbackGiven === "like" ? "bg-green-600 hover:bg-green-600" : ""}
            onClick={() => handleFeedback("like")}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"
              />
            </svg>
          </Button>
          <Button
            size="sm"
            variant={feedbackGiven === "dislike" ? "default" : "ghost"}
            className={feedbackGiven === "dislike" ? "bg-red-600 hover:bg-red-600" : ""}
            onClick={() => handleFeedback("dislike")}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5"
              />
            </svg>
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setShowTextFeedbackModal(true)}
            className="ml-2"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
              />
            </svg>
            Give Feedback
          </Button>
        </div>
        {feedbackGiven && (
          <span className="text-sm text-muted-foreground animate-in fade-in">
            Thanks for your feedback!
          </span>
        )}
      </div>

      <FeedbackModal
        isOpen={showTextFeedbackModal}
        onClose={() => setShowTextFeedbackModal(false)}
        contentType={contentType}
        outputFormat={outputFormat}
        userId={userId}
        metadata={metadata}
      />
    </>
  );
}
