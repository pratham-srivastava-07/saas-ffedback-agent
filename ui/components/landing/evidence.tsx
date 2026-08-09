import { Reveal } from "@/components/landing/reveal";
import { SentimentBar, SeverityMarks, TrendBadge } from "@/components/app/signals";

/**
 * Rendered with the same components the product uses, not a mock-up of them,
 * so what the page promises is literally what ships.
 *
 * The figures are illustrative and labelled as such.
 */
const EXAMPLE_QUOTES = [
  {
    text: "Cannot complete signup, OAuth fails every attempt. Blocked onboarding for ten people.",
    tier: "enterprise",
    source: "support",
  },
  {
    text: "Signup page throws a server error on submit. Third try today.",
    tier: "paid",
    source: "support",
  },
  {
    text: "Tried to sign up for a trial and it just fails silently.",
    tier: "free",
    source: "review",
  },
];

export function Evidence() {
  return (
    <section className="border-t border-border py-24 sm:py-32">
      <div className="mx-auto grid max-w-6xl items-start gap-12 px-5 sm:px-8 lg:grid-cols-12 lg:gap-16">
        <div className="lg:col-span-5">
          <Reveal>
            <h2 className="font-display text-3xl font-semibold leading-[1.1] tracking-[-0.025em] sm:text-4xl">
              Every count opens.
            </h2>
          </Reveal>
          <Reveal delay={0.08}>
            <p className="mt-6 text-lg leading-relaxed text-muted-foreground">
              A number you cannot inspect is a number you cannot defend in a
              planning meeting. Click any theme and read the feedback it was
              built from.
            </p>
          </Reveal>
          <Reveal delay={0.14}>
            <p className="mt-6 text-sm leading-relaxed text-muted-foreground">
              Themes persist between runs, so next week this one is compared
              against itself rather than being discovered again under a new
              name.
            </p>
          </Reveal>
        </div>

        <Reveal delay={0.1} className="lg:col-span-7">
          <div className="overflow-hidden rounded-lg border bg-surface">
            <div className="flex items-center justify-between border-b border-border px-5 py-2.5">
              <span className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                Example readout
              </span>
              <TrendBadge direction="spiking" ratio={3.0} />
            </div>

            <div className="p-5 sm:p-6">
              <div className="flex flex-wrap items-baseline justify-between gap-3">
                <h3 className="font-display text-xl font-semibold tracking-tight">
                  Signup fails for enterprise accounts
                </h3>
                <span className="font-mono text-sm text-muted-foreground tabular">
                  impact 66.4
                </span>
              </div>

              <div className="mt-5 grid gap-5 sm:grid-cols-3">
                <div>
                  <p className="text-xs text-muted-foreground">Mentions</p>
                  <p className="mt-1 font-mono text-2xl tabular">34</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Avg severity</p>
                  <p className="mt-1 flex items-center gap-2 font-mono text-2xl tabular">
                    4.4
                    <SeverityMarks severity={4} />
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Sentiment</p>
                  <SentimentBar
                    className="mt-2"
                    breakdown={{ positive: 1, neutral: 4, negative: 29 }}
                  />
                </div>
              </div>

              <div className="mt-7 border-t border-border pt-5">
                <p className="text-xs text-muted-foreground">The evidence</p>
                <ul className="mt-3 space-y-3">
                  {EXAMPLE_QUOTES.map((quote) => (
                    <li key={quote.text} className="flex gap-3">
                      <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-negative" />
                      <div className="min-w-0">
                        <p className="text-sm leading-snug text-foreground/90">
                          {quote.text}
                        </p>
                        <p className="mt-1 font-mono text-[11px] uppercase tracking-wide text-muted-foreground">
                          {quote.tier} / {quote.source}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
