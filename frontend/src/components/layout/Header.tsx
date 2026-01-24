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
        {/* Amber gradient for prism */}
        <linearGradient id="header-prism-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: '#f59e0b' }} />
          <stop offset="50%" style={{ stopColor: '#d97706' }} />
          <stop offset="100%" style={{ stopColor: '#b45309' }} />
        </linearGradient>
        <linearGradient id="header-doc-fill" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: '#f8fafc' }} />
          <stop offset="100%" style={{ stopColor: '#f1f5f9' }} />
        </linearGradient>
        {/* Output rays - warm palette */}
        <linearGradient id="header-ray-1" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style={{ stopColor: '#f59e0b' }} />
          <stop offset="100%" style={{ stopColor: '#f59e0b', stopOpacity: 0 }} />
        </linearGradient>
        <linearGradient id="header-ray-2" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style={{ stopColor: '#ef4444' }} />
          <stop offset="100%" style={{ stopColor: '#ef4444', stopOpacity: 0 }} />
        </linearGradient>
        <linearGradient id="header-ray-3" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style={{ stopColor: '#22c55e' }} />
          <stop offset="100%" style={{ stopColor: '#22c55e', stopOpacity: 0 }} />
        </linearGradient>
        <linearGradient id="header-ray-4" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style={{ stopColor: '#3b82f6' }} />
          <stop offset="100%" style={{ stopColor: '#3b82f6', stopOpacity: 0 }} />
        </linearGradient>
        <linearGradient id="header-ray-5" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style={{ stopColor: '#a855f7' }} />
          <stop offset="100%" style={{ stopColor: '#a855f7', stopOpacity: 0 }} />
        </linearGradient>
      </defs>
      <g transform="translate(6, 8)">
        {/* Document shape */}
        <path
          d="M0 4 C0 1.8 1.8 0 4 0 L24 0 L32 8 L32 44 C32 46.2 30.2 48 28 48 L4 48 C1.8 48 0 46.2 0 44 Z"
          fill="url(#header-doc-fill)"
          stroke="url(#header-prism-gradient)"
          strokeWidth="2"
        />
        <path d="M24 0 L24 8 L32 8" fill="none" stroke="url(#header-prism-gradient)" strokeWidth="2" strokeLinejoin="round" />
        <path d="M24 0 L24 8 L32 8 Z" fill="#f1f5f9" />
        {/* Document lines */}
        <rect x="6" y="16" width="20" height="2.5" rx="1" fill="#94a3b8" />
        <rect x="6" y="22" width="16" height="2.5" rx="1" fill="#94a3b8" />
        <rect x="6" y="28" width="18" height="2.5" rx="1" fill="#94a3b8" />
        {/* Prism */}
        <path d="M12 34 L22 48 L2 48 Z" fill="url(#header-prism-gradient)" opacity="0.95" />
      </g>
      {/* Output rays */}
      <g transform="translate(38, 32)">
        <line x1="0" y1="0" x2="22" y2="-18" stroke="url(#header-ray-2)" strokeWidth="3" strokeLinecap="round" />
        <line x1="0" y1="0" x2="24" y2="-8" stroke="url(#header-ray-1)" strokeWidth="3" strokeLinecap="round" />
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
      <header className="sticky top-0 z-50 w-full border-b border-slate-200/60 dark:border-slate-800/60 bg-white/80 dark:bg-slate-950/80 backdrop-blur-xl supports-[backdrop-filter]:bg-white/60 dark:supports-[backdrop-filter]:bg-slate-950/60">
        <div className="container mx-auto px-4 flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <PrismDocsLogo className="transition-transform duration-300 group-hover:scale-110" />
            <span className="font-display font-semibold text-lg tracking-tight text-slate-900 dark:text-white">
              Prism<span className="text-amber-500">Docs</span>
            </span>
          </Link>

          <nav className="flex items-center gap-3">
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
