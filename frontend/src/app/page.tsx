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

function RefractionIllustration() {
  return (
    <div className="relative w-full max-w-4xl mx-auto">
      {/* Animated aurora background */}
      <div className="absolute inset-0 -z-10 overflow-hidden rounded-3xl">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-violet-500/10 to-fuchsia-500/10 blur-3xl animate-pulse" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-gradient-to-br from-violet-400/20 to-transparent rounded-full blur-3xl animate-blob" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-gradient-to-br from-fuchsia-400/20 to-transparent rounded-full blur-3xl animate-blob animation-delay-2000" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-gradient-to-br from-cyan-400/15 to-transparent rounded-full blur-3xl animate-blob animation-delay-4000" />
      </div>

      {/* Glass card container */}
      <div className="relative bg-white/40 dark:bg-black/20 backdrop-blur-xl rounded-3xl border border-white/30 dark:border-white/10 p-8 shadow-2xl shadow-violet-500/10">
        <svg
          viewBox="0 0 700 280"
          className="w-full"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient id="prism-main" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style={{ stopColor: '#0891b2', stopOpacity: 1 }} />
              <stop offset="50%" style={{ stopColor: '#7c3aed', stopOpacity: 1 }} />
              <stop offset="100%" style={{ stopColor: '#c026d3', stopOpacity: 1 }} />
            </linearGradient>
            <linearGradient id="prism-highlight" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style={{ stopColor: 'white', stopOpacity: 0.5 }} />
              <stop offset="100%" style={{ stopColor: 'white', stopOpacity: 0 }} />
            </linearGradient>
            <linearGradient id="ray-red" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style={{ stopColor: '#ef4444', stopOpacity: 1 }} />
              <stop offset="100%" style={{ stopColor: '#ef4444', stopOpacity: 0 }} />
            </linearGradient>
            <linearGradient id="ray-orange" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style={{ stopColor: '#f97316', stopOpacity: 1 }} />
              <stop offset="100%" style={{ stopColor: '#f97316', stopOpacity: 0 }} />
            </linearGradient>
            <linearGradient id="ray-yellow" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style={{ stopColor: '#eab308', stopOpacity: 1 }} />
              <stop offset="100%" style={{ stopColor: '#eab308', stopOpacity: 0 }} />
            </linearGradient>
            <linearGradient id="ray-green" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style={{ stopColor: '#22c55e', stopOpacity: 1 }} />
              <stop offset="100%" style={{ stopColor: '#22c55e', stopOpacity: 0 }} />
            </linearGradient>
            <linearGradient id="ray-cyan" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style={{ stopColor: '#06b6d4', stopOpacity: 1 }} />
              <stop offset="100%" style={{ stopColor: '#06b6d4', stopOpacity: 0 }} />
            </linearGradient>
            <linearGradient id="ray-violet" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style={{ stopColor: '#8b5cf6', stopOpacity: 1 }} />
              <stop offset="100%" style={{ stopColor: '#8b5cf6', stopOpacity: 0 }} />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
            <filter id="drop-shadow">
              <feDropShadow dx="0" dy="8" stdDeviation="8" floodColor="#7c3aed" floodOpacity="0.4" />
            </filter>
          </defs>

          {/* Input sources - enhanced glass cards */}
          <g>
            {/* PDF Card */}
            <g transform="translate(30, 45)">
              <rect x="0" y="0" width="70" height="55" rx="12" fill="white" fillOpacity="0.9" stroke="#fecaca" strokeWidth="2" />
              <rect x="0" y="0" width="70" height="55" rx="12" fill="url(#prism-highlight)" fillOpacity="0.3" />
              <g transform="translate(22, 8)">
                <path d="M0 4 L0 30 Q0 32 2 32 L20 32 Q22 32 22 30 L22 10 L16 4 L2 4 Q0 4 0 6 Z" fill="none" stroke="#dc2626" strokeWidth="2" />
                <path d="M16 4 L16 10 L22 10" fill="none" stroke="#dc2626" strokeWidth="2" />
                <text x="11" y="26" textAnchor="middle" fontSize="9" fontWeight="700" fill="#dc2626">PDF</text>
              </g>
              <text x="35" y="50" textAnchor="middle" fontSize="9" fontWeight="600" fill="#b91c1c">Document</text>
            </g>

            {/* URL Card */}
            <g transform="translate(30, 112)">
              <rect x="0" y="0" width="70" height="55" rx="12" fill="white" fillOpacity="0.9" stroke="#bfdbfe" strokeWidth="2" />
              <g transform="translate(22, 6)">
                <circle cx="13" cy="13" r="12" fill="none" stroke="#2563eb" strokeWidth="2" />
                <ellipse cx="13" cy="13" rx="5" ry="12" fill="none" stroke="#2563eb" strokeWidth="1.2" />
                <line x1="1" y1="13" x2="25" y2="13" stroke="#2563eb" strokeWidth="1.2" />
              </g>
              <text x="35" y="50" textAnchor="middle" fontSize="9" fontWeight="600" fill="#1d4ed8">Web URL</text>
            </g>

            {/* Text Card */}
            <g transform="translate(30, 179)">
              <rect x="0" y="0" width="70" height="55" rx="12" fill="white" fillOpacity="0.9" stroke="#c4b5fd" strokeWidth="2" />
              <g transform="translate(22, 8)">
                <rect x="0" y="0" width="26" height="30" rx="4" fill="none" stroke="#7c3aed" strokeWidth="2" />
                <line x1="4" y1="8" x2="22" y2="8" stroke="#7c3aed" strokeWidth="2" strokeLinecap="round" />
                <line x1="4" y1="14" x2="18" y2="14" stroke="#7c3aed" strokeWidth="1.5" strokeLinecap="round" />
                <line x1="4" y1="20" x2="16" y2="20" stroke="#7c3aed" strokeWidth="1.5" strokeLinecap="round" />
              </g>
              <text x="35" y="50" textAnchor="middle" fontSize="9" fontWeight="600" fill="#6d28d9">Plain Text</text>
            </g>
          </g>

          {/* Animated input beams */}
          <g>
            <defs>
              <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
                <path d="M0,0 L0,6 L8,3 z" fill="#94a3b8" />
              </marker>
            </defs>
            <line x1="105" y1="73" x2="245" y2="135" stroke="#94a3b8" strokeWidth="3" strokeLinecap="round" markerEnd="url(#arrow)" strokeDasharray="8,4">
              <animate attributeName="stroke-dashoffset" values="12;0" dur="1s" repeatCount="indefinite" />
            </line>
            <line x1="105" y1="140" x2="245" y2="140" stroke="#94a3b8" strokeWidth="3" strokeLinecap="round" markerEnd="url(#arrow)" strokeDasharray="8,4">
              <animate attributeName="stroke-dashoffset" values="12;0" dur="1s" repeatCount="indefinite" begin="0.2s" />
            </line>
            <line x1="105" y1="207" x2="245" y2="145" stroke="#94a3b8" strokeWidth="3" strokeLinecap="round" markerEnd="url(#arrow)" strokeDasharray="8,4">
              <animate attributeName="stroke-dashoffset" values="12;0" dur="1s" repeatCount="indefinite" begin="0.4s" />
            </line>
          </g>

          {/* Central Prism with enhanced 3D effect */}
          <g transform="translate(255, 55)" filter="url(#drop-shadow)">
            <polygon points="95,0 190,170 0,170" fill="url(#prism-main)" />
            <polygon points="95,0 190,170 95,170" fill="black" fillOpacity="0.15" />
            <polygon points="95,0 130,85 60,85" fill="url(#prism-highlight)" />
            <polygon points="95,0 190,170 0,170" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="2.5" />
            <text x="95" y="115" textAnchor="middle" fontSize="28" fontWeight="800" fill="white" style={{ fontFamily: 'system-ui' }}>AI</text>
            <circle cx="95" cy="105" r="35" fill="white" opacity="0.1">
              <animate attributeName="r" values="30;40;30" dur="3s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.05;0.15;0.05" dur="3s" repeatCount="indefinite" />
            </circle>
          </g>

          {/* Rainbow output rays with enhanced animation */}
          <g transform="translate(445, 140)" filter="url(#glow)">
            <line x1="0" y1="0" x2="200" y2="-95" stroke="url(#ray-red)" strokeWidth="5" strokeLinecap="round">
              <animate attributeName="x2" values="190;210;190" dur="2s" repeatCount="indefinite" />
            </line>
            <line x1="0" y1="0" x2="210" y2="-65" stroke="url(#ray-orange)" strokeWidth="5" strokeLinecap="round">
              <animate attributeName="x2" values="200;220;200" dur="2s" repeatCount="indefinite" begin="0.1s" />
            </line>
            <line x1="0" y1="0" x2="215" y2="-32" stroke="url(#ray-yellow)" strokeWidth="5" strokeLinecap="round">
              <animate attributeName="x2" values="205;225;205" dur="2s" repeatCount="indefinite" begin="0.2s" />
            </line>
            <line x1="0" y1="0" x2="220" y2="0" stroke="url(#ray-green)" strokeWidth="5" strokeLinecap="round">
              <animate attributeName="x2" values="210;230;210" dur="2s" repeatCount="indefinite" begin="0.3s" />
            </line>
            <line x1="0" y1="0" x2="215" y2="32" stroke="url(#ray-cyan)" strokeWidth="5" strokeLinecap="round">
              <animate attributeName="x2" values="205;225;205" dur="2s" repeatCount="indefinite" begin="0.4s" />
            </line>
            <line x1="0" y1="0" x2="200" y2="95" stroke="url(#ray-violet)" strokeWidth="5" strokeLinecap="round">
              <animate attributeName="x2" values="190;210;190" dur="2s" repeatCount="indefinite" begin="0.5s" />
            </line>
          </g>

          {/* Output labels with icons */}
          <g style={{ fontFamily: 'system-ui' }}>
            <text x="655" y="45" textAnchor="end" fontSize="13" fontWeight="700" fill="#ef4444">📕 PDF Report</text>
            <text x="665" y="75" textAnchor="end" fontSize="13" fontWeight="700" fill="#f97316">📊 Slides</text>
            <text x="670" y="108" textAnchor="end" fontSize="13" fontWeight="700" fill="#eab308">📝 Markdown</text>
            <text x="675" y="140" textAnchor="end" fontSize="13" fontWeight="700" fill="#22c55e">✍️ Blog Post</text>
            <text x="670" y="172" textAnchor="end" fontSize="13" fontWeight="700" fill="#06b6d4">🧠 Mind Map</text>
            <text x="655" y="235" textAnchor="end" fontSize="13" fontWeight="700" fill="#8b5cf6">🎙️ Podcast</text>
          </g>
        </svg>
      </div>
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
      // Not logged in - show auth modal first, then open API key modal after login
      setPendingApiKeyModal(true);
      setShowAuthModal(true);
    } else {
      // Already logged in - show API key modal directly
      setShowApiKeyModal(true);
    }
  };

  const handleAuthModalClose = () => {
    setShowAuthModal(false);
    // Don't clear pendingApiKeyModal here - let the useEffect handle it after auth
  };

  const handleApiKeyModalClose = (open: boolean) => {
    setShowApiKeyModal(open);
    // If modal is closing and we have API key, navigate to generate page
    if (!open && hasContentKey) {
      // Store keys in sessionStorage for generate page to pick up
      sessionStorage.setItem('prismdocs_content_api_key', contentApiKey);
      sessionStorage.setItem('prismdocs_provider', provider);
      sessionStorage.setItem('prismdocs_content_model', contentModel);
      if (imageApiKey) {
        sessionStorage.setItem('prismdocs_image_api_key', imageApiKey);
      }
      router.push('/generate');
    }
  };

  const galleryAccentStyles = {
    cyan: "border-cyan-500/40 bg-cyan-50/80 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300",
    fuchsia: "border-fuchsia-500/40 bg-fuchsia-50/80 text-fuchsia-700 dark:bg-fuchsia-900/30 dark:text-fuchsia-300",
    violet: "border-violet-500/40 bg-violet-50/80 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300",
    amber: "border-amber-500/40 bg-amber-50/80 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
  } as const;

  const galleryMediaHeight = "h-64 sm:h-72 lg:h-80";

  type GalleryItem = {
    id: string;
    category: string;
    title: string;
    format: string;
    accent: "cyan" | "fuchsia" | "violet" | "amber";
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

  const galleryItems: GalleryItem[] = [
    {
      id: "article-pdf",
      category: "Articles & Reports",
      title: "PDF Report",
      format: "PDF",
      accent: "cyan",
      kind: "scrolling",
      src: "/screenshots/Article_PDF.png",
      alt: "PDF Article Output",
      aspect: "portrait",
      className: "border-slate-200 dark:border-slate-800",
    },
    {
      id: "article-markdown",
      category: "Articles & Reports",
      title: "Markdown Document",
      format: "Markdown",
      accent: "cyan",
      kind: "scrolling",
      src: "/screenshots/Article_Markdown.png",
      alt: "Markdown Article Output",
      aspect: "portrait",
      className: "border-slate-200 dark:border-slate-800",
    },
    {
      id: "slides-pdf",
      category: "Presentations",
      title: "Slides (PDF Preview)",
      format: "Slides",
      accent: "fuchsia",
      kind: "scrolling",
      src: "/screenshots/Slides_PDF.png",
      alt: "Slides Output",
      aspect: "landscape",
      className: "border-slate-200 dark:border-slate-800",
    },
    {
      id: "podcast",
      category: "Audio & Visuals",
      title: "AI-Generated Podcast",
      format: "Audio",
      accent: "violet",
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
      category: "Audio & Visuals",
      title: "Interactive Mind Map",
      format: "Mind Map",
      accent: "violet",
      kind: "scrolling",
      src: "/screenshots/Mindmap.png",
      alt: "Mind Map Output",
      aspect: "landscape",
      className: "border-slate-200 dark:border-slate-800 bg-white",
    },
    {
      id: "image-original",
      category: "Image Studio",
      title: "Original Image",
      format: "Original",
      accent: "amber",
      kind: "image",
      src: "/screenshots/Original_Image.png",
      alt: "Original AI Image",
      aspect: "square",
      fit: "contain",
    },
    {
      id: "image-inpaint",
      category: "Image Studio",
      title: "Inpainting Selection",
      format: "Edit",
      accent: "amber",
      kind: "image",
      src: "/screenshots/Inpainting_UI.png",
      alt: "Inpainting UI",
      aspect: "square",
      fit: "contain",
    },
    {
      id: "image-edited",
      category: "Image Studio",
      title: "Final Result",
      format: "Result",
      accent: "amber",
      kind: "image",
      src: "/screenshots/Edited_Image.png",
      alt: "Edited Result",
      aspect: "square",
      fit: "contain",
    },
  ];

  return (
    <div className="relative overflow-hidden">
      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={handleAuthModalClose}
      />

      {/* API Keys Modal */}
      <ApiKeysModal
        isOpen={showApiKeyModal}
        onOpenChange={handleApiKeyModalClose}
        provider={provider}
        contentModel={contentModel}
        onProviderChange={setProvider}
        onContentModelChange={setContentModel}
        contentApiKey={contentApiKey}
        onContentApiKeyChange={setContentApiKey}
        enableImageGeneration={enableImageGeneration}
        onEnableImageGenerationChange={setEnableImageGeneration}
        allowImageGenerationToggle={false}
        requireImageKey={false}
        imageApiKey={imageApiKey}
        onImageApiKeyChange={setImageApiKey}
        canClose={hasContentKey}
      />

      {/* Animated gradient background for hero */}
      <div className="absolute inset-0 -z-20 overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-[800px] bg-gradient-to-b from-violet-50/80 via-fuchsia-50/40 to-transparent dark:from-violet-950/30 dark:via-fuchsia-950/20 dark:to-transparent" />
        <div className="absolute top-20 -left-40 w-[600px] h-[600px] bg-gradient-to-br from-cyan-200/30 to-transparent dark:from-cyan-900/20 rounded-full blur-3xl animate-blob" />
        <div className="absolute top-40 -right-40 w-[500px] h-[500px] bg-gradient-to-bl from-fuchsia-200/30 to-transparent dark:from-fuchsia-900/20 rounded-full blur-3xl animate-blob animation-delay-2000" />
      </div>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-24 md:py-32">
        <div className="flex flex-col items-center text-center space-y-8 max-w-5xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="inline-flex items-center rounded-full border px-5 py-2 text-sm font-medium bg-white/60 dark:bg-black/30 backdrop-blur-md border-violet-200/50 dark:border-violet-800/50 shadow-lg shadow-violet-500/10">
            <span className="relative flex h-2 w-2 mr-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-violet-500"></span>
            </span>
            <span className="bg-gradient-to-r from-cyan-600 via-violet-600 to-fuchsia-600 bg-clip-text text-transparent font-semibold">
              AI-Powered Document Generation
            </span>
          </div>

          <h1 className="text-5xl font-extrabold tracking-tight sm:text-6xl md:text-7xl lg:text-8xl max-w-5xl leading-[1.1]">
            Multiple Sources.{" "}
            <span className="bg-gradient-to-r from-cyan-500 via-violet-500 to-fuchsia-500 bg-clip-text text-transparent animate-gradient">
              Many Formats.
            </span>
          </h1>

          <p className="text-lg text-muted-foreground max-w-2xl md:text-xl leading-relaxed">
            Transform PDFs, URLs, and documents into professional reports,
            presentations, mind maps, and more. Bring your own LLM API key
            and watch your content refract into any format.
          </p>

          <div className="flex flex-col gap-4 sm:flex-row pt-4">
            <Button 
              size="lg" 
              className="h-14 px-10 text-lg bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700 shadow-xl shadow-violet-500/30 hover:shadow-violet-500/40 transition-all duration-300 hover:scale-105"
              onClick={handleStartGenerating}
            >
              Start Generating →
            </Button>
            <Button asChild variant="outline" size="lg" className="h-14 px-10 text-lg backdrop-blur-sm bg-white/50 dark:bg-black/30 hover:bg-white/80 dark:hover:bg-black/50 transition-all duration-300">
              <a href="https://github.com/nitishkmr005/PrismDocs" target="_blank" rel="noopener noreferrer">
                View on GitHub
              </a>
            </Button>
          </div>
        </div>

        {/* Refraction Illustration */}
        <div className="mt-20 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-300">
          <RefractionIllustration />
        </div>
      </section>

      {/* How It Works Section - Enhanced with glass cards */}
      <section className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-50/50 to-transparent dark:via-slate-900/30" />
        <div className="container mx-auto px-4 relative">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 mb-4">
              Simple & Powerful
            </span>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              How It Works
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
              Like light through a prism, your content refracts into multiple professional formats
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-3 max-w-5xl mx-auto">
            {/* Step 1 */}
            <div className="group relative flex flex-col items-center text-center space-y-5 p-8 rounded-2xl bg-white/60 dark:bg-white/5 backdrop-blur-xl border border-white/50 dark:border-white/10 shadow-xl shadow-cyan-500/5 transition-all duration-500 hover:shadow-2xl hover:shadow-cyan-500/10 hover:-translate-y-2">
              <div className="absolute -top-4 -left-4 w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-cyan-600 flex items-center justify-center text-white text-lg font-bold shadow-lg">1</div>
              <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-cyan-100 to-cyan-50 dark:from-cyan-900/50 dark:to-cyan-950/50 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <svg className="h-8 w-8 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold">Upload Any Source</h3>
              <p className="text-muted-foreground leading-relaxed">
                PDFs, Word docs, URLs, images, or plain text. Our AI parses and understands it all.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                <span className="px-3 py-1 text-xs font-medium rounded-full bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300">PDF</span>
                <span className="px-3 py-1 text-xs font-medium rounded-full bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300">URL</span>
                <span className="px-3 py-1 text-xs font-medium rounded-full bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300">DOCX</span>
              </div>
            </div>

            {/* Step 2 */}
            <div className="group relative flex flex-col items-center text-center space-y-5 p-8 rounded-2xl bg-white/60 dark:bg-white/5 backdrop-blur-xl border border-white/50 dark:border-white/10 shadow-xl shadow-violet-500/5 transition-all duration-500 hover:shadow-2xl hover:shadow-violet-500/10 hover:-translate-y-2">
              <div className="absolute -top-4 -left-4 w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-violet-600 flex items-center justify-center text-white text-lg font-bold shadow-lg">2</div>
              <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-violet-100 to-violet-50 dark:from-violet-900/50 dark:to-violet-950/50 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <svg className="h-8 w-8 text-violet-600" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <polygon points="12,2 22,20 2,20" strokeWidth={2} strokeLinejoin="round" />
                  <circle cx="12" cy="14" r="2" fill="currentColor" stroke="none" />
                </svg>
              </div>
              <h3 className="text-xl font-bold">AI Transforms</h3>
              <p className="text-muted-foreground leading-relaxed">
                Our AI prism transforms and restructures your content intelligently with your LLM of choice.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                <span className="px-3 py-1 text-xs font-medium rounded-full bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300">Claude</span>
                <span className="px-3 py-1 text-xs font-medium rounded-full bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300">Gemini</span>
                <span className="px-3 py-1 text-xs font-medium rounded-full bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300">OpenAI</span>
              </div>
            </div>

            {/* Step 3 */}
            <div className="group relative flex flex-col items-center text-center space-y-5 p-8 rounded-2xl bg-white/60 dark:bg-white/5 backdrop-blur-xl border border-white/50 dark:border-white/10 shadow-xl shadow-fuchsia-500/5 transition-all duration-500 hover:shadow-2xl hover:shadow-fuchsia-500/10 hover:-translate-y-2">
              <div className="absolute -top-4 -left-4 w-10 h-10 rounded-full bg-gradient-to-br from-fuchsia-500 to-fuchsia-600 flex items-center justify-center text-white text-lg font-bold shadow-lg">3</div>
              <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-fuchsia-100 to-fuchsia-50 dark:from-fuchsia-900/50 dark:to-fuchsia-950/50 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <svg className="h-8 w-8 text-fuchsia-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </div>
              <h3 className="text-xl font-bold">Download Formats</h3>
              <p className="text-muted-foreground leading-relaxed">
                Get your content in multiple professional formats, ready to share and use.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                <span className="px-3 py-1 text-xs font-medium rounded-full bg-fuchsia-100 dark:bg-fuchsia-900/30 text-fuchsia-700 dark:text-fuchsia-300">PDF</span>
                <span className="px-3 py-1 text-xs font-medium rounded-full bg-fuchsia-100 dark:bg-fuchsia-900/30 text-fuchsia-700 dark:text-fuchsia-300">PPTX</span>
                <span className="px-3 py-1 text-xs font-medium rounded-full bg-fuchsia-100 dark:bg-fuchsia-900/30 text-fuchsia-700 dark:text-fuchsia-300">Mind Map</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Studios Section - NEW */}
      <section className="py-24 bg-gradient-to-b from-slate-50 to-white dark:from-slate-900/50 dark:to-transparent">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium bg-fuchsia-100 dark:bg-fuchsia-900/30 text-fuchsia-700 dark:text-fuchsia-300 mb-4">
              Interactive Features
            </span>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Powerful Creative Studios
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
              Beyond document generation — explore interactive tools for ideation and visualization
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-3 max-w-5xl mx-auto">
            {/* Idea Canvas */}
            <div className="group relative p-6 rounded-2xl bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/30 border border-amber-200/50 dark:border-amber-800/30 hover:shadow-2xl hover:shadow-amber-500/20 transition-all duration-500 hover:-translate-y-2 overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-amber-200/30 to-transparent rounded-bl-full" />
              <div className="relative">
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center mb-4 shadow-lg">
                  <span className="text-2xl">💡</span>
                </div>
                <h3 className="text-xl font-bold mb-2">Idea Canvas</h3>
                <p className="text-muted-foreground text-sm mb-4">
                  Interactive Q&A that builds a visual decision tree and outputs a complete implementation spec pack.
                </p>
                <div className="flex gap-2">
                  <span className="px-2 py-1 text-xs rounded-full bg-amber-200/50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300">Voice Agent</span>
                  <span className="px-2 py-1 text-xs rounded-full bg-amber-200/50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300">Mind Map</span>
                </div>
              </div>
            </div>

            {/* Mind Map Studio */}
            <div className="group relative p-6 rounded-2xl bg-gradient-to-br from-cyan-50 to-teal-50 dark:from-cyan-950/30 dark:to-teal-950/30 border border-cyan-200/50 dark:border-cyan-800/30 hover:shadow-2xl hover:shadow-cyan-500/20 transition-all duration-500 hover:-translate-y-2 overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-cyan-200/30 to-transparent rounded-bl-full" />
              <div className="relative">
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-cyan-500 to-teal-500 flex items-center justify-center mb-4 shadow-lg">
                  <span className="text-2xl">🧠</span>
                </div>
                <h3 className="text-xl font-bold mb-2">Mind Map Studio</h3>
                <p className="text-muted-foreground text-sm mb-4">
                  Generate beautiful mind maps from any content with an interactive viewer and multiple export options.
                </p>
                <div className="flex gap-2">
                  <span className="px-2 py-1 text-xs rounded-full bg-cyan-200/50 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300">PNG</span>
                  <span className="px-2 py-1 text-xs rounded-full bg-cyan-200/50 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300">SVG</span>
                  <span className="px-2 py-1 text-xs rounded-full bg-cyan-200/50 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300">JSON</span>
                </div>
              </div>
            </div>

            {/* Image Studio */}
            <div className="group relative p-6 rounded-2xl bg-gradient-to-br from-violet-50 to-purple-50 dark:from-violet-950/30 dark:to-purple-950/30 border border-violet-200/50 dark:border-violet-800/30 hover:shadow-2xl hover:shadow-violet-500/20 transition-all duration-500 hover:-translate-y-2 overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-violet-200/30 to-transparent rounded-bl-full" />
              <div className="relative">
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center mb-4 shadow-lg">
                  <span className="text-2xl">🎨</span>
                </div>
                <h3 className="text-xl font-bold mb-2">Image Studio</h3>
                <p className="text-muted-foreground text-sm mb-4">
                  AI-powered image generation with style presets, refinement tools, and SVG/PNG output.
                </p>
                <div className="flex gap-2">
                  <span className="px-2 py-1 text-xs rounded-full bg-violet-200/50 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300">Styles</span>
                  <span className="px-2 py-1 text-xs rounded-full bg-violet-200/50 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300">Edit</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Sample Outputs Gallery - NEW */}
      <section className="py-24 bg-white dark:bg-slate-900/50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300 mb-4">
              Gallery
            </span>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              See What's Possible
            </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
            Check out sample documents generated entirely by PrismDocs
          </p>
        </div>

          <div className="relative">
            <div className="flex gap-6 overflow-x-auto scroll-smooth snap-x snap-mandatory pb-6 -mx-4 px-4">
              {galleryItems.map((item) => (
                <div key={item.id} className="snap-start shrink-0 w-[280px] sm:w-[340px] lg:w-[380px]">
                  <div className="group h-full rounded-2xl border border-slate-200/70 dark:border-slate-800/70 bg-white/80 dark:bg-slate-900/40 backdrop-blur-sm p-4 shadow-lg transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl">
                    <div className="flex items-center justify-between mb-3">
                      <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold ${galleryAccentStyles[item.accent]}`}>
                        {item.category}
                      </span>
                      <span className="text-xs font-medium text-muted-foreground">{item.format}</span>
                    </div>
                    <div className="space-y-3">
                      {item.kind === "scrolling" ? (
                        <ScrollingImage 
                          src={item.src} 
                          alt={item.alt}
                          aspectRatio={item.aspect}
                          className={`${galleryMediaHeight} ${item.className ?? ""}`}
                          fixedHeight
                        />
                      ) : (
                        <div className={`relative overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 shadow-xl bg-slate-100 dark:bg-slate-900 ${galleryMediaHeight} ${item.containerClassName ?? ""}`}>
                          <Image 
                            src={item.src} 
                            alt={item.alt} 
                            fill 
                            className={`transition-transform duration-500 group-hover:scale-105 ${item.fit === "contain" ? "object-contain p-4" : "object-cover"}`}
                          />
                          {item.showPlay && (
                            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                              <span className="text-white text-3xl">▶️</span>
                            </div>
                          )}
                        </div>
                      )}
                      <p className="text-sm font-semibold text-slate-900 dark:text-white">{item.title}</p>
                      {item.audioSrc && (
                        <audio controls preload="none" className="w-full">
                          <source src={item.audioSrc} type="audio/wav" />
                          Your browser does not support the audio element.
                        </audio>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="pointer-events-none absolute right-0 top-0 h-full w-10 bg-gradient-to-l from-white dark:from-slate-900/60 to-transparent" />
          </div>
          <p className="mt-4 text-center text-sm text-muted-foreground">Swipe or scroll to explore the gallery.</p>
        </div>
      </section>

      {/* Use Cases Section - Compact */}
      <section className="py-24">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 mb-4">
              For Everyone
            </span>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Built for Your Workflow
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
              From executives to developers, PrismDocs transforms how you create content
            </p>
          </div>

          <div className="grid gap-4 grid-cols-2 md:grid-cols-3 lg:grid-cols-6 max-w-6xl mx-auto">
            {[
              { emoji: "👨‍💼", title: "Executives", color: "amber" },
              { emoji: "🎓", title: "Researchers", color: "blue" },
              { emoji: "💼", title: "Job Seekers", color: "green" },
              { emoji: "🎨", title: "Creators", color: "pink" },
              { emoji: "👨‍💻", title: "Developers", color: "violet" },
              { emoji: "📚", title: "Educators", color: "cyan" },
            ].map((item) => (
              <div key={item.title} className="group flex flex-col items-center text-center p-6 rounded-2xl bg-white/60 dark:bg-white/5 backdrop-blur-sm border border-white/50 dark:border-white/10 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <div className="text-4xl mb-3 group-hover:scale-110 transition-transform duration-300">{item.emoji}</div>
                <h3 className="font-semibold text-sm">{item.title}</h3>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section - Enhanced */}
      <section className="py-24 bg-gradient-to-b from-white to-slate-50 dark:from-transparent dark:to-slate-900/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 mb-4">
              Enterprise Ready
            </span>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Why Choose PrismDocs?
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
              Enterprise-grade features with complete privacy and control
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-3 max-w-4xl mx-auto">
            {[
              { icon: "🔐", title: "BYO API Keys", desc: "Your data stays private. Use your own LLM API keys.", gradient: "from-emerald-500 to-teal-600", shadow: "emerald" },
              { icon: "🎨", title: "AI Images", desc: "Auto-generated visuals that match your content.", gradient: "from-violet-500 to-purple-600", shadow: "violet" },
              { icon: "🔄", title: "Multi-format", desc: "PDF, PPTX, Markdown, Mind Maps & more.", gradient: "from-blue-500 to-indigo-600", shadow: "blue" },
            ].map((item) => (
              <div key={item.title} className={`group flex flex-col items-center text-center space-y-4 p-8 rounded-2xl bg-white/80 dark:bg-white/5 backdrop-blur-xl border border-white/50 dark:border-white/10 transition-all duration-500 hover:shadow-2xl hover:shadow-${item.shadow}-500/20 hover:-translate-y-2`}>
                <div className={`h-16 w-16 rounded-2xl bg-gradient-to-br ${item.gradient} flex items-center justify-center text-3xl shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                  {item.icon}
                </div>
                <h3 className="text-lg font-bold">{item.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>

          {/* Feature pills */}
          <div className="flex flex-wrap justify-center gap-3 mt-12 max-w-4xl mx-auto">
            {["No usage limits", "Pay only for LLM tokens", "Open Source", "MIT License"].map((text) => (
              <span key={text} className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-white/80 dark:bg-white/5 backdrop-blur-sm border border-white/50 dark:border-white/10 text-sm font-medium shadow-lg">
                <span className="text-emerald-500 font-bold">✓</span> {text}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section - Enhanced */}
      <section className="py-24">
        <div className="container mx-auto px-4">
          <div className="relative max-w-3xl mx-auto">
            {/* Animated background */}
            <div className="absolute inset-0 bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-3xl overflow-hidden">
              <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4xIj48cGF0aCBkPSJNMzYgMzRjMC0yLjIwOS0xLjc5MS00LTQtNHMtNCAxLjc5MS00IDQgMS43OTEgNCA0IDQgNC0xLjc5MSA0LTR6bTAtMThjMC0yLjIwOS0xLjc5MS00LTQtNHMtNCAxLjc5MS00IDQgMS43OTEgNCA0IDQgNC0xLjc5MSA0LTR6bTE4IDBjMC0yLjIwOS0xLjc5MS00LTQtNHMtNCAxLjc5MS00IDQgMS43OTEgNCA0IDQgNC0xLjc5MSA0LTR6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-20" />
              <div className="absolute top-0 left-0 w-40 h-40 bg-white/10 rounded-full blur-3xl" />
              <div className="absolute bottom-0 right-0 w-60 h-60 bg-black/10 rounded-full blur-3xl" />
            </div>
            
            <div className="relative text-center space-y-6 p-12 text-white">
              <h2 className="text-3xl md:text-4xl font-bold">Ready to transform your content?</h2>
              <p className="text-white/80 text-lg max-w-xl mx-auto">
                Bring your own API key and start generating professional documents in seconds.
              </p>
              <Button asChild size="lg" className="h-14 px-10 text-lg bg-white text-violet-600 hover:bg-white/90 shadow-2xl hover:scale-105 transition-all duration-300">
                <Link href="/generate">Get Started Free →</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
