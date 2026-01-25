// frontend/src/components/idea-canvas/MermaidDiagram.tsx

"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import mermaid from "mermaid";
import { Button } from "@/components/ui/button";

interface MermaidDiagramProps {
  code: string;
  onElementClick?: (elementId: string) => void;
  highlightedElement?: string;
}

export function MermaidDiagram({
  code,
  onElementClick,
  highlightedElement,
}: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: "neutral",
      securityLevel: "loose",
      fontFamily: "inherit",
    });
  }, []);

  useEffect(() => {
    const renderDiagram = async () => {
      if (!containerRef.current || !code) return;

      try {
        setError(null);
        const id = `mermaid-${Date.now()}`;
        const { svg } = await mermaid.render(id, code);
        containerRef.current.innerHTML = svg;

        // Add click handlers to nodes
        if (onElementClick) {
          const nodes = containerRef.current.querySelectorAll(".node, .cluster");
          nodes.forEach((node) => {
            const nodeId = node.id || node.getAttribute("data-id");
            if (nodeId) {
              (node as HTMLElement).style.cursor = "pointer";
              node.addEventListener("click", () => onElementClick(nodeId));
            }
          });
        }

        // Highlight element if specified
        if (highlightedElement) {
          const element = containerRef.current.querySelector(
            `#${highlightedElement}, [data-id="${highlightedElement}"]`
          );
          if (element) {
            (element as HTMLElement).style.outline = "3px solid #3b82f6";
            (element as HTMLElement).style.outlineOffset = "2px";
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to render diagram");
      }
    };

    renderDiagram();
  }, [code, onElementClick, highlightedElement]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement("textarea");
      textarea.value = code;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  }, [code]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4 text-center">
        <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-3">
          <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p className="text-sm text-red-600 dark:text-red-400 mb-2">Failed to render diagram</p>
        <p className="text-xs text-muted-foreground">{error}</p>
      </div>
    );
  }

  return (
    <div className="relative h-full flex flex-col">
      <div
        ref={containerRef}
        className="flex-1 overflow-auto p-4 flex items-center justify-center [&_svg]:max-w-full [&_svg]:h-auto"
      />
      <div className="absolute bottom-3 right-3">
        <Button
          variant="outline"
          size="sm"
          onClick={handleCopy}
          className="h-8 text-xs bg-background/80 backdrop-blur-sm"
        >
          {copied ? (
            <>
              <svg className="w-3.5 h-3.5 mr-1.5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Copied!
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copy Diagram
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
