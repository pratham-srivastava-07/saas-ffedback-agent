# Sentilytics — Frontend Rules

> Single source of truth for visual and structural decisions in this frontend.
> Stack: Next.js 15 (App Router) + TypeScript + Tailwind v4 + shadcn/ui + Motion + three.js
> If a decision is not covered here, default to: **less is more, function before form.**

---

## 1. What this UI is

A feedback analytics tool for product managers. The product is **a ranked list of
what to fix this week, with the evidence attached.** Everything else exists to
support reading that list and trusting it.

The audience is a PM opening this on a Monday morning to decide what the team
works on. They are not browsing. They arrived with a question, and the interface
either answers it or wastes their time.

**This is a product UI, not a marketing site.** Two surfaces, two rule sets:

| Surface | Governed by |
|---|---|
| `/` landing page | Anti-slop marketing rules, section 11 |
| `/app/*` product | This document plus the dataviz rules, section 8 |

Rules written for landing pages do not automatically apply to the app, and the
reverse. Where they conflict, the surface decides.

---

## 2. Color

Tokens live in `app/globals.css`. Never hardcode a hex outside that file, with
one documented exception in section 9.

```
--background   page ground
--surface      cards, panels
--surface-2    nested surfaces, inputs
--border       hairlines, dividers
--primary      the one accent
--muted        inert fills
--positive / --neutral / --negative    sentiment, semantic only
--signal-up / --signal-down / --signal-new / --signal-flat   trend state
```

**Rules**

- **One accent.** `--primary` is the only brand colour. If a second hue shows up
  on badges, headings and borders at once, no colour is doing real work.
- **No gradients on interactive elements.** Flat fills. A gradient on a button is
  the clearest generated-UI signature there is.
- **No gradient text.**
- **No neon.** Nothing above 85% lightness at full saturation.
- **No pastels.** Every colour here has a job.
- **Semantic colours are reserved.** `--negative` means negative sentiment. It
  never becomes "series 4" or a decorative accent.
- **Colour is never the only signal.** Every status pairs with text or an icon.

---

## 3. Typography

Two families, both loaded through `next/font`. Never a `<link>` to Google Fonts.

```
Display / headings   font-display
Body / UI            default sans
Numbers              font-mono, with tabular
```

**Every number wears `font-mono` and `tabular`.** Counts, percentages, ratios,
durations, ids. Proportional digits make a column of numbers jitter as it
updates, and this interface updates numbers live.

- No font size below 11px.
- Line height 1.5 body, 1.2 display.
- Real heading hierarchy. Never a smaller tag styled larger.

---

## 4. Spacing, radius, shape

8px base grid. Tailwind's default scale is already on it. Stay on it.

**Shape consistency lock:** one radius system, applied everywhere.

```
rounded-md     inputs, buttons, small controls
rounded-lg     cards, panels
rounded-full   dots, pills, avatars only
```

Nothing above `rounded-lg` on a rectangular container. Round buttons in a square
layout is broken design.

---

## 5. Layout

The app is a fixed sidebar plus a scrolling content column.

```
Sidebar   240-280px, fixed, does not scroll with content
Header    56px, sticky, page title and page-level actions
Content   scrolls, fills the remaining width
```

- **Content fills the available width.** A 672px column stranded beside 1000px of
  nothing reads as broken. Cap a width only where the content has a natural
  measure, and say why in a comment.
- **Grid over flex-math.** `grid grid-cols-1 lg:grid-cols-3`, never
  `w-[calc(33%-1rem)]`.
- **Every multi-column layout declares its mobile collapse** in the same file.
- `min-h-[100dvh]`, never `h-screen`.

---

## 6. Motion

**Motion must be motivated.** Before adding an animation, name what it
communicates: hierarchy, sequence, feedback, or a state change. "It looked cool"
is not one of them.

**Use motion for**

- Pipeline stages changing state as a run streams. The movement is the data.
- Results entering when a run completes.
- `:active` on buttons, `scale-[0.98]`, a physical push.

**Never use motion for**

- Hover on non-interactive elements. No card lift, no scale, no shadow bloom.
- Ambient loops. Nothing animates without a user action or live data behind it.
- Scroll-triggered reveals inside the app. There is one scroll container and the
  user is reading, not being toured.

Anything beyond a trivial transition honours `prefers-reduced-motion`.

---

## 7. Components

shadcn/ui is the foundation. We own the code, so we customise it.

**Use it for** Button, Input, Textarea, Select, Badge, Separator, Card, Dialog.

**Never ship shadcn in its default state.** Radii, colours and typography come
from this document, not from the generator.

**Do not use it for** bespoke layouts or anything chart-shaped. Write those
directly.

---

## 8. Charts

Charts are hand-built SVG in `components/app/charts.tsx`. No charting library:
Recharts costs roughly 100kB gzipped to draw rectangles, and this app has already
learned what one stray dependency does to a bundle.

- **The form follows the job.** Magnitude is length. Composition is a stacked bar,
  not a donut, because three lengths compare more easily than three angles.
- **One axis.** Never two y-scales.
- **Categorical hues are assigned by fixed position and never cycled.** A seventh
  series folds into grey. Two themes sharing a colour is worse than admitting the
  palette ran out.
- **Every mark carries a direct label.** Colour alone is never the signal.
- Recessive grid and axes. Thin marks. 4px rounded data-ends. A 2px surface gap
  between adjacent fills.
- Every chart has a hover state and an empty state.

---

## 9. The one hardcoded palette, and why

`lib/chart-colors.ts` holds six hex values. It is the only place in the codebase
that hardcodes colour, and that is deliberate.

Those six were run through a colourblindness validator in both light and dark
mode and pass every check: lightness band, chroma floor, CVD separation,
normal-vision floor, and contrast against both surfaces. The palette they
replaced did not. Its worst adjacent pair sat at deuteranopia delta-E 3.7, which
means a red-green colourblind reader saw two different themes as one colour.

**One of the six is a violet.** A general "no purple" rule targets purple as a
*brand accent*, the AI-gradient tell. This is a data-series slot in a set chosen
for maximum mutual separation, where dropping a hue band costs measured
accessibility. Purple stays banned as an accent, a brand colour, a focus ring and
a gradient stop. It survives here, among six validated data hues, and nowhere
else.

**Do not edit these values without re-running the validator.** An unvalidated
palette is exactly how the last one shipped broken.

---

## 10. Interface states

Every view implements four, not just the successful one.

- **Loading.** Skeletons matching the final layout's shape, so nothing shifts on
  arrival. Never a bare spinner. For long work, report elapsed time: a number
  that moves is proof of life, a spinner is not.
- **Empty.** Composed, and it names the next action.
- **Error.** States what happened and how to recover. It does not apologise.
- **Partial.** This pipeline can finish with some items failed and the rest fine.
  Say so precisely rather than collapsing the run into "error".

---

## 11. Landing page only

These govern `/` and nothing else.

- No three-equal-feature-card row.
- No bento grid.
- No radial orbs, no blurred decorative shapes behind the hero.
- No dot-grid backgrounds.
- No fake product screenshots built from divs. Show the real components.
- No fabricated testimonials, no invented metrics, no logo wall we have not
  earned.
- No pricing tiers. There is no billing.
- Hero fits the viewport. Headline at most 2 lines, subtext at most 20 words.
- No scroll cues. The user knows what scrolling is.
- Copy says what the product does. It does not sell it.

---

## 12. Banned everywhere

- **Em-dashes in user-visible copy.** Use a comma, a colon, parentheses, or two
  sentences.
- **Glassmorphism as decoration.** A sticky header over scrolling content and a
  modal scrim are functional and allowed. A frosted panel because it looks
  expensive is not.
- **Sparkle icons to signal AI.** The product is obviously AI. It does not need to
  announce itself.
- **Icons as filler.** An icon earns its place by carrying meaning, not by sitting
  beside a heading.
- **Marketing copy inside the product.** Labels describe what the interface does.
- **Fake data anywhere.** No mock numbers, no placeholder charts, no invented
  coordinates. If the data is not there, the empty state says so. This rule has
  already been broken once in this codebase, and it is the one that matters most:
  a dashboard that lies is worse than a dashboard that is missing.

---

## 13. Accessibility baseline

- Visible focus on every interactive element, 2px offset, themed ring. Never the
  browser default on a dark surface, and never removed.
- Colour is never the only signal.
- Touch targets at least 44x44px on mobile.
- Every input has a label, visually hidden if needed. Never placeholder-as-label.
- WCAG AA contrast minimum for body text.
- Live regions announce streaming updates politely.

---

## 14. Conventions

```
app/                  routes, one folder per page
components/app/       product surfaces
components/landing/   marketing surfaces
components/ui/        shadcn generated, edited only to apply this document
components/three/     WebGL, always dynamically imported
lib/                  api client, formatting, tokens
```

- One component per file.
- TypeScript strict.
- **WebGL is always lazy.** three.js never enters a route's eager chunk. The
  explore route carried 251kB before this rule existed, including for devices
  that fall back to the non-3D view.
- `npm run build` passes clean before anything ships.

---

*Owner: frontend. Update this document in the same commit as any change that
contradicts it.*
