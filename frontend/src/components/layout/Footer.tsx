import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border/40 py-8">
      <div className="container mx-auto flex flex-col items-center justify-center gap-4 text-center">
        <div className="flex items-center gap-4">
          <Link
            href="https://github.com/nitishkmr005/document-generator"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-muted-foreground hover:text-primary transition-colors"
          >
            GitHub
          </Link>
          <span className="text-muted-foreground">•</span>
          <Link
            href="/generate"
            className="text-sm text-muted-foreground hover:text-primary transition-colors"
          >
            Get Started
          </Link>
        </div>
        <p className="text-xs text-muted-foreground/60" suppressHydrationWarning>
          © 2026 DocGen. Open source document generation.
        </p>
      </div>
    </footer>
  );
}
