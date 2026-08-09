import { Reveal } from "@/components/landing/reveal";

export function Problem() {
  return (
    <section id="problem" className="border-t border-border py-24 sm:py-32">
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <Reveal>
          <h2 className="max-w-[18ch] font-display text-3xl font-semibold leading-[1.1] tracking-[-0.025em] sm:text-5xl">
            A percentage is not a decision.
          </h2>
        </Reveal>

        <Reveal delay={0.08}>
          <p className="mt-7 max-w-[62ch] text-lg leading-relaxed text-muted-foreground">
            Sentiment scoring reports that 68% of your feedback is negative. No
            product manager has ever changed a roadmap because of that number.
            What you can act on is a theme with volume, trajectory, and blast
            radius.
          </p>
        </Reveal>

        <Reveal delay={0.14}>
          <div className="mt-14 grid gap-px overflow-hidden rounded-lg border bg-border md:grid-cols-2">
            <div className="bg-surface p-7 sm:p-9">
              <p className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
                Example
              </p>
              <p className="mt-5 font-mono text-2xl text-muted-foreground tabular">
                68% negative
              </p>
              <p className="mt-5 text-sm leading-relaxed text-muted-foreground">
                True, and useless. It names no problem, no owner, and no fix.
                You cannot file it.
              </p>
            </div>

            <div className="bg-surface-2 p-7 sm:p-9">
              <p className="font-mono text-xs uppercase tracking-widest text-primary">
                Example
              </p>
              <p className="mt-5 font-display text-2xl font-semibold leading-snug tracking-tight">
                Signup fails for enterprise accounts
              </p>
              <p className="mt-3 font-mono text-sm text-muted-foreground tabular">
                34 mentions <span className="text-signal-up">3.0x this week</span>{" "}
                9 paid
              </p>
              <p className="mt-5 text-sm leading-relaxed text-foreground/80">
                Same feedback, counted. This one gets a ticket before lunch.
              </p>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
