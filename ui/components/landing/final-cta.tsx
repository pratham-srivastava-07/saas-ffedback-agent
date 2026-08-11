import Link from "next/link";

import { Button } from "@/components/ui/button";

/**
 * The closing ask.
 *
 * One statement, one primary action, one honest qualifier. The page has
 * already shown the product; this is not the place to re-argue it.
 */
export function FinalCta() {
  return (
    <section className="relative isolate border-t border-border px-5 py-24 sm:px-8">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            "radial-gradient(44rem 18rem at 50% 100%, var(--color-primary), transparent 70%)",
          opacity: 0.07,
        }}
      />

      <div className="mx-auto max-w-2xl text-center">
        <h2 className="font-display text-3xl font-semibold leading-tight tracking-[-0.02em] text-balance sm:text-4xl">
          Find out what your customers actually keep saying.
        </h2>
        <p className="mx-auto mt-4 max-w-[46ch] text-base leading-relaxed text-muted-foreground">
          Paste a batch of feedback and read the ranked list. No connectors to
          configure first.
        </p>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Button asChild size="lg">
            <Link href="/signup">Create account</Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link href="/login">Sign in</Link>
          </Button>
        </div>

        {/* Stated plainly rather than buried: trends need history, and a
            first run cannot have any. */}
        <p className="mt-6 font-mono text-[11px] text-muted-foreground">
          Trend detection needs three prior runs before it will call anything.
        </p>
      </div>
    </section>
  );
}
