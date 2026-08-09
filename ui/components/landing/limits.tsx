import { Reveal } from "@/components/landing/reveal";

/**
 * Stating the limits plainly is the same discipline the product applies to its
 * own output: it reports "not enough history" rather than extrapolating a
 * trend from two data points.
 */
const LIMITS = [
  {
    title: "No connectors yet",
    body: "Zendesk, Intercom and App Store pulls are not built. You upload a CSV export or paste a batch.",
  },
  {
    title: "Trends need history",
    body: "With fewer than three prior runs a theme reports insufficient history instead of inventing a percentage.",
  },
  {
    title: "One workspace per account",
    body: "Themes and trends are scoped to a workspace. There are no teams, roles, or shared seats.",
  },
  {
    title: "Billing is not wired up",
    body: "The plans below describe intent, not a checkout. Nothing charges your card because nothing can.",
  },
];

export function Limits() {
  return (
    <section className="border-t border-border bg-surface-2/40 py-24 sm:py-32">
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <Reveal>
          <h2 className="max-w-[22ch] font-display text-3xl font-semibold leading-[1.1] tracking-[-0.025em] sm:text-4xl">
            What it does not do yet.
          </h2>
        </Reveal>

        <div className="mt-12 grid gap-x-14 gap-y-9 sm:grid-cols-2">
          {LIMITS.map((limit, index) => (
            <Reveal key={limit.title} delay={index * 0.06}>
              <h3 className="font-display text-base font-semibold tracking-tight">
                {limit.title}
              </h3>
              <p className="mt-2 max-w-[52ch] text-sm leading-relaxed text-muted-foreground">
                {limit.body}
              </p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
