import Link from "next/link";
import { Button } from "@/components/ui/button";

function RefractionIllustration() {
  return (
    <div className="relative w-full max-w-3xl mx-auto">
      {/* Enhanced floating particles background */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        {/* Main ambient glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-r from-cyan-500/20 via-violet-500/20 to-fuchsia-500/20 rounded-full blur-3xl animate-pulse" />
        
        {/* Floating particles */}
        <div className="absolute top-[10%] left-[15%] w-3 h-3 rounded-full bg-gradient-to-r from-cyan-400 to-cyan-500 opacity-60 animate-bounce" style={{ animationDuration: '3s', animationDelay: '0s' }} />
        <div className="absolute top-[20%] right-[20%] w-2 h-2 rounded-full bg-gradient-to-r from-violet-400 to-violet-500 opacity-50 animate-bounce" style={{ animationDuration: '4s', animationDelay: '0.5s' }} />
        <div className="absolute bottom-[25%] left-[10%] w-4 h-4 rounded-full bg-gradient-to-r from-fuchsia-400 to-fuchsia-500 opacity-40 animate-bounce" style={{ animationDuration: '3.5s', animationDelay: '1s' }} />
        <div className="absolute top-[60%] right-[10%] w-2.5 h-2.5 rounded-full bg-gradient-to-r from-amber-400 to-orange-500 opacity-50 animate-bounce" style={{ animationDuration: '4.5s', animationDelay: '0.3s' }} />
        <div className="absolute top-[40%] left-[5%] w-2 h-2 rounded-full bg-gradient-to-r from-emerald-400 to-green-500 opacity-45 animate-bounce" style={{ animationDuration: '5s', animationDelay: '0.8s' }} />
        <div className="absolute bottom-[15%] right-[25%] w-3 h-3 rounded-full bg-gradient-to-r from-blue-400 to-indigo-500 opacity-55 animate-bounce" style={{ animationDuration: '3.8s', animationDelay: '1.2s' }} />
        <div className="absolute top-[75%] left-[30%] w-1.5 h-1.5 rounded-full bg-gradient-to-r from-pink-400 to-rose-500 opacity-60 animate-bounce" style={{ animationDuration: '4.2s', animationDelay: '0.6s' }} />
        <div className="absolute top-[5%] right-[40%] w-2 h-2 rounded-full bg-gradient-to-r from-teal-400 to-cyan-500 opacity-45 animate-bounce" style={{ animationDuration: '3.2s', animationDelay: '1.5s' }} />
        
        {/* Orbiting rings - subtle */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 border border-violet-300/10 rounded-full animate-spin" style={{ animationDuration: '25s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 border border-cyan-300/10 rounded-full animate-spin" style={{ animationDuration: '20s', animationDirection: 'reverse' }} />
      </div>
      
      <svg
        viewBox="0 0 600 240"
        className="w-full"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Enhanced prism gradient with 3D effect */}
          <linearGradient id="prism-main" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#0891b2', stopOpacity: 1 }} />
            <stop offset="50%" style={{ stopColor: '#7c3aed', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: '#c026d3', stopOpacity: 1 }} />
          </linearGradient>
          
          {/* Prism highlight for 3D effect */}
          <linearGradient id="prism-highlight" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{ stopColor: 'white', stopOpacity: 0.4 }} />
            <stop offset="50%" style={{ stopColor: 'white', stopOpacity: 0.1 }} />
            <stop offset="100%" style={{ stopColor: 'white', stopOpacity: 0 }} />
          </linearGradient>
          
          {/* Prism shadow for depth */}
          <linearGradient id="prism-shadow" x1="100%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style={{ stopColor: 'black', stopOpacity: 0 }} />
            <stop offset="100%" style={{ stopColor: 'black', stopOpacity: 0.3 }} />
          </linearGradient>
          
          {/* Rainbow ray gradients */}
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
          <linearGradient id="ray-blue" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style={{ stopColor: '#3b82f6', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: '#3b82f6', stopOpacity: 0 }} />
          </linearGradient>
          <linearGradient id="ray-violet" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style={{ stopColor: '#8b5cf6', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: '#8b5cf6', stopOpacity: 0 }} />
          </linearGradient>
          
          {/* Input beam gradient */}
          <linearGradient id="input-beam" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style={{ stopColor: '#f8fafc', stopOpacity: 0.3 }} />
            <stop offset="100%" style={{ stopColor: '#f8fafc', stopOpacity: 0.9 }} />
          </linearGradient>
          
          {/* Card gradient fills */}
          <linearGradient id="card-pdf" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#fef2f2', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: '#fee2e2', stopOpacity: 1 }} />
          </linearGradient>
          <linearGradient id="card-url" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#eff6ff', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: '#dbeafe', stopOpacity: 1 }} />
          </linearGradient>
          <linearGradient id="card-txt" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#f5f3ff', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: '#ede9fe', stopOpacity: 1 }} />
          </linearGradient>
          
          {/* Glow filters */}
          <filter id="glow-strong">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          
          <filter id="glow-soft">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          
          <filter id="drop-shadow">
            <feDropShadow dx="0" dy="4" stdDeviation="4" floodColor="#7c3aed" floodOpacity="0.3" />
          </filter>
          
          <filter id="card-shadow">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#000" floodOpacity="0.1" />
          </filter>
        </defs>

        {/* Input sources with enhanced icons */}
        <g>
          {/* PDF Source Card */}
          <g transform="translate(20, 35)" filter="url(#card-shadow)">
            <rect x="0" y="0" width="60" height="50" rx="10" fill="url(#card-pdf)" stroke="#fecaca" strokeWidth="1.5" />
            {/* PDF Icon - Document with corner fold */}
            <g transform="translate(18, 8)">
              <path d="M0 4 L0 28 Q0 30 2 30 L18 30 Q20 30 20 28 L20 10 L14 4 L2 4 Q0 4 0 6 Z" fill="none" stroke="#dc2626" strokeWidth="1.5" strokeLinejoin="round" />
              <path d="M14 4 L14 10 L20 10" fill="none" stroke="#dc2626" strokeWidth="1.5" strokeLinejoin="round" />
              <text x="10" y="24" textAnchor="middle" fontSize="8" fontWeight="700" fill="#dc2626">PDF</text>
            </g>
            <text x="30" y="46" textAnchor="middle" fontSize="8" fontWeight="600" fill="#b91c1c">Document</text>
          </g>
          
          {/* URL Source Card */}
          <g transform="translate(20, 95)" filter="url(#card-shadow)">
            <rect x="0" y="0" width="60" height="50" rx="10" fill="url(#card-url)" stroke="#bfdbfe" strokeWidth="1.5" />
            {/* Globe Icon */}
            <g transform="translate(18, 6)">
              <circle cx="12" cy="12" r="11" fill="none" stroke="#2563eb" strokeWidth="1.5" />
              <ellipse cx="12" cy="12" rx="4.5" ry="11" fill="none" stroke="#2563eb" strokeWidth="1" />
              <line x1="1" y1="12" x2="23" y2="12" stroke="#2563eb" strokeWidth="1" />
              <path d="M3 6 Q12 8 21 6" fill="none" stroke="#2563eb" strokeWidth="0.8" />
              <path d="M3 18 Q12 16 21 18" fill="none" stroke="#2563eb" strokeWidth="0.8" />
            </g>
            <text x="30" y="46" textAnchor="middle" fontSize="8" fontWeight="600" fill="#1d4ed8">Web URL</text>
          </g>
          
          {/* Text Source Card */}
          <g transform="translate(20, 155)" filter="url(#card-shadow)">
            <rect x="0" y="0" width="60" height="50" rx="10" fill="url(#card-txt)" stroke="#c4b5fd" strokeWidth="1.5" />
            {/* Text Lines Icon */}
            <g transform="translate(18, 8)">
              <rect x="0" y="0" width="24" height="28" rx="3" fill="none" stroke="#7c3aed" strokeWidth="1.5" />
              <line x1="4" y1="7" x2="20" y2="7" stroke="#7c3aed" strokeWidth="1.5" strokeLinecap="round" />
              <line x1="4" y1="12" x2="18" y2="12" stroke="#7c3aed" strokeWidth="1.2" strokeLinecap="round" />
              <line x1="4" y1="17" x2="16" y2="17" stroke="#7c3aed" strokeWidth="1.2" strokeLinecap="round" />
              <line x1="4" y1="22" x2="14" y2="22" stroke="#7c3aed" strokeWidth="1" strokeLinecap="round" />
            </g>
            <text x="30" y="46" textAnchor="middle" fontSize="8" fontWeight="600" fill="#6d28d9">Plain Text</text>
          </g>
        </g>

        {/* Converging input beams with arrows */}
        <g>
          {/* Arrow marker definition */}
          <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
              <path d="M0,0 L0,6 L9,3 z" fill="#94a3b8" />
            </marker>
          </defs>
          
          {/* Input lines with arrows */}
          <line x1="85" y1="60" x2="210" y2="115" stroke="#94a3b8" strokeWidth="2.5" strokeLinecap="round" markerEnd="url(#arrow)">
            <animate attributeName="opacity" values="0.5;1;0.5" dur="2s" repeatCount="indefinite" />
          </line>
          <line x1="85" y1="120" x2="210" y2="120" stroke="#94a3b8" strokeWidth="2.5" strokeLinecap="round" markerEnd="url(#arrow)">
            <animate attributeName="opacity" values="0.6;1;0.6" dur="2s" repeatCount="indefinite" begin="0.3s" />
          </line>
          <line x1="85" y1="180" x2="210" y2="125" stroke="#94a3b8" strokeWidth="2.5" strokeLinecap="round" markerEnd="url(#arrow)">
            <animate attributeName="opacity" values="0.5;1;0.5" dur="2s" repeatCount="indefinite" begin="0.6s" />
          </line>
        </g>

        {/* Central Prism with 3D effect and AI label */}
        <g transform="translate(220, 50)" filter="url(#drop-shadow)">
          {/* Main prism body */}
          <polygon points="80,0 160,140 0,140" fill="url(#prism-main)" />
          {/* Highlight face for 3D */}
          <polygon points="80,0 160,140 80,140" fill="url(#prism-shadow)" />
          {/* Top highlight edge */}
          <polygon points="80,0 110,70 50,70" fill="url(#prism-highlight)" />
          {/* Border */}
          <polygon points="80,0 160,140 0,140" fill="none" stroke="rgba(255,255,255,0.5)" strokeWidth="2" />
          
          {/* AI Label inside prism */}
          <text x="80" y="95" textAnchor="middle" fontSize="24" fontWeight="700" fill="white" opacity="0.9" style={{ fontFamily: 'system-ui' }}>
            AI
          </text>
          
          {/* Inner glow */}
          <circle cx="80" cy="90" r="30" fill="white" opacity="0.1">
            <animate attributeName="r" values="25;35;25" dur="3s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.08;0.15;0.08" dur="3s" repeatCount="indefinite" />
          </circle>
        </g>

        {/* Rainbow output rays with staggered animations */}
        <g transform="translate(380, 120)" filter="url(#glow-soft)">
          {/* Red */}
          <line x1="0" y1="0" x2="180" y2="-80" stroke="url(#ray-red)" strokeWidth="4" strokeLinecap="round">
            <animate attributeName="x2" values="170;190;170" dur="2s" repeatCount="indefinite" />
          </line>
          {/* Orange */}
          <line x1="0" y1="0" x2="190" y2="-55" stroke="url(#ray-orange)" strokeWidth="4" strokeLinecap="round">
            <animate attributeName="x2" values="180;200;180" dur="2s" repeatCount="indefinite" begin="0.1s" />
          </line>
          {/* Yellow */}
          <line x1="0" y1="0" x2="195" y2="-28" stroke="url(#ray-yellow)" strokeWidth="4" strokeLinecap="round">
            <animate attributeName="x2" values="185;205;185" dur="2s" repeatCount="indefinite" begin="0.2s" />
          </line>
          {/* Green */}
          <line x1="0" y1="0" x2="200" y2="0" stroke="url(#ray-green)" strokeWidth="4" strokeLinecap="round">
            <animate attributeName="x2" values="190;210;190" dur="2s" repeatCount="indefinite" begin="0.3s" />
          </line>
          {/* Cyan */}
          <line x1="0" y1="0" x2="195" y2="28" stroke="url(#ray-cyan)" strokeWidth="4" strokeLinecap="round">
            <animate attributeName="x2" values="185;205;185" dur="2s" repeatCount="indefinite" begin="0.4s" />
          </line>
          {/* Blue */}
          <line x1="0" y1="0" x2="190" y2="55" stroke="url(#ray-blue)" strokeWidth="4" strokeLinecap="round">
            <animate attributeName="x2" values="180;200;180" dur="2s" repeatCount="indefinite" begin="0.5s" />
          </line>
          {/* Violet */}
          <line x1="0" y1="0" x2="180" y2="80" stroke="url(#ray-violet)" strokeWidth="4" strokeLinecap="round">
            <animate attributeName="x2" values="170;190;170" dur="2s" repeatCount="indefinite" begin="0.6s" />
          </line>
        </g>

        {/* Output labels with icons */}
        <g style={{ fontFamily: 'system-ui' }}>
          {/* PDF Report - Document icon */}
          <g transform="translate(565, 35)">
            <rect x="0" y="0" width="10" height="12" rx="1" fill="none" stroke="#ef4444" strokeWidth="1" />
            <line x1="2" y1="4" x2="8" y2="4" stroke="#ef4444" strokeWidth="0.8" />
            <line x1="2" y1="6" x2="7" y2="6" stroke="#ef4444" strokeWidth="0.6" />
            <line x1="2" y1="8" x2="6" y2="8" stroke="#ef4444" strokeWidth="0.6" />
          </g>
          <text x="560" y="45" textAnchor="end" fontSize="11" fontWeight="600" fill="#ef4444">PDF Report</text>
          
          {/* Slides - Presentation icon */}
          <g transform="translate(573, 60)">
            <rect x="0" y="0" width="12" height="9" rx="1" fill="none" stroke="#f97316" strokeWidth="1" />
            <circle cx="6" cy="4.5" r="2" fill="none" stroke="#f97316" strokeWidth="0.8" />
          </g>
          <text x="568" y="70" textAnchor="end" fontSize="11" fontWeight="600" fill="#f97316">Slides</text>
          
          {/* Markdown - Code icon */}
          <g transform="translate(578, 85)">
            <rect x="0" y="0" width="12" height="10" rx="1" fill="none" stroke="#eab308" strokeWidth="1" />
            <text x="6" y="8" textAnchor="middle" fontSize="6" fontWeight="700" fill="#eab308">M↓</text>
          </g>
          <text x="573" y="95" textAnchor="end" fontSize="11" fontWeight="600" fill="#eab308">Markdown</text>
          
          {/* Blog Post - Pencil/Edit icon */}
          <g transform="translate(583, 110)">
            <path d="M0 10 L2 8 L10 0 L12 2 L4 10 L0 12 Z" fill="none" stroke="#22c55e" strokeWidth="1" strokeLinejoin="round" />
          </g>
          <text x="578" y="120" textAnchor="end" fontSize="11" fontWeight="600" fill="#22c55e">Blog Post</text>
          
          {/* Mind Map - Network icon */}
          <g transform="translate(578, 135)">
            <circle cx="6" cy="5" r="2.5" fill="none" stroke="#06b6d4" strokeWidth="1" />
            <circle cx="1" cy="9" r="1.5" fill="none" stroke="#06b6d4" strokeWidth="0.8" />
            <circle cx="11" cy="9" r="1.5" fill="none" stroke="#06b6d4" strokeWidth="0.8" />
            <line x1="4" y1="7" x2="2" y2="8" stroke="#06b6d4" strokeWidth="0.8" />
            <line x1="8" y1="7" x2="10" y2="8" stroke="#06b6d4" strokeWidth="0.8" />
          </g>
          <text x="573" y="145" textAnchor="end" fontSize="11" fontWeight="600" fill="#06b6d4">Mind Map</text>
          
          {/* FAQ Cards - Question icon */}
          <g transform="translate(573, 160)">
            <rect x="0" y="0" width="10" height="12" rx="1" fill="none" stroke="#3b82f6" strokeWidth="1" />
            <text x="5" y="9" textAnchor="middle" fontSize="8" fontWeight="700" fill="#3b82f6">?</text>
          </g>
          <text x="568" y="170" textAnchor="end" fontSize="11" fontWeight="600" fill="#3b82f6">FAQ Cards</text>
          
          {/* Podcast - Microphone icon */}
          <g transform="translate(565, 183)">
            <ellipse cx="5" cy="4" rx="3" ry="4" fill="none" stroke="#8b5cf6" strokeWidth="1" />
            <path d="M0 6 Q0 11 5 11 Q10 11 10 6" fill="none" stroke="#8b5cf6" strokeWidth="0.8" />
            <line x1="5" y1="11" x2="5" y2="14" stroke="#8b5cf6" strokeWidth="0.8" />
            <line x1="2" y1="14" x2="8" y2="14" stroke="#8b5cf6" strokeWidth="0.8" />
          </g>
          <text x="560" y="195" textAnchor="end" fontSize="11" fontWeight="600" fill="#8b5cf6">Podcast</text>
        </g>
      </svg>
    </div>
  );
}


export default function HomePage() {
  return (
    <div className="relative overflow-hidden">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 md:py-28">
        <div className="flex flex-col items-center text-center space-y-8 max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="inline-flex items-center rounded-full border px-4 py-1.5 text-sm font-medium bg-gradient-to-r from-cyan-50 to-fuchsia-50 dark:from-cyan-950/50 dark:to-fuchsia-950/50 border-violet-200 dark:border-violet-800">
            <span className="bg-gradient-to-r from-cyan-600 via-violet-600 to-fuchsia-600 bg-clip-text text-transparent">
              AI-Powered Document Generation
            </span>
          </div>

          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl max-w-4xl">
            Multiple Sources.{" "}
            <span className="bg-gradient-to-r from-cyan-500 via-violet-500 to-fuchsia-500 bg-clip-text text-transparent">
              Many Formats.
            </span>
          </h1>

          <p className="text-lg text-muted-foreground max-w-2xl md:text-xl leading-relaxed">
            Transform PDFs, URLs, and documents into professional reports,
            presentations, mind maps, and more. Bring your own LLM API key
            and watch your content refract into any format.
          </p>

          <div className="flex flex-col gap-4 sm:flex-row">
            <Button asChild size="lg" className="h-12 px-8 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700">
              <Link href="/generate">Start Generating</Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="h-12 px-8">
              <a href="https://github.com/nitishkmr005/PrismDocs" target="_blank" rel="noopener noreferrer">
                View on GitHub
              </a>
            </Button>
          </div>
        </div>

        {/* Refraction Illustration */}
        <div className="mt-16 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-300">
          <RefractionIllustration />
        </div>
      </section>

      {/* How It Works Section */}
      <section className="container mx-auto px-4 py-16 border-t">
        <h2 className="text-2xl font-bold text-center mb-4">
          How It Works
        </h2>
        <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
          Like light through a prism, your content refracts into multiple professional formats
        </p>

        <div className="grid gap-6 md:grid-cols-3 max-w-5xl mx-auto">
          {/* Input Card */}
          <div className="group relative flex flex-col items-center text-center space-y-4 p-6 rounded-xl border bg-card transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/10 hover:-translate-y-1">
            <div className="h-14 w-14 rounded-xl bg-gradient-to-br from-cyan-100 to-cyan-50 dark:from-cyan-900/50 dark:to-cyan-950/50 flex items-center justify-center">
              <svg className="h-7 w-7 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold">Any Source</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Upload PDFs, Word docs, images, or paste URLs and plain text. We parse and understand it all.
            </p>
            <div className="flex flex-wrap justify-center gap-2 pt-2">
              <span className="px-2 py-1 text-xs rounded-full bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300">PDF</span>
              <span className="px-2 py-1 text-xs rounded-full bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300">URL</span>
              <span className="px-2 py-1 text-xs rounded-full bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300">DOCX</span>
              <span className="px-2 py-1 text-xs rounded-full bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300">Images</span>
            </div>
            {/* Connector arrow (hidden on mobile) */}
            <div className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 text-muted-foreground/30">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>

          {/* Transform Card */}
          <div className="group relative flex flex-col items-center text-center space-y-4 p-6 rounded-xl border bg-card transition-all duration-300 hover:shadow-lg hover:shadow-violet-500/10 hover:-translate-y-1">
            <div className="h-14 w-14 rounded-xl bg-gradient-to-br from-violet-100 to-violet-50 dark:from-violet-900/50 dark:to-violet-950/50 flex items-center justify-center">
              <svg className="h-7 w-7 text-violet-600" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <polygon points="12,2 22,20 2,20" strokeWidth={2} strokeLinejoin="round" />
                <circle cx="12" cy="14" r="2" fill="currentColor" stroke="none" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold">AI</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Your content passes through our AI-powered prism, transforming and restructuring intelligently.
            </p>
            <div className="flex flex-wrap justify-center gap-2 pt-2">
              <span className="px-2 py-1 text-xs rounded-full bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300">Claude</span>
              <span className="px-2 py-1 text-xs rounded-full bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300">Gemini</span>
              <span className="px-2 py-1 text-xs rounded-full bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300">OpenAI</span>
            </div>
            {/* Connector arrow (hidden on mobile) */}
            <div className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 text-muted-foreground/30">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>

          {/* Output Card */}
          <div className="group flex flex-col items-center text-center space-y-4 p-6 rounded-xl border bg-card transition-all duration-300 hover:shadow-lg hover:shadow-fuchsia-500/10 hover:-translate-y-1">
            <div className="h-14 w-14 rounded-xl bg-gradient-to-br from-fuchsia-100 to-fuchsia-50 dark:from-fuchsia-900/50 dark:to-fuchsia-950/50 flex items-center justify-center">
              <svg className="h-7 w-7 text-fuchsia-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold">Many Formats</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Download your content refracted into multiple professional formats, ready to share.
            </p>
            <div className="flex flex-wrap justify-center gap-2 pt-2">
              <span className="px-2 py-1 text-xs rounded-full bg-fuchsia-100 dark:bg-fuchsia-900/30 text-fuchsia-700 dark:text-fuchsia-300">PDF</span>
              <span className="px-2 py-1 text-xs rounded-full bg-fuchsia-100 dark:bg-fuchsia-900/30 text-fuchsia-700 dark:text-fuchsia-300">PPTX</span>
              <span className="px-2 py-1 text-xs rounded-full bg-fuchsia-100 dark:bg-fuchsia-900/30 text-fuchsia-700 dark:text-fuchsia-300">Mind Map</span>
              <span className="px-2 py-1 text-xs rounded-full bg-fuchsia-100 dark:bg-fuchsia-900/30 text-fuchsia-700 dark:text-fuchsia-300">Podcast</span>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="container mx-auto px-4 py-16 border-t">
        <h2 className="text-2xl font-bold text-center mb-4">
          Built for Everyone
        </h2>
        <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
          From executives to developers, PrismDocs transforms how you create content
        </p>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto">
          {/* Executives */}
          <div className="group relative flex flex-col space-y-3 p-6 rounded-xl border bg-card transition-all duration-300 hover:shadow-lg hover:shadow-amber-500/10 hover:-translate-y-1 overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-amber-100/50 dark:from-amber-900/20 to-transparent rounded-bl-full" />
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-amber-100 to-amber-50 dark:from-amber-900/50 dark:to-amber-950/50 flex items-center justify-center text-2xl">
                👨‍💼
              </div>
              <h3 className="text-lg font-semibold">Executives</h3>
            </div>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Generate compelling pitch decks, board presentations, and executive summaries from research documents in minutes.
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              <span className="px-2 py-1 text-xs rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300">Pitch Decks</span>
              <span className="px-2 py-1 text-xs rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300">Reports</span>
            </div>
          </div>

          {/* Researchers */}
          <div className="group relative flex flex-col space-y-3 p-6 rounded-xl border bg-card transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10 hover:-translate-y-1 overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-blue-100/50 dark:from-blue-900/20 to-transparent rounded-bl-full" />
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-blue-100 to-blue-50 dark:from-blue-900/50 dark:to-blue-950/50 flex items-center justify-center text-2xl">
                🎓
              </div>
              <h3 className="text-lg font-semibold">Researchers</h3>
            </div>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Transform papers into study guides, mind maps, and visual summaries. Perfect for literature reviews and knowledge synthesis.
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              <span className="px-2 py-1 text-xs rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">Study Guides</span>
              <span className="px-2 py-1 text-xs rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">Mind Maps</span>
            </div>
          </div>

          {/* Job Seekers */}
          <div className="group relative flex flex-col space-y-3 p-6 rounded-xl border bg-card transition-all duration-300 hover:shadow-lg hover:shadow-green-500/10 hover:-translate-y-1 overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-green-100/50 dark:from-green-900/20 to-transparent rounded-bl-full" />
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-green-100 to-green-50 dark:from-green-900/50 dark:to-green-950/50 flex items-center justify-center text-2xl">
                💼
              </div>
              <h3 className="text-lg font-semibold">Job Seekers</h3>
            </div>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Turn your experience into polished resumes, portfolios, and cover letters tailored for any industry.
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              <span className="px-2 py-1 text-xs rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300">Resumes</span>
              <span className="px-2 py-1 text-xs rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300">Portfolios</span>
            </div>
          </div>

          {/* Content Creators */}
          <div className="group relative flex flex-col space-y-3 p-6 rounded-xl border bg-card transition-all duration-300 hover:shadow-lg hover:shadow-pink-500/10 hover:-translate-y-1 overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-pink-100/50 dark:from-pink-900/20 to-transparent rounded-bl-full" />
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-pink-100 to-pink-50 dark:from-pink-900/50 dark:to-pink-950/50 flex items-center justify-center text-2xl">
                🎨
              </div>
              <h3 className="text-lg font-semibold">Content Creators</h3>
            </div>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Convert blog posts into podcasts, create visual content from scripts, and repurpose content across formats.
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              <span className="px-2 py-1 text-xs rounded-full bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300">Podcasts</span>
              <span className="px-2 py-1 text-xs rounded-full bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300">Blogs</span>
            </div>
          </div>

          {/* Developers */}
          <div className="group relative flex flex-col space-y-3 p-6 rounded-xl border bg-card transition-all duration-300 hover:shadow-lg hover:shadow-violet-500/10 hover:-translate-y-1 overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-violet-100/50 dark:from-violet-900/20 to-transparent rounded-bl-full" />
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-violet-100 to-violet-50 dark:from-violet-900/50 dark:to-violet-950/50 flex items-center justify-center text-2xl">
                👨‍💻
              </div>
              <h3 className="text-lg font-semibold">Developers</h3>
            </div>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Generate technical documentation, API guides, and architecture diagrams from code comments and specs.
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              <span className="px-2 py-1 text-xs rounded-full bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300">Docs</span>
              <span className="px-2 py-1 text-xs rounded-full bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300">API Guides</span>
            </div>
          </div>

          {/* Educators */}
          <div className="group relative flex flex-col space-y-3 p-6 rounded-xl border bg-card transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/10 hover:-translate-y-1 overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-cyan-100/50 dark:from-cyan-900/20 to-transparent rounded-bl-full" />
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-cyan-100 to-cyan-50 dark:from-cyan-900/50 dark:to-cyan-950/50 flex items-center justify-center text-2xl">
                📚
              </div>
              <h3 className="text-lg font-semibold">Educators</h3>
            </div>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Create lesson plans, slideshows, and handouts from textbooks. Transform curriculum into engaging materials.
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              <span className="px-2 py-1 text-xs rounded-full bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300">Slides</span>
              <span className="px-2 py-1 text-xs rounded-full bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300">Handouts</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid Section */}
      <section className="container mx-auto px-4 py-16 border-t">
        <h2 className="text-2xl font-bold text-center mb-4">
          Why Choose PrismDocs?
        </h2>
        <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
          Enterprise-grade features with complete privacy and control
        </p>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 max-w-6xl mx-auto">
          {/* BYO API Keys */}
          <div className="group flex flex-col items-center text-center space-y-4 p-6 rounded-xl border bg-card transition-all duration-300 hover:shadow-lg hover:border-emerald-300 dark:hover:border-emerald-700">
            <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/25">
              <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold">BYO API Keys</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Your data stays private. Use your own LLM API keys – we never store or access your content.
            </p>
          </div>

          {/* Fast Generation */}
          <div className="group flex flex-col items-center text-center space-y-4 p-6 rounded-xl border bg-card transition-all duration-300 hover:shadow-lg hover:border-amber-300 dark:hover:border-amber-700">
            <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/25">
              <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold">Fast Generation</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Documents in seconds, not minutes. Optimized pipeline for rapid content transformation.
            </p>
          </div>

          {/* AI Images */}
          <div className="group flex flex-col items-center text-center space-y-4 p-6 rounded-xl border bg-card transition-all duration-300 hover:shadow-lg hover:border-violet-300 dark:hover:border-violet-700">
            <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/25">
              <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold">AI Images</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Auto-generated visuals that match your content. No more searching for stock photos.
            </p>
          </div>

          {/* Multi-format */}
          <div className="group flex flex-col items-center text-center space-y-4 p-6 rounded-xl border bg-card transition-all duration-300 hover:shadow-lg hover:border-blue-300 dark:hover:border-blue-700">
            <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
              <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold">Multi-format</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              PDF, PPTX, Markdown, Mind Maps, Podcasts – one input source, endless output possibilities.
            </p>
          </div>
        </div>

        {/* Additional Feature Pills */}
        <div className="flex flex-wrap justify-center gap-3 mt-10 max-w-4xl mx-auto">
          <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-slate-100 to-slate-50 dark:from-slate-800 dark:to-slate-900 border text-sm font-medium">
            <span className="text-emerald-500">✓</span> No usage limits
          </span>
          <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-slate-100 to-slate-50 dark:from-slate-800 dark:to-slate-900 border text-sm font-medium">
            <span className="text-emerald-500">✓</span> Pay only for LLM tokens
          </span>
          <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-slate-100 to-slate-50 dark:from-slate-800 dark:to-slate-900 border text-sm font-medium">
            <span className="text-emerald-500">✓</span> Open Source
          </span>
          <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-slate-100 to-slate-50 dark:from-slate-800 dark:to-slate-900 border text-sm font-medium">
            <span className="text-emerald-500">✓</span> MIT License
          </span>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="max-w-2xl mx-auto text-center space-y-6 p-8 rounded-2xl bg-gradient-to-br from-violet-50 to-fuchsia-50 dark:from-violet-950/30 dark:to-fuchsia-950/30 border border-violet-100 dark:border-violet-900/50">
          <h2 className="text-2xl font-bold">Ready to transform your content?</h2>
          <p className="text-muted-foreground">
            Bring your own API key and start generating professional documents in seconds.
          </p>
          <Button asChild size="lg" className="h-12 px-8 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700">
            <Link href="/generate">Get Started Free</Link>
          </Button>
        </div>
      </section>
    </div>
  );
}
