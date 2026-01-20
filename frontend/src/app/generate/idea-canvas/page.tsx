"use client";

import { useCallback, useState } from "react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { IdeaCanvasForm, IdeaCanvas, QuestionCard } from "@/components/idea-canvas";
import { MindMapViewer } from "@/components/mindmap";
import { useIdeaCanvas } from "@/hooks/useIdeaCanvas";
import { useAuth } from "@/hooks/useAuth";
import { AuthModal } from "@/components/auth/AuthModal";
import { StartCanvasRequest } from "@/lib/types/idea-canvas";
import { generateCanvasReport, generateCanvasMindmap, CanvasMindmapResult } from "@/lib/api/idea-canvas";
import { generateImage, downloadImage } from "@/lib/api/image";

export default function IdeaCanvasPage() {
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);

  const {
    state: canvasState,
    sessionId: canvasSessionId,
    canvas,
    currentQuestion,
    questionHistory,
    progressMessage: canvasProgressMessage,
    error: canvasError,
    provider: canvasProvider,
    apiKey: canvasApiKey,
    imageApiKey: canvasImageApiKey,
    includeReportImage,
    canGoBack,
    start: startCanvas,
    answer: submitCanvasAnswer,
    goBack: goBackCanvas,
    reset: resetCanvas,
  } = useIdeaCanvas();

  // Report generation state
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [reportData, setReportData] = useState<{
    title: string;
    markdown_content: string;
    pdf_base64?: string;
    image_base64?: string;
    image_format?: "png" | "svg";
  } | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);
  const [exitedToSummary, setExitedToSummary] = useState(false);
  const [markdownCopied, setMarkdownCopied] = useState(false);

  // Image generation from report state
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [generatedImage, setGeneratedImage] = useState<{ data: string; format: string } | null>(null);
  const [imageGenError, setImageGenError] = useState<string | null>(null);

  // Canvas mind map state
  const [canvasMindMap, setCanvasMindMap] = useState<CanvasMindmapResult | null>(null);
  const [isGeneratingCanvasMindMap, setIsGeneratingCanvasMindMap] = useState(false);
  const [canvasMindMapError, setCanvasMindMapError] = useState<string | null>(null);

  const handleExitToSummary = useCallback(() => {
    setExitedToSummary(true);
  }, []);

  const handleCanvasSubmit = useCallback(
    (
      request: StartCanvasRequest,
      contentApiKey: string,
      imageApiKey: string | null,
      includeImage: boolean
    ) => {
      startCanvas(request, contentApiKey, imageApiKey, includeImage, user?.id);
    },
    [startCanvas, user?.id]
  );

  const handleCanvasAnswer = useCallback(
    (answer: string | string[]) => {
      submitCanvasAnswer(answer, user?.id);
    },
    [submitCanvasAnswer, user?.id]
  );

  const handleGenerateCanvasMindMap = useCallback(async () => {
    if (!canvasSessionId || !canvasApiKey) return;

    setIsGeneratingCanvasMindMap(true);
    setCanvasMindMapError(null);

    try {
      const result = await generateCanvasMindmap({
        sessionId: canvasSessionId,
        provider: canvasProvider,
        apiKey: canvasApiKey,
      });
      setCanvasMindMap(result);
    } catch (err) {
      setCanvasMindMapError(err instanceof Error ? err.message : "Failed to generate mind map");
    } finally {
      setIsGeneratingCanvasMindMap(false);
    }
  }, [canvasSessionId, canvasApiKey, canvasProvider]);

  const generateImageFromReportContent = useCallback(
    async (reportTitle: string, reportMarkdown: string) => {
      if (!canvasImageApiKey) {
        setImageGenError("No image API key available");
        return;
      }

      setIsGeneratingImage(true);
      setImageGenError(null);
      setGeneratedImage(null);

      try {
        const summaryPrompt = `Create a beautiful hand-drawn style infographic that visually summarizes this implementation plan:

Title: ${reportTitle}

Key points to visualize:
${reportMarkdown.slice(0, 1500)}

Style: Hand-drawn, sketch-like, warm colors, clean whiteboard aesthetic with icons and arrows connecting concepts. Include the main title at the top.`;

        const result = await generateImage(
          {
            prompt: summaryPrompt,
            style_category: "handwritten_and_human",
            style: "whiteboard_handwritten",
            output_format: "raster",
            free_text_mode: false,
          },
          canvasImageApiKey
        );

        if (result.success && result.image_data) {
          setGeneratedImage({
            data: result.image_data,
            format: result.format,
          });
        } else {
          setImageGenError(result.error || "Failed to generate image");
        }
      } catch (err) {
        setImageGenError(err instanceof Error ? err.message : "Image generation failed");
      } finally {
        setIsGeneratingImage(false);
      }
    },
    [canvasImageApiKey]
  );

  const handleGenerateReport = useCallback(async () => {
    if (!canvasSessionId || !canvasApiKey) {
      setReportError("No active canvas session");
      return;
    }
    if (includeReportImage && !canvasImageApiKey) {
      setReportError("Missing image API key for report image");
      return;
    }

    setIsGeneratingReport(true);
    setReportError(null);
    setImageGenError(null);
    setMarkdownCopied(false);
    setGeneratedImage(null);

    try {
      const reportImageApiKey = includeReportImage ? canvasImageApiKey : undefined;
      const result = await generateCanvasReport({
        sessionId: canvasSessionId,
        outputFormat: "both",
        provider: canvasProvider,
        apiKey: canvasApiKey,
        imageApiKey: reportImageApiKey,
      });

      setReportData({
        title: result.title,
        markdown_content: result.markdown_content || "",
        pdf_base64: result.pdf_base64,
        image_base64: result.image_base64,
        image_format: result.image_format,
      });
      if (result.image_base64 && result.image_format) {
        setGeneratedImage({
          data: result.image_base64,
          format: result.image_format,
        });
      } else if (includeReportImage) {
        void generateImageFromReportContent(result.title, result.markdown_content || "");
      }
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "Failed to generate report");
    } finally {
      setIsGeneratingReport(false);
    }
  }, [
    canvasSessionId,
    canvasApiKey,
    canvasProvider,
    canvasImageApiKey,
    includeReportImage,
    generateImageFromReportContent,
  ]);

  const handleDownloadMarkdown = useCallback(() => {
    if (!reportData) return;

    const blob = new Blob([reportData.markdown_content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${reportData.title.replace(/[^a-z0-9]/gi, "_").toLowerCase()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [reportData]);

  const createPdfBlob = useCallback((pdfBase64: string) => {
    const byteCharacters = atob(pdfBase64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: "application/pdf" });
  }, []);

  const handleDownloadPdf = useCallback(() => {
    if (!reportData?.pdf_base64) return;

    const blob = createPdfBlob(reportData.pdf_base64);

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${reportData.title.replace(/[^a-z0-9]/gi, "_").toLowerCase()}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [reportData, createPdfBlob]);

  const handleOpenPdfPreview = useCallback(() => {
    if (!reportData?.pdf_base64) return;

    const blob = createPdfBlob(reportData.pdf_base64);
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener,noreferrer");
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }, [reportData, createPdfBlob]);

  const handleCopyMarkdown = useCallback(async () => {
    if (!reportData?.markdown_content) return;

    try {
      await navigator.clipboard.writeText(reportData.markdown_content);
      setMarkdownCopied(true);
      setTimeout(() => setMarkdownCopied(false), 1500);
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = reportData.markdown_content;
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
  }, [reportData]);

  const isCanvasStarting = canvasState === "starting";
  const isCanvasAnswering = canvasState === "answering";

  // Check if canvas is in workspace mode
  const isCanvasWorkspace =
    canvasState === "suggest_complete" || reportData || exitedToSummary;

  // Form view - show when idle or starting
  if (canvasState === "idle" || canvasState === "starting") {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white dark:from-slate-950 dark:to-slate-900">
        <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />

        <header className="border-b bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm sticky top-0 z-40">
          <div className="container mx-auto px-4 h-14 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <a href="/generate" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Studio
              </a>
              <div className="h-6 w-px bg-border" />
              <span className="font-bold text-lg">Idea Canvas</span>
            </div>
            {!authLoading && !isAuthenticated && (
              <Button size="sm" onClick={() => setShowAuthModal(true)}>
                Sign In
              </Button>
            )}
          </div>
        </header>

        <main className="container mx-auto px-4 py-8">
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <div className="inline-flex items-center rounded-full border px-4 py-1.5 text-sm font-medium bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300 mb-4">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Guided Exploration
              </div>
              <h1 className="text-3xl font-bold mb-2">Idea Canvas</h1>
              <p className="text-muted-foreground">
                Explore your idea through guided Q&A and get implementation specs
              </p>
            </div>

            <IdeaCanvasForm onSubmit={handleCanvasSubmit} isStarting={isCanvasStarting} />
          </div>
        </main>
      </div>
    );
  }

  // Error view
  if (canvasState === "error") {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white dark:from-slate-950 dark:to-slate-900">
        <header className="border-b bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm sticky top-0 z-40">
          <div className="container mx-auto px-4 h-14 flex items-center">
            <a href="/generate" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Studio
            </a>
          </div>
        </header>

        <main className="container mx-auto px-4 py-8">
          <div className="max-w-md mx-auto">
            <div className="flex flex-col items-center justify-center min-h-[400px] p-8 rounded-xl border border-red-200 bg-red-50 dark:bg-red-950/20 dark:border-red-800">
              <svg className="w-12 h-12 text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-lg font-medium text-red-800 dark:text-red-200 mb-2">Something went wrong</h3>
              <p className="text-sm text-red-600 dark:text-red-300 text-center mb-4">{canvasError}</p>
              <Button variant="outline" onClick={resetCanvas}>
                Try Again
              </Button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Canvas workspace view (suggest_complete or has report)
  if (isCanvasWorkspace) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white dark:from-slate-950 dark:to-slate-900">
        <header className="border-b bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm sticky top-0 z-40">
          <div className="container mx-auto px-4 h-14 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <a href="/generate" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Studio
              </a>
              <div className="h-6 w-px bg-border" />
              <span className="font-bold">Idea Canvas</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                resetCanvas();
                setReportData(null);
                setExitedToSummary(false);
                setCanvasMindMap(null);
                setCanvasMindMapError(null);
              }}
            >
              <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              New Canvas
            </Button>
          </div>
        </header>

        <main className="container mx-auto px-4 py-4">
          <div className="h-[calc(100vh-7rem)] flex gap-4">
            {/* Left Panel: Mind Map & Decision Tree */}
            <div className="w-1/2 flex flex-col rounded-2xl border border-border/60 bg-card overflow-hidden shadow-sm">
              <Tabs defaultValue="mindmap" className="flex flex-col h-full">
                <div className="px-5 py-3 border-b border-border/60 bg-gradient-to-r from-slate-50 to-slate-100/50 dark:from-slate-900/50 dark:to-slate-800/30 flex items-center justify-between">
                  <TabsList className="bg-white/50 dark:bg-slate-800/50">
                    <TabsTrigger value="mindmap" className="text-xs gap-1.5">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      Mind Map
                      {isGeneratingCanvasMindMap && (
                        <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      )}
                    </TabsTrigger>
                    <TabsTrigger value="tree" className="text-xs gap-1.5">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                      </svg>
                      Decision Tree
                    </TabsTrigger>
                  </TabsList>
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white dark:bg-slate-800 border border-border/60 shadow-sm">
                    <svg className="w-3.5 h-3.5 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-xs font-medium">{canvas?.question_count || 0} questions</span>
                  </div>
                </div>

                <TabsContent value="mindmap" className="flex-1 min-h-0 m-0">
                  {isGeneratingCanvasMindMap ? (
                    <div className="flex flex-col items-center justify-center h-full p-8">
                      <div className="w-10 h-10 border-3 border-primary border-t-transparent rounded-full animate-spin mb-4" />
                      <p className="text-sm text-muted-foreground">Generating mind map from your exploration...</p>
                    </div>
                  ) : canvasMindMapError ? (
                    <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                      <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-3">
                        <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <p className="text-sm text-red-600 dark:text-red-400 mb-3">{canvasMindMapError}</p>
                      <Button variant="outline" size="sm" onClick={handleGenerateCanvasMindMap}>
                        Try Again
                      </Button>
                    </div>
                  ) : canvasMindMap ? (
                    <MindMapViewer
                      tree={{
                        title: canvasMindMap.title,
                        summary: canvasMindMap.summary,
                        source_count: canvasMindMap.source_count,
                        mode: canvasMindMap.mode,
                        nodes: canvasMindMap.nodes as import("@/lib/types/mindmap").MindMapNode,
                      }}
                      onReset={() => setCanvasMindMap(null)}
                    />
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full p-8">
                      <Button onClick={handleGenerateCanvasMindMap}>Generate Mind Map</Button>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="tree" className="flex-1 min-h-0 m-0">
                  <IdeaCanvas
                    canvas={canvas}
                    currentQuestion={null}
                    progressMessage={null}
                    isAnswering={false}
                    onAnswer={() => {}}
                    onReset={resetCanvas}
                    isSuggestComplete={true}
                    hideQuestionCard={true}
                  />
                </TabsContent>
              </Tabs>
            </div>

            {/* Right Panel: Report & Actions */}
            <div className="w-1/2 flex flex-col rounded-2xl border border-border/60 bg-card overflow-hidden shadow-sm">
              <div className="px-5 py-4 border-b border-border/60 bg-gradient-to-r from-emerald-50 to-teal-50/50 dark:from-emerald-950/30 dark:to-teal-950/20 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-sm">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm">{reportData ? "Report Ready" : "Exploration Complete"}</h4>
                    <p className="text-xs text-muted-foreground">{canvasProgressMessage || "Generate your implementation spec"}</p>
                  </div>
                </div>
              </div>

              <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
                <div className="p-5 flex-1 flex flex-col min-h-0 space-y-5">
                  {reportError && (
                    <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-sm text-red-600 dark:text-red-400 flex items-center gap-2 shrink-0">
                      <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {reportError}
                    </div>
                  )}

                  {!reportData ? (
                    <div className="space-y-3">
                      <Button
                        onClick={handleGenerateReport}
                        disabled={isGeneratingReport}
                        className="w-full h-12 text-base shadow-sm hover:shadow-md transition-all"
                        size="lg"
                      >
                        {isGeneratingReport ? (
                          <>
                            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                            Generating Report Pack...
                          </>
                        ) : (
                          <>
                            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Generate Report Pack
                          </>
                        )}
                      </Button>
                      <Button onClick={() => handleCanvasAnswer("continue")} variant="outline" className="w-full h-10">
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                        Continue Exploring
                      </Button>
                    </div>
                  ) : (
                    <>
                      <div className="grid grid-cols-3 gap-2 shrink-0">
                        <Button onClick={handleDownloadPdf} disabled={!reportData?.pdf_base64} className="h-10 text-sm">
                          <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                          </svg>
                          PDF
                        </Button>
                        <Button onClick={handleDownloadMarkdown} variant="outline" className="h-10 text-sm">
                          <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                          Markdown
                        </Button>
                        <Button
                          onClick={() => {
                            if (generatedImage) {
                              downloadImage(
                                generatedImage.data,
                                `${reportData?.title.replace(/[^a-z0-9]/gi, "_").toLowerCase() || "infographic"}`,
                                generatedImage.format as "png" | "svg"
                              );
                            }
                          }}
                          disabled={!includeReportImage || !generatedImage || isGeneratingImage}
                          variant="outline"
                          className="h-10 text-sm"
                        >
                          {isGeneratingImage ? (
                            <>
                              <div className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin mr-1.5" />
                              Image...
                            </>
                          ) : (
                            <>
                              <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                              Image
                            </>
                          )}
                        </Button>
                      </div>

                      {imageGenError && <p className="text-xs text-red-600 shrink-0">{imageGenError}</p>}

                      <Tabs defaultValue="image" className="flex-1 flex flex-col min-h-0">
                        <TabsList className="w-full grid grid-cols-3 h-9 shrink-0">
                          <TabsTrigger value="image" className="text-xs">Image</TabsTrigger>
                          <TabsTrigger value="pdf" className="text-xs">PDF</TabsTrigger>
                          <TabsTrigger value="markdown" className="text-xs">Markdown</TabsTrigger>
                        </TabsList>

                        <TabsContent value="image" className="mt-3 rounded-lg border border-border/60 overflow-auto bg-white dark:bg-slate-900">
                          {isGeneratingImage ? (
                            <div className="flex items-center justify-center flex-1 min-h-[200px] text-muted-foreground">
                              <div className="flex flex-col items-center gap-3">
                                <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                                <span className="text-sm">Generating visual summary...</span>
                              </div>
                            </div>
                          ) : generatedImage ? (
                            <img
                              src={`data:image/${generatedImage.format};base64,${generatedImage.data}`}
                              alt="Generated infographic"
                              className="w-full h-auto"
                            />
                          ) : imageGenError ? (
                            <div className="flex items-center justify-center flex-1 min-h-[200px] text-red-600 text-sm">
                              {imageGenError}
                            </div>
                          ) : (
                            <div className="flex items-center justify-center flex-1 min-h-[200px] text-muted-foreground text-sm">
                              {includeReportImage ? "Image generation pending..." : "Image disabled for this report."}
                            </div>
                          )}
                        </TabsContent>

                        <TabsContent value="pdf" className="mt-3 rounded-lg border border-border/60 overflow-hidden">
                          <div className="flex items-center justify-end px-3 py-2 border-b border-border/60 bg-muted/30 shrink-0">
                            <Button size="sm" variant="ghost" onClick={handleOpenPdfPreview} disabled={!reportData.pdf_base64} className="h-7 text-xs">
                              <svg className="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                              </svg>
                              Open in New Tab
                            </Button>
                          </div>
                          {reportData.pdf_base64 ? (
                            <iframe
                              src={`data:application/pdf;base64,${reportData.pdf_base64}#view=FitH&zoom=page-width`}
                              className="w-full flex-1 min-h-0 border-0 bg-white"
                              title="PDF Preview"
                            />
                          ) : (
                            <div className="flex items-center justify-center flex-1 text-muted-foreground text-sm">
                              PDF generation in progress...
                            </div>
                          )}
                        </TabsContent>

                        <TabsContent value="markdown" className="mt-3 rounded-lg border border-border/60 overflow-hidden">
                          <div className="flex items-center justify-between px-3 py-2 border-b border-border/60 bg-muted/30 shrink-0">
                            <span className="text-xs text-muted-foreground font-medium">Markdown Source</span>
                            <Button size="sm" variant="ghost" onClick={handleCopyMarkdown} disabled={!reportData.markdown_content} className="h-7 text-xs">
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
                          </div>
                          <div className="p-3 flex-1 min-h-0 overflow-y-auto">
                            <pre className="text-xs font-mono whitespace-pre-wrap text-muted-foreground leading-relaxed">
                              {reportData.markdown_content}
                            </pre>
                          </div>
                        </TabsContent>
                      </Tabs>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Active questioning - Fullscreen mode
  return (
    <div className="fixed inset-0 z-50 bg-background">
      <div className="h-14 border-b flex items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <button
            onClick={handleExitToSummary}
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Finish & View Summary
          </button>
          <div className="h-6 w-px bg-border" />
          <span className="text-sm font-medium">
            {canvas?.idea.slice(0, 50)}
            {(canvas?.idea.length || 0) > 50 ? "..." : ""}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-muted-foreground">
            Questions: <span className="font-medium text-foreground">{canvas?.question_count || 0}</span>
          </div>
        </div>
      </div>

      <div className="h-[calc(100vh-3.5rem)] flex">
        <div className="w-[420px] border-r bg-muted/30 flex flex-col">
          {questionHistory.length > 0 && (
            <div className="px-6 pt-4 pb-2 border-b flex items-center justify-end">
              <span className="text-xs text-muted-foreground">
                Q{questionHistory.length + 1} of ~{Math.max(questionHistory.length + 3, 8)}
              </span>
            </div>
          )}

          <div className="flex-1 overflow-y-auto p-6">
            {currentQuestion ? (
              <QuestionCard
                question={currentQuestion}
                onAnswer={handleCanvasAnswer}
                onSkip={currentQuestion.allow_skip ? () => handleCanvasAnswer("Skipped") : undefined}
                isAnswering={isCanvasAnswering}
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                  <p className="text-sm text-muted-foreground">{canvasProgressMessage || "Loading next question..."}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex-1 bg-card">
          <IdeaCanvas
            canvas={canvas}
            currentQuestion={currentQuestion}
            progressMessage={null}
            isAnswering={isCanvasAnswering}
            onAnswer={handleCanvasAnswer}
            onReset={resetCanvas}
            isSuggestComplete={false}
            hideQuestionCard={true}
          />
        </div>
      </div>
    </div>
  );
}
