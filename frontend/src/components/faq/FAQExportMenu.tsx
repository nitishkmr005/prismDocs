// frontend/src/components/faq/FAQExportMenu.tsx

"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { FAQDocument } from "@/lib/types/faq";
import { getApiUrl } from "@/config/api";

interface FAQExportMenuProps {
  faqDocument: FAQDocument;
  downloadUrl?: string | null;
}

function buildFaqMarkdown(doc: FAQDocument): string {
  const lines: string[] = [];
  lines.push(`# ${doc.title}`);
  if (doc.description) {
    lines.push("");
    lines.push(doc.description);
  }
  lines.push("");

  doc.items.forEach((item) => {
    lines.push(`## ${item.question}`);
    lines.push("");
    lines.push(item.answer);
    if (item.tags.length > 0) {
      lines.push("");
      lines.push(`Tags: ${item.tags.map((tag) => `\`${tag}\``).join(" ")}`);
    }
    lines.push("");
  });

  return lines.join("\n").trim();
}

export function FAQExportMenu({ faqDocument, downloadUrl }: FAQExportMenuProps) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const resolvedDownloadUrl = downloadUrl
    ? (downloadUrl.startsWith("http") ? downloadUrl : getApiUrl(downloadUrl))
    : null;

  const handleDownloadJson = () => {
    if (resolvedDownloadUrl) {
      const link = document.createElement("a");
      link.href = resolvedDownloadUrl;
      link.download = `${faqDocument.title.replace(/[^a-zA-Z0-9]/g, "_")}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      return;
    }

    const blob = new Blob([JSON.stringify(faqDocument, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${faqDocument.title.replace(/[^a-zA-Z0-9]/g, "_")}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleCopyMarkdown = async () => {
    const markdown = buildFaqMarkdown(faqDocument);
    try {
      await navigator.clipboard.writeText(markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Ignore clipboard errors
    }
  };

  const handleDownloadMarkdown = () => {
    const markdown = buildFaqMarkdown(faqDocument);
    const blob = new Blob([markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${faqDocument.title.replace(/[^a-zA-Z0-9]/g, "_")}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="relative">
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen((prev) => !prev)}
        className="h-8 text-xs"
      >
        Export
        <svg className="w-3.5 h-3.5 ml-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </Button>

      {open && (
        <div className="absolute right-0 mt-2 w-44 rounded-lg border border-border bg-background shadow-lg z-20">
          <button
            type="button"
            onClick={() => {
              handleDownloadJson();
              setOpen(false);
            }}
            className="w-full px-3 py-2 text-left text-xs hover:bg-muted"
          >
            Download JSON
          </button>
          <button
            type="button"
            onClick={() => {
              handleDownloadMarkdown();
              setOpen(false);
            }}
            className="w-full px-3 py-2 text-left text-xs hover:bg-muted"
          >
            Download Markdown
          </button>
          <button
            type="button"
            onClick={() => {
              handleCopyMarkdown();
              setOpen(false);
            }}
            className="w-full px-3 py-2 text-left text-xs hover:bg-muted"
          >
            {copied ? "Copied!" : "Copy Markdown"}
          </button>
        </div>
      )}
    </div>
  );
}
