import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border/40 py-8 bg-gradient-to-b from-transparent to-violet-50/30 dark:to-violet-950/10">
      <div className="container mx-auto flex flex-col items-center justify-center gap-4 text-center">
        <div className="flex items-center gap-1 text-sm font-medium">
          <span className="text-muted-foreground">Built with</span>
          <span className="bg-gradient-to-r from-cyan-600 via-violet-600 to-fuchsia-600 bg-clip-text text-transparent">
            PrismDocs
          </span>
        </div>
        <div className="flex items-center gap-4">
          <Link
            href="https://github.com/nitishkmr005/PrismDocs"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-muted-foreground hover:text-violet-600 transition-colors"
          >
            GitHub
          </Link>
          <span className="text-muted-foreground/40">•</span>
          <Link
            href="/generate"
            className="text-sm text-muted-foreground hover:text-violet-600 transition-colors"
          >
            Get Started
          </Link>
        </div>
        <p className="text-xs text-muted-foreground/50" suppressHydrationWarning>
          © 2026 PrismDocs. Open source document generation.
        </p>
      </div>
    </footer>
  );
}
