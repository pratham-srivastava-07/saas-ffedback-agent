import { Reveal } from "@/components/landing/reveal";

/**
 * The pipeline is a genuine sequence, which is the only condition under which
 * ordered presentation carries information rather than decorating.
 */
const STAGES = [
  {
    title: "Clean",
    body: "Duplicate submissions and noise are dropped before anything reaches a model. Different wording for the same bug is kept, because that is two mentions, not one.",
    nodes: ["normalize", "triage"],
  },
  {
    title: "Read",
    body: "One structured pass per item returns sentiment, intent, severity, feature area, and whether the customer signalled they may leave.",
    nodes: ["analyze", "embed"],
  },
  {
    title: "Group",
    body: "Items cluster by meaning rather than keywords, then match against themes already on file, so a recurring problem keeps the name it had last month.",
    nodes: ["cluster", "resolve_taxonomy", "name_themes"],
  },
  {
    title: "Rank",
    body: "Impact combines how many people are affected, how badly, and what they are worth. A critic then audits the recommendations against the evidence.",
    nodes: ["prioritize", "detect_trends", "recommend", "critique"],
  },
];

export function Pipeline() {
  return (
    <section id="pipeline" className="border-t border-border bg-surface-2/40 py-24 sm:py-32">
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <Reveal>
          <h2 className="max-w-[20ch] font-display text-3xl font-semibold leading-[1.1] tracking-[-0.025em] sm:text-5xl">
            Four stages, and it shows its work.
          </h2>
        </Reveal>

        <div className="mt-16 grid gap-x-10 gap-y-12 sm:grid-cols-2 lg:grid-cols-4">
          {STAGES.map((stage, index) => (
            <Reveal key={stage.title} delay={index * 0.07}>
              <div className="relative">
                <div className="flex items-baseline gap-3 border-b border-border pb-3">
                  <span className="font-mono text-xs text-muted-foreground tabular">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <h3 className="font-display text-xl font-semibold tracking-tight">
                    {stage.title}
                  </h3>
                </div>

                <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                  {stage.body}
                </p>

                <ul className="mt-5 flex flex-wrap gap-1.5">
                  {stage.nodes.map((node) => (
                    <li
                      key={node}
                      className="rounded border border-border bg-surface px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground"
                    >
                      {node}
                    </li>
                  ))}
                </ul>
              </div>
            </Reveal>
          ))}
        </div>

        <Reveal delay={0.1}>
          <p className="mt-14 max-w-[64ch] border-l-2 border-primary/60 pl-5 text-sm leading-relaxed text-muted-foreground">
            You watch this happen. Every stage reports as it finishes, so a run
            is a sequence of results arriving rather than a spinner and a wait.
          </p>
        </Reveal>
      </div>
    </section>
  );
}
