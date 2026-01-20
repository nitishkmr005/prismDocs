"use client";

import Image from "next/image";
import { cn } from "@/lib/utils";

interface ScrollingImageProps {
  src: string;
  alt: string;
  aspectRatio?: "portrait" | "landscape" | "square" | "video";
  className?: string;
  fit?: "contain" | "cover";
  fixedHeight?: boolean;
}

export function ScrollingImage({ 
  src, 
  alt, 
  aspectRatio = "portrait",
  className,
  fit = "contain",
  fixedHeight = false,
}: ScrollingImageProps) {
  // Aspect ratio map
  const aspectClass = fixedHeight
    ? ""
    : {
        portrait: "aspect-[3/4]",
        landscape: "aspect-video",
        square: "aspect-square",
        video: "aspect-video",
      }[aspectRatio];

  return (
    <div 
      className={cn(
        "relative w-full overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 shadow-xl bg-slate-100 dark:bg-slate-900 group cursor-pointer",
        aspectClass,
        className
      )}
    >
      <Image
        src={src}
        alt={alt}
        fill
        className={cn(
          "transition-transform duration-500 ease-in-out",
          fit === "contain" ? "object-contain" : "object-cover"
        )}
      />

      {/* Overlay to indicate interactivity */}
      <div className="absolute inset-0 pointer-events-none ring-1 ring-inset ring-black/10 dark:ring-white/10 rounded-xl" />
    </div>
  );
}
