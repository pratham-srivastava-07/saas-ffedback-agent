import Link from "next/link";

import { Logo } from "@/components/logo";
import { ThemeToggle } from "@/components/ui/theme-toggle";

/**
 * Split auth layout. The right panel carries the product's argument rather
 * than decoration, and is hidden on small screens where the form is the only
 * thing that matters.
 */
export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  footer: React.ReactNode;
}) {
  return (
    <div className="grid min-h-dvh lg:grid-cols-2">
      <div className="flex flex-col px-5 py-6 sm:px-10">
        <div className="flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-2.5 rounded-md focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ring"
          >
            <Logo className="size-6" />
            <span className="font-display text-[15px] font-semibold tracking-tight">
              Sentilytics
            </span>
          </Link>
          <ThemeToggle />
        </div>

        <div className="flex flex-1 items-center">
          <div className="mx-auto w-full max-w-sm py-12">
            <h1 className="font-display text-2xl font-semibold tracking-tight">
              {title}
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">{subtitle}</p>

            <div className="mt-8">{children}</div>

            <div className="mt-6 text-sm text-muted-foreground">{footer}</div>
          </div>
        </div>
      </div>

      <aside className="relative hidden border-l border-border bg-surface-2/50 lg:flex lg:flex-col lg:justify-center lg:px-14">
        <blockquote className="max-w-[38ch]">
          <p className="font-display text-2xl font-semibold leading-snug tracking-tight">
            Forty people reported the same bug in forty different ways.
          </p>
          <p className="mt-5 text-base leading-relaxed text-muted-foreground">
            That is forty mentions, not one. Counting them correctly is the
            whole job.
          </p>
        </blockquote>
      </aside>
    </div>
  );
}
