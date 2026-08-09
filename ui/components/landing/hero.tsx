import Link from "next/link";

import { Button } from "@/components/ui/button";
import { HeroField } from "@/components/three/webgl-slot";

export function Hero() {
  return (
    <section className="relative isolate overflow-hidden">
      {/* The cloud sits to the right of the copy on desktop and behind it on
          mobile, where it drops to low opacity so text contrast survives. */}
      <HeroField className="pointer-events-none absolute inset-y-0 right-0 h-full w-full opacity-30 md:w-[62%] md:opacity-100" />

      <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-background via-background/85 to-transparent md:via-background/55" />

      <div className="relative mx-auto grid min-h-[calc(100dvh-4rem)] max-w-6xl items-center px-5 pt-16 pb-20 sm:px-8 md:grid-cols-12 md:pt-20">
        <div className="md:col-span-7 lg:col-span-6">
          <h1 className="font-display text-[2.6rem] font-semibold leading-[1.04] tracking-[-0.03em] text-balance sm:text-6xl">
            Your roadmap is set by whoever complained loudest.
          </h1>

          <p className="mt-6 max-w-[46ch] text-lg leading-relaxed text-muted-foreground">
            Sentilytics reads all your feedback and ranks what to fix by how many
            customers it actually affects.
          </p>

          <div className="mt-9 flex flex-wrap items-center gap-3">
            <Button asChild size="lg">
              <Link href="/signup">Create account</Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <a href="#pipeline">See how it works</a>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
