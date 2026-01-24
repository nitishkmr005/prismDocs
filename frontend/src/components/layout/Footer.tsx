import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-slate-200/60 dark:border-slate-800/60 py-12 bg-slate-50/50 dark:bg-slate-900/50">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Brand */}
          <div className="flex items-center gap-2">
            <span className="font-display font-semibold text-slate-900 dark:text-white">
              Prism<span className="text-amber-500">Docs</span>
            </span>
            <span className="text-slate-400 dark:text-slate-600">|</span>
            <span className="mono-label text-slate-500 dark:text-slate-400">
              Document Generation
            </span>
          </div>

          {/* Links */}
          <div className="flex items-center gap-6">
            <Link
              href="https://github.com/nitishkmr005/PrismDocs"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-slate-600 dark:text-slate-400 hover:text-amber-600 dark:hover:text-amber-400 transition-colors"
            >
              GitHub
            </Link>
            <Link
              href="/generate"
              className="text-sm text-slate-600 dark:text-slate-400 hover:text-amber-600 dark:hover:text-amber-400 transition-colors"
            >
              Get Started
            </Link>
          </div>

          {/* Credits */}
          <div className="flex flex-col items-center md:items-end gap-1 text-xs text-slate-500 dark:text-slate-400">
            <p suppressHydrationWarning>
              © 2026 PrismDocs. Open source.
            </p>
            <p>
              Built by{" "}
              <Link
                href="https://github.com/nitishkmr005"
                target="_blank"
                rel="noopener noreferrer"
                className="text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 transition-colors font-medium"
              >
                Nitish Harsoor
              </Link>
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
