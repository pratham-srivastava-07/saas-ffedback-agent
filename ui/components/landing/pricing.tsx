import Link from "next/link";
import { Check } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Reveal } from "@/components/landing/reveal";

const PLANS = [
  {
    name: "Free",
    price: "$0",
    cadence: "while it is in development",
    description: "Everything works. Nothing is metered.",
    features: [
      "200 items per analysis",
      "Persistent theme taxonomy",
      "Trend detection across runs",
      "CSV upload and live streaming",
    ],
    emphasis: true,
  },
  {
    name: "Team",
    price: "Not available",
    cadence: "planned",
    description: "Shared workspaces and connectors, once they exist.",
    features: [
      "Multiple seats per workspace",
      "Zendesk and Intercom ingestion",
      "Scheduled runs and alerting",
      "Retention beyond the local database",
    ],
    emphasis: false,
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="border-t border-border py-24 sm:py-32">
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <Reveal>
          <h2 className="font-display text-3xl font-semibold leading-[1.1] tracking-[-0.025em] sm:text-4xl">
            Free, because there is no checkout.
          </h2>
          <p className="mt-5 max-w-[58ch] text-lg leading-relaxed text-muted-foreground">
            Billing has not been built. The second plan is a description of
            where this is going, not something you can buy today.
          </p>
        </Reveal>

        <div className="mt-14 grid gap-6 lg:grid-cols-2">
          {PLANS.map((plan, index) => (
            <Reveal key={plan.name} delay={index * 0.08}>
              <div
                className={
                  plan.emphasis
                    ? "h-full rounded-lg border-2 border-primary/60 bg-surface p-7 sm:p-9"
                    : "h-full rounded-lg border border-border bg-surface-2/50 p-7 sm:p-9"
                }
              >
                <h3 className="font-display text-lg font-semibold tracking-tight">
                  {plan.name}
                </h3>

                <p className="mt-5 flex items-baseline gap-2">
                  <span
                    className={
                      plan.emphasis
                        ? "font-display text-4xl font-semibold tracking-tight tabular"
                        : "font-display text-2xl font-semibold tracking-tight text-muted-foreground"
                    }
                  >
                    {plan.price}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {plan.cadence}
                  </span>
                </p>

                <p className="mt-3 text-sm text-muted-foreground">
                  {plan.description}
                </p>

                <ul className="mt-7 space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2.5 text-sm">
                      <Check
                        className={
                          plan.emphasis
                            ? "mt-0.5 size-4 shrink-0 text-primary"
                            : "mt-0.5 size-4 shrink-0 text-muted-foreground/60"
                        }
                        aria-hidden
                      />
                      <span
                        className={
                          plan.emphasis ? "" : "text-muted-foreground"
                        }
                      >
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>

                {plan.emphasis ? (
                  <Button asChild size="lg" className="mt-8 w-full">
                    <Link href="/signup">Create account</Link>
                  </Button>
                ) : (
                  <Button
                    size="lg"
                    variant="outline"
                    className="mt-8 w-full"
                    disabled
                  >
                    Not available yet
                  </Button>
                )}
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
