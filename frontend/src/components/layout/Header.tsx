'use client'

import { useState } from 'react'
import Link from "next/link";
import { AuthButton, AuthModal } from "@/components/auth";
import { ThemeToggle } from "@/components/system/ThemeToggle";

function PrismDocsLogo({ className }: { className?: string }) {
  return (
    <svg
      width="32"
      height="32"
      viewBox="0 0 64 64"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id="header-prism-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: '#0891b2' }} />
          <stop offset="50%" style={{ stopColor: '#7c3aed' }} />
          <stop offset="100%" style={{ stopColor: '#c026d3' }} />
        </linearGradient>
        <linearGradient id="header-doc-fill" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: '#f8fafc' }} />
          <stop offset="100%" style={{ stopColor: '#f1f5f9' }} />
        </linearGradient>
        <linearGradient id="header-ray-1" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style={{ stopColor: '#06d6a0' }} />
          <stop offset="100%" style={{ stopColor: '#06d6a0', stopOpacity: 0 }} />
        </linearGradient>
        <linearGradient id="header-ray-2" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style={{ stopColor: '#0891b2' }} />
          <stop offset="100%" style={{ stopColor: '#0891b2', stopOpacity: 0 }} />
        </linearGradient>
        <linearGradient id="header-ray-3" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style={{ stopColor: '#7c3aed' }} />
          <stop offset="100%" style={{ stopColor: '#7c3aed', stopOpacity: 0 }} />
        </linearGradient>
        <linearGradient id="header-ray-4" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style={{ stopColor: '#c026d3' }} />
          <stop offset="100%" style={{ stopColor: '#c026d3', stopOpacity: 0 }} />
        </linearGradient>
        <linearGradient id="header-ray-5" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style={{ stopColor: '#e11d48' }} />
          <stop offset="100%" style={{ stopColor: '#e11d48', stopOpacity: 0 }} />
        </linearGradient>
      </defs>
      <g transform="translate(6, 8)">
        <path
          d="M0 4 C0 1.8 1.8 0 4 0 L24 0 L32 8 L32 44 C32 46.2 30.2 48 28 48 L4 48 C1.8 48 0 46.2 0 44 Z"
          fill="url(#header-doc-fill)"
          stroke="url(#header-prism-gradient)"
          strokeWidth="2"
        />
        <path d="M24 0 L24 8 L32 8" fill="none" stroke="url(#header-prism-gradient)" strokeWidth="2" strokeLinejoin="round" />
        <path d="M24 0 L24 8 L32 8 Z" fill="#f1f5f9" />
        <rect x="6" y="16" width="20" height="2.5" rx="1" fill="#94a3b8" />
        <rect x="6" y="22" width="16" height="2.5" rx="1" fill="#94a3b8" />
        <rect x="6" y="28" width="18" height="2.5" rx="1" fill="#94a3b8" />
        <path d="M12 34 L22 48 L2 48 Z" fill="url(#header-prism-gradient)" opacity="0.95" />
      </g>
      <g transform="translate(38, 32)">
        <line x1="0" y1="0" x2="22" y2="-18" stroke="url(#header-ray-1)" strokeWidth="3" strokeLinecap="round" />
        <line x1="0" y1="0" x2="24" y2="-8" stroke="url(#header-ray-2)" strokeWidth="3" strokeLinecap="round" />
        <line x1="0" y1="0" x2="24" y2="2" stroke="url(#header-ray-3)" strokeWidth="3" strokeLinecap="round" />
        <line x1="0" y1="0" x2="24" y2="12" stroke="url(#header-ray-4)" strokeWidth="3" strokeLinecap="round" />
        <line x1="0" y1="0" x2="20" y2="22" stroke="url(#header-ray-5)" strokeWidth="3" strokeLinecap="round" />
      </g>
    </svg>
  );
}

export function Header() {
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false)

  return (
    <>
      <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2 font-semibold text-lg">
            <PrismDocsLogo />
            <span className="bg-gradient-to-r from-cyan-600 via-violet-600 to-fuchsia-600 bg-clip-text text-transparent font-bold">
              PrismDocs
            </span>
          </Link>

          <nav className="flex items-center gap-4">
            <ThemeToggle />
            <AuthButton onSignInClick={() => setIsAuthModalOpen(true)} />
          </nav>
        </div>
      </header>
      <AuthModal 
        isOpen={isAuthModalOpen} 
        onClose={() => setIsAuthModalOpen(false)} 
      />
    </>
  );
}
