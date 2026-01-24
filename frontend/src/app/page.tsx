"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { ScrollingImage } from "@/components/ui/scrolling-image";
import { ApiKeysModal } from "@/components/studio/ApiKeysModal";
import { AuthModal } from "@/components/auth";
import { useAuth } from "@/hooks/useAuth";
import { Provider } from "@/lib/types/requests";

// Geometric Prism Illustration - Editorial Style with 6 outputs
function PrismIllustration() {
  return (
    <div className="relative w-full max-w-3xl mx-auto">
      <svg
        viewBox="0 0 920 420"
        className="w-full"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Amber gradient for prism */}
          <linearGradient id="prism-amber" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity="1" />
            <stop offset="50%" stopColor="#d97706" stopOpacity="1" />
            <stop offset="100%" stopColor="#b45309" stopOpacity="1" />
          </linearGradient>

          {/* Light reflection */}
          <linearGradient id="prism-light" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="white" stopOpacity="0.4" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </linearGradient>

          {/* Input beam gradient */}
          <linearGradient id="input-beam" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#94a3b8" stopOpacity="0.4" />
            <stop offset="40%" stopColor="#f59e0b" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#f59e0b" stopOpacity="1" />
          </linearGradient>

          {/* Input beam glow */}
          <filter id="input-glow" x="-50%" y="-100%" width="200%" height="300%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* Output ray gradients - 6 colors */}
          <linearGradient id="ray-pdf" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#ef4444" stopOpacity="1" />
            <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="ray-slides" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity="1" />
            <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="ray-markdown" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22c55e" stopOpacity="1" />
            <stop offset="100%" stopColor="#22c55e" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="ray-whiteboard" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#14b8a6" stopOpacity="1" />
            <stop offset="100%" stopColor="#14b8a6" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="ray-mindmap" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="1" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="ray-podcast" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#a855f7" stopOpacity="1" />
            <stop offset="100%" stopColor="#a855f7" stopOpacity="0" />
          </linearGradient>

          {/* Glow filter for output rays */}
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* Drop shadow for prism */}
          <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="0" dy="10" stdDeviation="20" floodColor="#f59e0b" floodOpacity="0.3" />
          </filter>
        </defs>

        {/* Input document */}
        <g className="animate-reveal-up delay-200">
          <rect x="40" y="150" width="100" height="120" rx="6" fill="white" fillOpacity="0.95" stroke="#cbd5e1" strokeWidth="1.5" className="dark:fill-slate-800 dark:fill-opacity-60 dark:stroke-slate-600" />
          <line x1="58" y1="178" x2="122" y2="178" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round" />
          <line x1="58" y1="198" x2="112" y2="198" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round" />
          <line x1="58" y1="218" x2="118" y2="218" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round" />
          <line x1="58" y1="238" x2="100" y2="238" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round" />
          <text x="90" y="290" textAnchor="middle" className="fill-slate-400 dark:fill-slate-500" style={{ fontSize: '11px', fontFamily: 'monospace', letterSpacing: '0.1em' }}>SOURCE</text>
        </g>

        {/* Input beam - enhanced visibility */}
        <g filter="url(#input-glow)">
          {/* Background glow */}
          <line x1="145" y1="210" x2="305" y2="210" stroke="#fcd34d" strokeWidth="14" opacity="0.15" strokeLinecap="round" />
          {/* Main beam */}
          <line x1="150" y1="210" x2="300" y2="210" stroke="url(#input-beam)" strokeWidth="8" strokeLinecap="round">
            <animate attributeName="stroke-width" values="6;10;6" dur="2s" repeatCount="indefinite" />
          </line>
          {/* Animated particles */}
          <circle r="5" fill="#f59e0b">
            <animateMotion dur="1.2s" repeatCount="indefinite" path="M150,210 L300,210" />
            <animate attributeName="opacity" values="0;1;1;0" dur="1.2s" repeatCount="indefinite" />
          </circle>
          <circle r="4" fill="#fbbf24">
            <animateMotion dur="1.2s" repeatCount="indefinite" begin="0.4s" path="M150,210 L300,210" />
            <animate attributeName="opacity" values="0;1;1;0" dur="1.2s" repeatCount="indefinite" begin="0.4s" />
          </circle>
          <circle r="3" fill="#fcd34d">
            <animateMotion dur="1.2s" repeatCount="indefinite" begin="0.8s" path="M150,210 L300,210" />
            <animate attributeName="opacity" values="0;1;1;0" dur="1.2s" repeatCount="indefinite" begin="0.8s" />
          </circle>
          {/* Arrow head */}
          <polygon points="295,200 318,210 295,220" fill="#f59e0b">
            <animate attributeName="opacity" values="0.8;1;0.8" dur="1s" repeatCount="indefinite" />
          </polygon>
        </g>

        {/* Central Prism */}
        <g filter="url(#shadow)" className="animate-reveal-scale delay-300">
          <polygon points="400,50 540,370 260,370" fill="url(#prism-amber)" />
          <polygon points="400,50 540,370 400,370" fill="black" fillOpacity="0.2" />
          <polygon points="400,50 455,210 345,210" fill="url(#prism-light)" />
          <polygon points="400,50 540,370 260,370" fill="none" stroke="rgba(255,255,255,0.4)" strokeWidth="2" />
          <text x="400" y="235" textAnchor="middle" fill="white" style={{ fontSize: '34px', fontWeight: 700, fontFamily: 'Clash Display, system-ui' }}>AI</text>
          <circle cx="400" cy="210" r="30" fill="white" opacity="0.1">
            <animate attributeName="r" values="25;40;25" dur="3s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.05;0.2;0.05" dur="3s" repeatCount="indefinite" />
          </circle>
        </g>

        {/* Output rays - 6 rays evenly distributed */}
        <g filter="url(#glow)">
          {/* PDF - Red */}
          <line x1="460" y1="145" x2="680" y2="50" stroke="url(#ray-pdf)" strokeWidth="5" strokeLinecap="round">
            <animate attributeName="x2" values="670;695;670" dur="3s" repeatCount="indefinite" />
          </line>
          {/* Slides - Amber */}
          <line x1="485" y1="185" x2="700" y2="115" stroke="url(#ray-slides)" strokeWidth="5" strokeLinecap="round">
            <animate attributeName="x2" values="690;715;690" dur="3s" repeatCount="indefinite" begin="0.15s" />
          </line>
          {/* Markdown - Green */}
          <line x1="500" y1="220" x2="710" y2="180" stroke="url(#ray-markdown)" strokeWidth="5" strokeLinecap="round">
            <animate attributeName="x2" values="700;725;700" dur="3s" repeatCount="indefinite" begin="0.3s" />
          </line>
          {/* Whiteboard - Teal */}
          <line x1="500" y1="255" x2="710" y2="250" stroke="url(#ray-whiteboard)" strokeWidth="5" strokeLinecap="round">
            <animate attributeName="x2" values="700;725;700" dur="3s" repeatCount="indefinite" begin="0.45s" />
          </line>
          {/* Mind Map - Blue */}
          <line x1="485" y1="290" x2="700" y2="315" stroke="url(#ray-mindmap)" strokeWidth="5" strokeLinecap="round">
            <animate attributeName="x2" values="690;715;690" dur="3s" repeatCount="indefinite" begin="0.6s" />
          </line>
          {/* Podcast - Purple */}
          <line x1="460" y1="330" x2="680" y2="385" stroke="url(#ray-podcast)" strokeWidth="5" strokeLinecap="round">
            <animate attributeName="x2" values="670;695;670" dur="3s" repeatCount="indefinite" begin="0.75s" />
          </line>
        </g>

        {/* Output labels with icons */}
        <g style={{ fontFamily: 'monospace', fontSize: '12px', fontWeight: 600, letterSpacing: '0.05em' }}>
          {/* PDF */}
          <g>
            <rect x="695" y="38" width="14" height="18" rx="2" fill="none" stroke="#ef4444" strokeWidth="1.5" />
            <line x1="698" y1="44" x2="706" y2="44" stroke="#ef4444" strokeWidth="1" />
            <line x1="698" y1="48" x2="704" y2="48" stroke="#ef4444" strokeWidth="1" />
            <text x="714" y="52" textAnchor="start" fill="#ef4444">PDF</text>
          </g>
          {/* Slides */}
          <g>
            <rect x="715" y="100" width="14" height="10" rx="1" fill="none" stroke="#f59e0b" strokeWidth="1.5" />
            <rect x="718" y="97" width="14" height="10" rx="1" fill="none" stroke="#f59e0b" strokeWidth="1" opacity="0.5" />
            <text x="735" y="110" textAnchor="start" fill="#f59e0b">SLIDES</text>
          </g>
          {/* Markdown */}
          <g>
            <text x="725" y="180" textAnchor="start" fill="#22c55e">
              <tspan fontWeight={800}>M</tspan>
              <tspan dx="1">ARKDOWN</tspan>
            </text>
          </g>
          {/* Whiteboard - NEW */}
          <g>
            <rect x="725" y="238" width="16" height="12" rx="1" fill="none" stroke="#14b8a6" strokeWidth="1.5" />
            <path d="M728 246 L731 241 L735 245 L738 240" stroke="#14b8a6" strokeWidth="1.2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
            <text x="746" y="250" textAnchor="start" fill="#14b8a6">WHITEBOARD</text>
          </g>
          {/* Mind Map */}
          <g>
            <circle cx="722" cy="312" r="4" fill="none" stroke="#3b82f6" strokeWidth="1.5" />
            <line x1="726" y1="309" x2="732" y2="304" stroke="#3b82f6" strokeWidth="1.2" />
            <circle cx="734" cy="302" r="2" fill="#3b82f6" />
            <line x1="726" y1="315" x2="732" y2="320" stroke="#3b82f6" strokeWidth="1.2" />
            <circle cx="734" cy="322" r="2" fill="#3b82f6" />
            <text x="740" y="316" textAnchor="start" fill="#3b82f6">MIND MAP</text>
          </g>
          {/* Podcast */}
          <g>
            <ellipse cx="700" cy="383" rx="5" ry="8" fill="none" stroke="#a855f7" strokeWidth="1.5" />
            <line x1="700" y1="391" x2="700" y2="396" stroke="#a855f7" strokeWidth="2" />
            <line x1="695" y1="396" x2="705" y2="396" stroke="#a855f7" strokeWidth="1.5" />
            <text x="712" y="388" textAnchor="start" fill="#a855f7">PODCAST</text>
          </g>
        </g>
      </svg>
    </div>
  );
}

// Stat counter component
function StatCounter({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center">
      <div className="editorial-heading text-4xl md:text-5xl text-gradient-amber">{value}</div>
      <div className="mono-label text-slate-500 dark:text-slate-400 mt-2">{label}</div>
    </div>
  );
}

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  // Modal states
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [pendingApiKeyModal, setPendingApiKeyModal] = useState(false);

  // API Keys state for modal
  const [provider, setProvider] = useState<Provider>("gemini");
  const [contentModel, setContentModel] = useState("gemini-2.5-flash");
  const [imageModel, setImageModel] = useState("gemini-2.5-flash-image");
  const [contentApiKey, setContentApiKey] = useState("");
  const [imageApiKey, setImageApiKey] = useState("");
  const [enableImageGeneration, setEnableImageGeneration] = useState(false);

  const hasContentKey = contentApiKey.trim().length > 0;

  // After successful auth, open API key modal if pending
  useEffect(() => {
    if (isAuthenticated && pendingApiKeyModal) {
      setPendingApiKeyModal(false);
      setShowApiKeyModal(true);
    }
  }, [isAuthenticated, pendingApiKeyModal]);

  const handleStartGenerating = () => {
    if (authLoading) return;

    if (!isAuthenticated) {
      setPendingApiKeyModal(true);
      setShowAuthModal(true);
    } else {
      setShowApiKeyModal(true);
    }
  };

  const handleAuthModalClose = () => {
    setShowAuthModal(false);
  };

  const handleApiKeyModalClose = (open: boolean) => {
    setShowApiKeyModal(open);
  };

  const handleApiKeyModalConfirm = () => {
    if (!hasContentKey) return;
    sessionStorage.setItem("prismdocs_content_api_key", contentApiKey);
    sessionStorage.setItem("prismdocs_provider", provider);
    sessionStorage.setItem("prismdocs_content_model", contentModel);
    sessionStorage.setItem(
      "prismdocs_enable_image_generation",
      enableImageGeneration ? "1" : "0"
    );
    if (imageApiKey) {
      sessionStorage.setItem("prismdocs_image_api_key", imageApiKey);
    }
    setShowApiKeyModal(false);
    router.push("/generate");
  };

  type GalleryItem = {
    id: string;
    category: string;
    title: string;
    format: string;
    kind: "scrolling" | "image";
    src: string;
    alt: string;
    aspect: "portrait" | "landscape" | "square";
    className?: string;
    fit?: "contain" | "cover";
    showPlay?: boolean;
    containerClassName?: string;
    audioSrc?: string;
  };

  const [activeImage, setActiveImage] = useState<GalleryItem | null>(null);

  const handleOpenImage = (item: GalleryItem) => {
    setActiveImage(item);
  };

  const handleCloseImage = () => {
    setActiveImage(null);
  };

  const galleryMediaHeight = "h-64 sm:h-72 lg:h-80";

  const galleryItems: GalleryItem[] = [
    {
      id: "article-pdf",
      category: "Articles",
      title: "PDF Report",
      format: "PDF",
      kind: "scrolling",
      src: "/screenshots/Article_PDF.png",
      alt: "PDF Article Output",
      aspect: "portrait",
      className: "border-slate-200 dark:border-slate-800",
    },
    {
      id: "article-markdown",
      category: "Articles",
      title: "Markdown Document",
      format: "Markdown",
      kind: "scrolling",
      src: "/screenshots/Article_Markdown.png",
      alt: "Markdown Article Output",
      aspect: "portrait",
      className: "border-slate-200 dark:border-slate-800",
    },
    {
      id: "slides-pdf",
      category: "Presentations",
      title: "Slides Preview",
      format: "Slides",
      kind: "scrolling",
      src: "/screenshots/Slides_PDF.png",
      alt: "Slides Output",
      aspect: "landscape",
      className: "border-slate-200 dark:border-slate-800",
    },
    {
      id: "podcast",
      category: "Audio",
      title: "AI Podcast",
      format: "Audio",
      kind: "image",
      src: "/screenshots/Podcast.png",
      alt: "Podcast Output",
      aspect: "landscape",
      fit: "contain",
      containerClassName: "bg-slate-900",
      showPlay: true,
      audioSrc: "/audio/Podcast.wav",
    },
    {
      id: "mindmap",
      category: "Visual",
      title: "Mind Map",
      format: "Mind Map",
      kind: "scrolling",
      src: "/screenshots/Mindmap.png",
      alt: "Mind Map Output",
      aspect: "landscape",
      className: "border-slate-200 dark:border-slate-800 bg-white",
    },
    {
      id: "image-original",
      category: "Image",
      title: "Original Image",
      format: "Original",
      kind: "image",
      src: "/screenshots/Original_Image.png",
      alt: "Original AI Image",
      aspect: "square",
      fit: "contain",
    },
    {
      id: "image-inpaint",
      category: "Image",
      title: "Inpainting",
      format: "Edit",
      kind: "image",
      src: "/screenshots/Inpainting_UI.png",
      alt: "Inpainting UI",
      aspect: "square",
      fit: "contain",
    },
    {
      id: "image-edited",
      category: "Image",
      title: "Final Result",
      format: "Result",
      kind: "image",
      src: "/screenshots/Edited_Image.png",
      alt: "Edited Result",
      aspect: "square",
      fit: "contain",
    },
  ];

  useEffect(() => {
    if (!activeImage) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setActiveImage(null);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    document.body.style.overflow = "hidden";

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [activeImage]);

  // Process steps data
  const processSteps = [
    {
      num: "01",
      title: "Upload",
      desc: "Drop any document — PDF, URL, DOCX, image, or plain text",
      formats: ["PDF", "URL", "DOCX", "TXT"]
    },
    {
      num: "02",
      title: "Transform",
      desc: "AI analyzes and restructures your content intelligently",
      formats: ["Claude", "Gemini", "OpenAI"]
    },
    {
      num: "03",
      title: "Export",
      desc: "Download in multiple professional formats instantly",
      formats: ["PDF", "PPTX", "MD", "Audio"]
    }
  ];

  // Studios data
  const studios: Array<{
    icon: string;
    title: string;
    desc: string;
    tags: string[];
    isNew?: boolean;
  }> = [
    {
      icon: "01",
      title: "Idea Canvas",
      desc: "Interactive Q&A that builds a visual decision tree and outputs a complete implementation spec.",
      tags: ["Voice Agent", "Mind Map"]
    },
    {
      icon: "02",
      title: "Mind Map Studio",
      desc: "Generate beautiful mind maps from any content with an interactive viewer.",
      tags: ["PNG", "SVG", "JSON"]
    },
    {
      icon: "03",
      title: "Image Studio",
      desc: "AI-powered image generation with style presets and refinement tools.",
      tags: ["Styles", "Edit", "Generate"]
    },
    {
      icon: "04",
      title: "Whiteboard Notes",
      desc: "Transform content into hand-drawn diagrams, sticky notes, and visual explanations.",
      tags: ["Diagrams", "Sketches", "Visual"],
      isNew: true
    }
  ];

  // Features data
  const features = [
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      ),
      title: "Your Keys, Your Data",
      desc: "Bring your own API keys. Zero data retention. Complete privacy."
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      ),
      title: "AI-Generated Visuals",
      desc: "Auto-generated images that match your content and style."
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
        </svg>
      ),
      title: "Multi-Format Output",
      desc: "PDF, PPTX, Markdown, Mind Maps, Podcasts and more."
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      title: "Lightning Fast",
      desc: "Optimized pipelines for rapid document generation."
    }
  ];

  return (
    <div className="relative overflow-hidden noise-overlay">
      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={handleAuthModalClose}
      />

      {/* API Keys Modal */}
      <ApiKeysModal
        isOpen={showApiKeyModal}
        onOpenChange={handleApiKeyModalClose}
        onConfirm={handleApiKeyModalConfirm}
        provider={provider}
        contentModel={contentModel}
        onProviderChange={setProvider}
        onContentModelChange={setContentModel}
        contentApiKey={contentApiKey}
        onContentApiKeyChange={setContentApiKey}
        enableImageGeneration={enableImageGeneration}
        onEnableImageGenerationChange={setEnableImageGeneration}
        allowImageGenerationToggle={true}
        requireImageKey={false}
        imageModel={imageModel}
        onImageModelChange={setImageModel}
        imageApiKey={imageApiKey}
        onImageApiKeyChange={setImageApiKey}
        canClose={true}
        canConfirm={hasContentKey}
      />

      {/* Geometric background elements */}
      <div className="absolute inset-0 -z-10 geometric-grid" />
      <div className="geometric-accent top-0 left-0" />
      <div className="geometric-accent bottom-0 right-0 rotate-180" />

      {/* ===== HERO SECTION ===== */}
      <section className="relative min-h-[90vh] flex items-center">
        <div className="container mx-auto px-4 py-20 md:py-32">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left: Text content */}
            <div className="space-y-8">
              {/* Eyebrow */}
              <div className="animate-reveal-up">
                <span className="mono-label inline-flex items-center gap-3 text-amber-600 dark:text-amber-400">
                  <span className="w-8 h-[2px] bg-amber-500" />
                  AI-Powered Document Generation
                </span>
              </div>

              {/* Main headline */}
              <h1 className="animate-reveal-up delay-100">
                <span className="editorial-heading text-5xl md:text-6xl lg:text-7xl text-slate-900 dark:text-white block">
                  Transform Content
                </span>
                <span className="editorial-heading text-5xl md:text-6xl lg:text-7xl text-gradient-amber block mt-2">
                  Into Any Format
                </span>
              </h1>

              {/* Subheadline */}
              <p className="text-lg md:text-xl text-slate-600 dark:text-slate-400 max-w-xl leading-relaxed animate-reveal-up delay-200">
                Upload a PDF, URL, or document. Get professional reports, presentations,
                mind maps, and podcasts. Your API keys, your data, your control.
              </p>

              {/* CTA buttons */}
              <div className="flex flex-col sm:flex-row gap-4 animate-reveal-up delay-300">
                <Button
                  size="lg"
                  className="h-14 px-8 text-base font-semibold bg-amber-500 hover:bg-amber-600 text-black shadow-lg shadow-amber-500/25 hover:shadow-amber-500/40 transition-all duration-300 hover:-translate-y-0.5"
                  onClick={handleStartGenerating}
                >
                  Start Generating
                  <svg className="w-5 h-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </Button>
                <Button
                  asChild
                  variant="outline"
                  size="lg"
                  className="h-14 px-8 text-base font-medium border-slate-300 dark:border-slate-700 hover:border-amber-500 dark:hover:border-amber-500 hover:text-amber-600 dark:hover:text-amber-400 transition-all duration-300"
                >
                  <a href="https://github.com/nitishkmr005/PrismDocs" target="_blank" rel="noopener noreferrer">
                    <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                      <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                    </svg>
                    View on GitHub
                  </a>
                </Button>
              </div>

              {/* Trust badges */}
              <div className="flex flex-wrap gap-6 pt-4 animate-reveal-up delay-400">
                {["Open Source", "MIT License", "No Usage Limits"].map((badge) => (
                  <span key={badge} className="inline-flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                    <svg className="w-4 h-4 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    {badge}
                  </span>
                ))}
              </div>
            </div>

            {/* Right: Prism illustration */}
            <div className="animate-reveal-scale delay-200">
              <PrismIllustration />
            </div>
          </div>
        </div>
      </section>

      {/* ===== STATS BAR ===== */}
      <section className="border-y border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
        <div className="container mx-auto px-4 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <StatCounter value="6+" label="Output Formats" />
            <StatCounter value="3+" label="AI Providers" />
            <StatCounter value="100%" label="Open Source" />
            <StatCounter value="0" label="Data Stored" />
          </div>
        </div>
      </section>

      {/* ===== HOW IT WORKS ===== */}
      <section className="py-24 md:py-32">
        <div className="container mx-auto px-4">
          {/* Section header */}
          <div className="max-w-2xl mb-16">
            <span className="mono-label text-amber-600 dark:text-amber-400 flex items-center gap-3 mb-4">
              <span className="w-8 h-[2px] bg-amber-500" />
              Process
            </span>
            <h2 className="editorial-heading text-4xl md:text-5xl text-slate-900 dark:text-white mb-4">
              How It Works
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-400">
              Three simple steps to transform your content into professional documents.
            </p>
          </div>

          {/* Process steps */}
          <div className="grid md:grid-cols-3 gap-8 lg:gap-12">
            {processSteps.map((step, i) => (
              <div
                key={step.num}
                className={`editorial-card rounded-2xl p-8 animate-reveal-up delay-${(i + 1) * 100}`}
              >
                {/* Step number */}
                <div className="flex items-center gap-4 mb-6">
                  <span className="editorial-heading text-5xl text-gradient-amber">{step.num}</span>
                  <div className="flex-1 h-[1px] bg-gradient-to-r from-amber-500/50 to-transparent" />
                </div>

                {/* Content */}
                <h3 className="editorial-subhead text-2xl text-slate-900 dark:text-white mb-3">
                  {step.title}
                </h3>
                <p className="text-slate-600 dark:text-slate-400 mb-6">
                  {step.desc}
                </p>

                {/* Format tags */}
                <div className="flex flex-wrap gap-2">
                  {step.formats.map((format) => (
                    <span
                      key={format}
                      className="mono-label px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                    >
                      {format}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== CREATIVE STUDIOS ===== */}
      <section className="py-24 md:py-32 bg-slate-50 dark:bg-slate-900/50">
        <div className="container mx-auto px-4">
          {/* Section header */}
          <div className="max-w-2xl mb-16">
            <span className="mono-label text-amber-600 dark:text-amber-400 flex items-center gap-3 mb-4">
              <span className="w-8 h-[2px] bg-amber-500" />
              Features
            </span>
            <h2 className="editorial-heading text-4xl md:text-5xl text-slate-900 dark:text-white mb-4">
              Creative Studios
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-400">
              Beyond document generation — interactive tools for ideation and visualization.
            </p>
          </div>

          {/* Studios grid */}
          <div className="grid md:grid-cols-3 gap-8">
            {studios.map((studio, i) => (
              <div
                key={studio.title}
                className={`group relative editorial-card rounded-2xl p-8 overflow-hidden animate-reveal-up delay-${(i + 1) * 100}`}
              >
                {/* Decorative corner */}
                <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-amber-500/10 to-transparent" />

                {/* Icon number */}
                <div className="relative mb-6">
                  <span className="mono-label text-amber-500">{studio.icon}</span>
                </div>

                {/* Content */}
                <h3 className="editorial-subhead text-xl text-slate-900 dark:text-white mb-3 group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors">
                  {studio.title}
                </h3>
                <p className="text-slate-600 dark:text-slate-400 text-sm mb-6">
                  {studio.desc}
                </p>

                {/* Tags */}
                <div className="flex flex-wrap gap-2">
                  {studio.tags.map((tag) => (
                    <span
                      key={tag}
                      className="text-xs px-2.5 py-1 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== GALLERY ===== */}
      <section className="py-24 md:py-32">
        <div className="container mx-auto px-4">
          {/* Section header */}
          <div className="max-w-2xl mb-16">
            <span className="mono-label text-amber-600 dark:text-amber-400 flex items-center gap-3 mb-4">
              <span className="w-8 h-[2px] bg-amber-500" />
              Examples
            </span>
            <h2 className="editorial-heading text-4xl md:text-5xl text-slate-900 dark:text-white mb-4">
              Sample Outputs
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-400">
              Documents generated entirely by PrismDocs. Scroll to explore.
            </p>
          </div>

          {/* Gallery horizontal scroll */}
          <div className="relative -mx-4">
            <div className="flex gap-6 overflow-x-auto scroll-smooth snap-x snap-mandatory pb-6 px-4 editorial-scrollbar">
              {galleryItems.map((item) => (
                <div key={item.id} className="snap-start shrink-0 w-[300px] sm:w-[360px]">
                  <div className="group h-full editorial-card rounded-xl p-4">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-3">
                      <span className="mono-label text-amber-600 dark:text-amber-400">
                        {item.category}
                      </span>
                      <span className="text-xs text-slate-500 dark:text-slate-400">{item.format}</span>
                    </div>

                    {/* Media */}
                    <button
                      type="button"
                      className="block w-full rounded-lg text-left cursor-zoom-in focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400"
                      onClick={() => handleOpenImage(item)}
                      aria-label={`Open ${item.title} in full screen`}
                    >
                      {item.kind === "scrolling" ? (
                        <ScrollingImage
                          src={item.src}
                          alt={item.alt}
                          aspectRatio={item.aspect}
                          className={`${galleryMediaHeight} ${item.className ?? ""}`}
                          fixedHeight
                        />
                      ) : (
                        <div className={`relative overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 ${galleryMediaHeight} ${item.containerClassName ?? ""}`}>
                          <Image
                            src={item.src}
                            alt={item.alt}
                            fill
                            className={`transition-transform duration-500 group-hover:scale-105 ${item.fit === "contain" ? "object-contain p-4" : "object-cover"}`}
                          />
                          {item.showPlay && (
                            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                              <span className="w-16 h-16 rounded-full bg-amber-500 flex items-center justify-center">
                                <svg className="w-6 h-6 text-black ml-1" fill="currentColor" viewBox="0 0 24 24">
                                  <path d="M8 5v14l11-7z" />
                                </svg>
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    </button>

                    {/* Title */}
                    <p className="text-sm font-medium text-slate-900 dark:text-white mt-3">{item.title}</p>

                    {/* Audio player */}
                    {item.audioSrc && (
                      <audio controls preload="none" className="w-full mt-3 h-10">
                        <source src={item.audioSrc} type="audio/wav" />
                      </audio>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Fade edge */}
            <div className="pointer-events-none absolute right-0 top-0 h-full w-16 bg-gradient-to-l from-white dark:from-slate-950 to-transparent" />
          </div>
        </div>
      </section>

      {/* ===== FEATURES GRID ===== */}
      <section className="py-24 md:py-32 bg-slate-50 dark:bg-slate-900/50">
        <div className="container mx-auto px-4">
          {/* Section header - centered */}
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="mono-label text-amber-600 dark:text-amber-400 inline-flex items-center gap-3 mb-4">
              <span className="w-8 h-[2px] bg-amber-500" />
              Why PrismDocs
              <span className="w-8 h-[2px] bg-amber-500" />
            </span>
            <h2 className="editorial-heading text-4xl md:text-5xl text-slate-900 dark:text-white">
              Enterprise-Grade Features
            </h2>
          </div>

          {/* Features grid */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl mx-auto">
            {features.map((feature, i) => (
              <div
                key={feature.title}
                className={`editorial-card rounded-xl p-6 text-center animate-reveal-up delay-${(i + 1) * 100}`}
              >
                {/* Icon */}
                <div className="w-12 h-12 mx-auto mb-4 rounded-xl bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                  {feature.icon}
                </div>

                {/* Content */}
                <h3 className="editorial-subhead text-lg text-slate-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== USE CASES ===== */}
      <section className="py-24 md:py-32">
        <div className="container mx-auto px-4">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="mono-label text-amber-600 dark:text-amber-400 inline-flex items-center gap-3 mb-4">
              <span className="w-8 h-[2px] bg-amber-500" />
              For Everyone
              <span className="w-8 h-[2px] bg-amber-500" />
            </span>
            <h2 className="editorial-heading text-4xl md:text-5xl text-slate-900 dark:text-white">
              Built for Your Workflow
            </h2>
          </div>

          {/* Use case pills */}
          <div className="flex flex-wrap justify-center gap-4 max-w-4xl mx-auto">
            {[
              { emoji: "01", title: "Executives" },
              { emoji: "02", title: "Researchers" },
              { emoji: "03", title: "Job Seekers" },
              { emoji: "04", title: "Creators" },
              { emoji: "05", title: "Developers" },
              { emoji: "06", title: "Educators" },
            ].map((item) => (
              <div
                key={item.title}
                className="group flex items-center gap-3 px-6 py-4 rounded-full editorial-card cursor-default"
              >
                <span className="mono-label text-amber-500">{item.emoji}</span>
                <span className="font-medium text-slate-900 dark:text-white">{item.title}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== FINAL CTA ===== */}
      <section className="py-24 md:py-32">
        <div className="container mx-auto px-4">
          <div className="relative max-w-4xl mx-auto">
            {/* Background */}
            <div className="absolute inset-0 bg-gradient-to-br from-slate-900 to-slate-800 dark:from-slate-800 dark:to-slate-900 rounded-3xl overflow-hidden">
              <div className="absolute inset-0 geometric-grid opacity-20" />
              <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/20 rounded-full blur-3xl" />
              <div className="absolute bottom-0 left-0 w-48 h-48 bg-amber-500/10 rounded-full blur-3xl" />
            </div>

            {/* Content */}
            <div className="relative text-center p-12 md:p-16">
              <h2 className="editorial-heading text-3xl md:text-4xl lg:text-5xl text-white mb-4">
                Ready to transform your content?
              </h2>
              <p className="text-lg text-slate-300 max-w-xl mx-auto mb-8">
                Bring your own API key and start generating professional documents in seconds.
              </p>
              <Button
                asChild
                size="lg"
                className="h-14 px-10 text-base font-semibold bg-amber-500 hover:bg-amber-400 text-black shadow-lg shadow-amber-500/25 transition-all duration-300 hover:-translate-y-0.5"
              >
                <Link href="/generate">
                  Get Started Free
                  <svg className="w-5 h-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Image lightbox modal */}
      {activeImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
          role="dialog"
          aria-modal="true"
          aria-label={`${activeImage.title} full screen`}
          onClick={handleCloseImage}
        >
          <button
            type="button"
            onClick={handleCloseImage}
            className="absolute right-4 top-4 mono-label px-4 py-2 rounded-full bg-white/10 text-white/80 hover:bg-white/20 transition-colors"
            aria-label="Close"
          >
            ESC
          </button>
          <div
            className="relative w-full max-w-6xl overflow-hidden rounded-2xl bg-slate-900/90 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="relative h-[70vh] sm:h-[75vh] w-full bg-black/80">
              <Image
                src={activeImage.src}
                alt={activeImage.alt}
                fill
                sizes="100vw"
                className="object-contain"
              />
            </div>
            <div className="flex items-center justify-between gap-4 px-6 py-4 border-t border-white/10">
              <span className="font-medium text-white">{activeImage.title}</span>
              <span className="mono-label text-slate-400">{activeImage.category}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
