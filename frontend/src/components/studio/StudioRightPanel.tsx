"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { MindMapViewer } from "@/components/mindmap";
import { MindMapTree } from "@/lib/types/mindmap";
import { FeedbackButtons } from "@/components/feedback/FeedbackButtons";
import { RegionSelector } from "@/components/image/RegionSelector";
import { BeforeAfterView } from "@/components/image/BeforeAfterView";
import { StyleSelector } from "@/components/image/StyleSelector";
import { editImage } from "@/lib/api/image";
import type { Region } from "@/lib/types/image";
import type { StyleCategory } from "@/data/imageStyles";
import { StudioOutputType } from "./OutputTypeSelector";

type GenerationState = "idle" | "generating" | "success" | "error";

interface StudioRightPanelProps {
  outputType: StudioOutputType;
  state: GenerationState;
  progress: number;
  status: string;
  error: string | null;
  // Content outputs
  pdfBase64?: string | null;
  markdownContent?: string | null;
  downloadUrl?: string | null;
  // Image outputs
  imageData?: string | null;
  imageFormat?: "png" | "svg";
  // Mind map outputs
  mindMapTree?: MindMapTree | null;
  // Metadata
  metadata?: {
    title?: string;
    pages?: number;
    slides?: number;
    imagesGenerated?: number;
  } | null;
  // Actions
  onReset: () => void;
  onDownload?: () => void;
  userId?: string;
  // API key for image editing (passed from parent)
  imageApiKey?: string;
}

export function StudioRightPanel({
  outputType,
  state,
  progress,
  status,
  error,
  pdfBase64,
  markdownContent,
  downloadUrl,
  imageData,
  imageFormat,
  mindMapTree,
  metadata,
  onReset,
  onDownload,
  userId,
  imageApiKey,
}: StudioRightPanelProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [markdownCopied, setMarkdownCopied] = useState(false);
  
  // Image editing state
  const [isEditingMode, setIsEditingMode] = useState(false);
  const [editRegion, setEditRegion] = useState<Region | null>(null);
  const [editPrompt, setEditPrompt] = useState("");
  const [editStyleCategory, setEditStyleCategory] = useState<StyleCategory | null>(null);
  const [editStyleId, setEditStyleId] = useState<string | null>(null);
  const [editedImageData, setEditedImageData] = useState<string | null>(null);
  const [isApplyingEdit, setIsApplyingEdit] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  const handleCopyMarkdown = async () => {
    if (!markdownContent) return;
    try {
      await navigator.clipboard.writeText(markdownContent);
      setMarkdownCopied(true);
      setTimeout(() => setMarkdownCopied(false), 1500);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement("textarea");
      textarea.value = markdownContent;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setMarkdownCopied(true);
      setTimeout(() => setMarkdownCopied(false), 1500);
    }
  };

  const handleOpenPdfInNewTab = () => {
    if (!pdfBase64) return;
    const byteCharacters = atob(pdfBase64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: "application/pdf" });
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener,noreferrer");
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  };

  const handleDownloadImage = (data?: string | null, format?: string) => {
    const imgData = data || imageData;
    const imgFormat = format || imageFormat;
    if (!imgData || !imgFormat) return;
    const link = document.createElement("a");
    link.href = `data:image/${imgFormat};base64,${imgData}`;
    link.download = `generated-image.${imgFormat}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleStartEdit = () => {
    setIsEditingMode(true);
    setEditedImageData(null);
    setEditError(null);
  };

  const handleCancelEdit = () => {
    setIsEditingMode(false);
    setEditRegion(null);
    setEditPrompt("");
    setEditStyleCategory(null);
    setEditStyleId(null);
    setEditError(null);
  };

  const handleApplyEdit = async () => {
    if (!imageData || !imageApiKey) {
      setEditError("Missing image data or API key");
      return;
    }
    if (!editPrompt.trim() && !editStyleId) {
      setEditError("Please enter an edit prompt or select a style");
      return;
    }

    setIsApplyingEdit(true);
    setEditError(null);

    try {
      const result = await editImage(
        {
          image: imageData,
          prompt: editPrompt || `Apply ${editStyleId || 'style transfer'}`,
          edit_mode: editRegion ? "region" : editStyleId ? "style_transfer" : "basic",
          style_category: editStyleCategory,
          style: editStyleId,
          region: editRegion,
        },
        imageApiKey
      );

      if (result.success && result.image_data) {
        setEditedImageData(result.image_data);
        setIsEditingMode(false);
      } else {
        setEditError(result.error || "Image editing failed");
      }
    } catch (err) {
      setEditError(err instanceof Error ? err.message : "Image editing failed");
    } finally {
      setIsApplyingEdit(false);
    }
  };

  const handleBackToOriginal = () => {
    setEditedImageData(null);
    setEditRegion(null);
    setEditPrompt("");
    setEditStyleCategory(null);
    setEditStyleId(null);
  };

  // Idle state - customized per output type
  if (state === "idle") {
    // Get output type specific content
    const getIdleContent = () => {
      switch (outputType) {
        case "article_pdf":
        case "article_markdown":
          return { icon: "📄", title: "Ready to Create Article", desc: "Add your sources and generate a polished article in PDF or Markdown format" };
        case "slide_deck_pdf":
        case "presentation_pptx":
          return { icon: "📊", title: "Ready to Create Presentation", desc: "Add your sources and generate a professional slide deck or presentation" };
        case "mindmap":
          return { icon: "🧠", title: "Ready to Create Mind Map", desc: "Add your content and generate an interactive mind map visualization" };
        case "image_generate":
          return { icon: "🎨", title: "Ready to Generate Image", desc: "Describe your image, select a style, and generate stunning visuals" };
        default:
          return { icon: "✨", title: "Ready to Generate", desc: "Configure your options and click Generate to create your content" };
      }
    };

    const { icon, title, desc } = getIdleContent();

    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center p-8 rounded-xl border border-dashed border-border bg-muted/10">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 flex items-center justify-center mb-4">
          <span className="text-4xl">{icon}</span>
        </div>
        <h3 className="text-lg font-semibold text-foreground mb-2">
          {title}
        </h3>
        <p className="text-sm text-muted-foreground max-w-xs">
          {desc}
        </p>
      </div>
    );
  }

  // Generating state
  if (state === "generating") {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center p-8 rounded-xl border bg-card">
        <div className="w-16 h-16 relative mb-6">
          <div className="absolute inset-0 rounded-full border-4 border-muted"></div>
          <div 
            className="absolute inset-0 rounded-full border-4 border-primary border-t-transparent animate-spin"
            style={{ animationDuration: '1s' }}
          ></div>
          <div className="absolute inset-3 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
            <span className="text-sm font-bold text-primary">{Math.round(progress)}%</span>
          </div>
        </div>
        <h3 className="text-lg font-medium mb-2">Generating...</h3>
        <p className="text-sm text-muted-foreground mb-4">{status}</p>
        <div className="w-full max-w-xs h-2 bg-muted rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-primary to-primary/70 transition-all duration-300"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>
    );
  }

  // Error state
  if (state === "error") {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center p-8 rounded-xl border border-red-200 dark:border-red-800 bg-red-50/50 dark:bg-red-950/20">
        <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4">
          <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-red-800 dark:text-red-200 mb-2">Generation Failed</h3>
        <p className="text-sm text-red-600 dark:text-red-300 mb-4 max-w-xs">{error}</p>
        <Button variant="outline" onClick={onReset}>Try Again</Button>
      </div>
    );
  }

  // Success state - render based on output type
  const renderContent = () => {
    // Mind Map
    if (outputType === "mindmap" && mindMapTree) {
      return (
        <div className="h-full">
          <MindMapViewer tree={mindMapTree} onReset={onReset} />
        </div>
      );
    }

    // Image outputs with integrated editing
    if (outputType === "image_generate" && imageData) {
      // Show before/after view if we have an edited image
      if (editedImageData) {
        return (
          <div className="flex flex-col h-full">
            <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/30">
              <span className="text-sm font-medium">Before & After</span>
              <Button variant="ghost" size="sm" onClick={handleBackToOriginal}>
                ← Back to Original
              </Button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <BeforeAfterView
                originalImage={imageData}
                editedImage={editedImageData}
              />
            </div>
            <div className="p-4 border-t flex items-center justify-between gap-2 flex-wrap">
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => handleDownloadImage(imageData, imageFormat)}>
                  Download Original
                </Button>
                <Button variant="default" size="sm" onClick={() => handleDownloadImage(editedImageData, "png")}>
                  Download Edited
                </Button>
              </div>
              {userId && (
                <FeedbackButtons
                  contentType="image"
                  userId={userId}
                />
              )}
            </div>
          </div>
        );
      }

      // Show editing mode UI
      if (isEditingMode) {
        return (
          <div className="flex flex-col h-full">
            <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/30">
              <span className="text-sm font-medium">Edit Image</span>
              <Button variant="ghost" size="sm" onClick={handleCancelEdit}>
                Cancel
              </Button>
            </div>
            <div className="flex-1 overflow-auto p-4 space-y-4">
              {/* Region Selector */}
              <RegionSelector
                imageData={imageData}
                region={editRegion}
                onRegionChange={setEditRegion}
                disabled={isApplyingEdit}
              />

              {/* Style Selector */}
              <div className="space-y-2">
                <Label className="text-sm font-medium">Style Transfer (Optional)</Label>
                <StyleSelector
                  selectedCategory={editStyleCategory}
                  selectedStyle={editStyleId}
                  onCategoryChange={setEditStyleCategory}
                  onStyleChange={setEditStyleId}
                  disabled={isApplyingEdit}
                />
              </div>

              {/* Edit Prompt */}
              <div className="space-y-2">
                <Label htmlFor="edit-prompt" className="text-sm font-medium">Edit Instructions</Label>
                <Textarea
                  id="edit-prompt"
                  placeholder="Describe what changes you want to make..."
                  value={editPrompt}
                  onChange={(e) => setEditPrompt(e.target.value)}
                  disabled={isApplyingEdit}
                  rows={3}
                />
              </div>

              {editError && (
                <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800">
                  <p className="text-sm text-red-600 dark:text-red-300">{editError}</p>
                </div>
              )}
            </div>
            <div className="p-4 border-t flex justify-end gap-2">
              <Button variant="outline" onClick={handleCancelEdit} disabled={isApplyingEdit}>
                Cancel
              </Button>
              <Button onClick={handleApplyEdit} disabled={isApplyingEdit}>
                {isApplyingEdit ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Applying...
                  </>
                ) : (
                  "Apply Edit"
                )}
              </Button>
            </div>
          </div>
        );
      }

      // Normal image view with Edit button
      return (
        <div className="flex flex-col h-full">
          <div className="flex-1 overflow-auto p-4 flex items-center justify-center bg-checkered">
            <img 
              src={`data:image/${imageFormat};base64,${imageData}`}
              alt="Generated image"
              className="max-w-full max-h-full object-contain rounded-lg shadow-lg"
            />
          </div>
          <div className="p-4 border-t flex items-center justify-between gap-2 flex-wrap">
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => handleDownloadImage()}>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download {imageFormat?.toUpperCase()}
              </Button>
              {imageApiKey && (
                <Button variant="secondary" size="sm" onClick={handleStartEdit}>
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Edit Image
                </Button>
              )}
            </div>
            {userId && (
              <FeedbackButtons
                contentType="image"
                userId={userId}
              />
            )}
          </div>
        </div>
      );
    }

    // Markdown output
    if (outputType === "article_markdown" && markdownContent) {
      return (
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/30">
            <span className="text-xs font-medium text-muted-foreground">Markdown Preview</span>
            <div className="flex gap-2">
              <Button 
                size="sm" 
                variant="ghost" 
                onClick={handleCopyMarkdown} 
                className={`h-7 text-xs transition-all ${markdownCopied ? 'copy-glow' : ''}`}
              >
                {markdownCopied ? (
                  <>
                    <svg className="w-3.5 h-3.5 mr-1 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Copied!
                  </>
                ) : (
                  <>
                    <svg className="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copy
                  </>
                )}
              </Button>
              {onDownload && (
                <Button size="sm" variant="outline" onClick={onDownload} className="h-7 text-xs">
                  <svg className="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download
                </Button>
              )}
            </div>
          </div>
          <div className="flex-1 overflow-auto p-4">
            <pre className="text-sm font-mono whitespace-pre-wrap text-muted-foreground leading-relaxed">
              {markdownContent}
            </pre>
          </div>
          {userId && (
            <div className="p-3 border-t flex justify-end">
              <FeedbackButtons
                contentType="document"
                userId={userId}
              />
            </div>
          )}
        </div>
      );
    }

    // PDF outputs (article_pdf, slide_deck_pdf, presentation_pptx)
    if (pdfBase64) {
      return (
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/30">
            <span className="text-xs font-medium text-muted-foreground">
              {metadata?.title || "Document Preview"}
              {metadata?.pages && ` • ${metadata.pages} pages`}
              {metadata?.slides && ` • ${metadata.slides} slides`}
            </span>
            <div className="flex gap-2">
              <Button size="sm" variant="ghost" onClick={handleOpenPdfInNewTab} className="h-7 text-xs">
                <svg className="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                Open
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setIsFullscreen(true)} className="h-7 text-xs">
                <svg className="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
                Fullscreen
              </Button>
              {onDownload && (
                <Button size="sm" variant="outline" onClick={onDownload} className="h-7 text-xs">
                  <svg className="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download
                </Button>
              )}
            </div>
          </div>
          <div className="flex-1 min-h-0">
            <iframe
              src={`data:application/pdf;base64,${pdfBase64}#view=FitH&zoom=page-width`}
              className="w-full h-full border-0"
              title="PDF Preview"
            />
          </div>
          {userId && (
            <div className="p-3 border-t flex justify-end">
              <FeedbackButtons
                contentType="document"
                userId={userId}
              />
            </div>
          )}
        </div>
      );
    }

    // Download URL fallback
    if (downloadUrl) {
      return (
        <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center p-8">
          <div className="w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-lg font-medium mb-2">Generation Complete!</h3>
          {metadata?.title && (
            <p className="text-sm text-muted-foreground mb-4">{metadata.title}</p>
          )}
          <Button asChild>
            <a href={downloadUrl} download>
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download
            </a>
          </Button>
        </div>
      );
    }

    return null;
  };

  return (
    <>
      <div className="flex flex-col h-full rounded-xl border bg-card overflow-hidden">
        {renderContent()}
      </div>

      {/* Fullscreen Modal */}
      {isFullscreen && pdfBase64 && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="relative w-full h-full max-w-6xl bg-white rounded-lg overflow-hidden">
            <div className="absolute top-4 right-4 z-10 flex gap-2">
              <Button size="sm" variant="secondary" onClick={() => setIsFullscreen(false)}>
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Close
              </Button>
            </div>
            <iframe
              src={`data:application/pdf;base64,${pdfBase64}#view=FitH`}
              className="w-full h-full border-0"
              title="PDF Fullscreen"
            />
          </div>
        </div>
      )}
    </>
  );
}
