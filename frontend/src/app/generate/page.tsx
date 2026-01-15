"use client";

import { useCallback } from "react";
import { GenerateForm } from "@/components/forms/GenerateForm";
import { GenerationProgress } from "@/components/progress/GenerationProgress";
import { useGeneration } from "@/hooks/useGeneration";
import {
  OutputFormat,
  Provider,
  Audience,
  ImageStyle,
  SourceItem,
} from "@/lib/types/requests";

export default function GeneratePage() {
  const {
    state,
    progress,
    status,
    downloadUrl,
    error,
    metadata,
    generate,
    reset,
  } = useGeneration();

  const handleSubmit = useCallback(
    (
      sources: SourceItem[],
      options: {
        outputFormat: OutputFormat;
        provider: Provider;
        audience: Audience;
        imageStyle: ImageStyle;
        enableImageGeneration: boolean;
      },
      contentApiKey: string,
      imageApiKey?: string
    ) => {
      generate(
        {
          output_format: options.outputFormat,
          sources,
          provider: options.provider,
          preferences: {
            audience: options.audience,
            image_style: options.imageStyle,
            temperature: 0.4,
            max_tokens: 8000,
            max_slides: 10,
            max_summary_points: 5,
            enable_image_generation: options.enableImageGeneration,
          },
        },
        contentApiKey,
        imageApiKey
      );
    },
    [generate]
  );

  const isGenerating = state === "generating";

  return (
    <div className="container mx-auto px-4 py-8 md:py-12">
      <div className="mx-auto max-w-3xl space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
            Generate Document
          </h1>
          <p className="text-muted-foreground">
            Add your sources, configure options, and generate professional documents.
          </p>
        </div>

        {state !== "idle" && (
          <GenerationProgress
            state={state}
            progress={progress}
            status={status}
            downloadUrl={downloadUrl}
            error={error}
            metadata={metadata}
            onReset={reset}
          />
        )}

        {state === "idle" && (
          <GenerateForm onSubmit={handleSubmit} isGenerating={isGenerating} />
        )}
      </div>
    </div>
  );
}
