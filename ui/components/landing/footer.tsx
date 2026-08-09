import Link from "next/link";

import { Logo } from "@/components/logo";

export function Footer() {
  return (
    <footer className="border-t border-border py-12">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-5 sm:flex-row sm:items-center sm:justify-between sm:px-8">
        <div className="flex items-center gap-2.5">
          <Logo className="size-5" />
          <span className="font-display text-sm font-semibold tracking-tight">
            Sentilytics
          </span>
        </div>

        <nav className="flex flex-wrap items-center gap-6" aria-label="Footer">
          <a
            href="#problem"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            Why
          </a>
          <a
            href="#pipeline"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            How it works
          </a>
          <a
            href="#pricing"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            Pricing
          </a>
          <Link
            href="/login"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            Sign in
          </Link>
        </nav>
      </div>
    </footer>
  );
}
