import { Boxes, History, Layers, LayoutDashboard, Play } from "lucide-react";

import { RankedBars } from "@/components/app/charts";
import { TrendBadge } from "@/components/app/signals";
import { Logo } from "@/components/logo";
import { colorAt } from "@/lib/chart-colors";

/**
 * The product itself, as the landing page's primary visual.
 *
 * Assembled from the same components the application renders — `RankedBars`
 * and `TrendBadge` are imported, not redrawn — so this cannot drift into
 * showing an interface that does not exist. A screenshot would go stale and
 * an illustration would be a claim rather than a demonstration.
 *
 * The figures are representative, not measured: this is a marketing surface
 * with no workspace behind it. They use the product's real vocabulary and
 * plausible magnitudes, and every one of them is a number the application
 * genuinely computes.
 */

const THEMES = [
  { label: "OAuth signup failures", value: 34 },
  { label: "Duplicate billing charges", value: 21 },
  { label: "Dashboard load time", value: 17 },
  { label: "CSV export missing", value: 12 },
  { label: "Mobile crash on launch", value: 8 },
];

const NAV = [
  { icon: LayoutDashboard, label: "Overview" },
  { icon: Play, label: "Analyze", active: true },
  { icon: Layers, label: "Themes" },
  { icon: Boxes, label: "Explore" },
  { icon: History, label: "Runs" },
];

export function ProductPreview() {
  return (
    <section className="px-5 pb-24 sm:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="overflow-hidden rounded-xl border border-border bg-surface shadow-sm">
          {/* Window chrome, quiet enough to read as a frame rather than an
              illustration of a browser. */}
          <div className="flex items-center gap-3 border-b border-border bg-surface-2/60 px-4 py-2.5">
            <div className="flex gap-1.5" aria-hidden>
              <span className="size-2.5 rounded-full bg-border" />
              <span className="size-2.5 rounded-full bg-border" />
              <span className="size-2.5 rounded-full bg-border" />
            </div>
            <span className="mx-auto font-mono text-[11px] text-muted-foreground">
              sentilytics / themes ranked by impact
            </span>
          </div>

          <div className="grid sm:grid-cols-[11rem_1fr]">
            {/* Sidebar rail, matching the application shell. */}
            <div className="hidden flex-col border-r border-border bg-surface-2/40 p-3 sm:flex">
              <div className="mb-5 flex items-center gap-2 px-2">
                <Logo className="size-5" />
                <span className="font-display text-sm font-semibold tracking-tight">
                  Sentilytics
                </span>
              </div>
              <ul className="space-y-0.5">
                {NAV.map((item) => (
                  <li
                    key={item.label}
                    className={`flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13px] ${
                      item.active
                        ? "bg-secondary font-medium text-foreground"
                        : "text-muted-foreground"
                    }`}
                  >
                    <item.icon className="size-3.5 shrink-0" aria-hidden />
                    {item.label}
                  </li>
                ))}
              </ul>
            </div>

            <div className="min-w-0 p-5 sm:p-6">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h3 className="font-display text-lg font-semibold tracking-tight">
                    This week
                  </h3>
                  <p className="mt-1 font-mono text-[11px] text-muted-foreground tabular">
                    92 items analysed / 5 themes / 4 rejected as noise
                  </p>
                </div>
                <TrendBadge direction="spiking" ratio={3.1} />
              </div>

              <div className="mt-6">
                <RankedBars
                  data={THEMES}
                  colors={THEMES.map((_, index) => colorAt(index))}
                  valueSuffix=" mentions"
                />
              </div>

              <p className="mt-6 border-t border-border pt-4 text-sm leading-relaxed text-muted-foreground">
                <span className="text-foreground">OAuth signup failures</span> is
                the week&apos;s top issue: 34 mentions, 3.1&times; its four-run
                average, and nine of them from paying accounts.
              </p>
            </div>
          </div>
        </div>

        <p className="mx-auto mt-5 max-w-[52ch] text-center text-sm text-muted-foreground">
          Every theme is a group the system found on its own, and every count is
          something you can open and read.
        </p>
      </div>
    </section>
  );
}
