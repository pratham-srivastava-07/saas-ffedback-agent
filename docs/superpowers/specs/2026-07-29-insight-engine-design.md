# Sentilytics Insight Engine — Design

**Date:** 2026-07-29
**Status:** Approved
**Scope:** Backend only. UI is designed and approved separately.

## The problem

A SaaS company's customer feedback arrives continuously, as unstructured text, from
many sources at once — support tickets, NPS responses, app store reviews, sales
calls, Slack. Nobody can read all of it, so roadmap decisions get made from anecdote
instead of aggregate. The loudest customer in last week's call gets a fix; the issue
quietly mentioned by forty people does not, because nobody counted.

Per-item sentiment analysis does not solve this. "68% negative" is a chart, not a
decision. The unit a product manager can act on is a **theme with volume, trajectory,
and blast radius**:

> OAuth signup fails for enterprise accounts — 34 mentions, 3x since Tuesday's
> release, 9 of them paid.

**Sentilytics turns a feedback firehose into a ranked list of what to fix this week,
with the evidence attached.**

## What exists today, and why it cannot do this

The current pipeline (`graph.py`, `nodes/`) is a five-node chain that handles the
per-item half well and never performs the aggregate half:

- `nodes/cluster.py` asks the LLM to label each item with a free-text theme in
  isolation. "Bug in Signup Flow" and "Signup bug" become distinct themes, so
  counting is impossible and trajectory is impossible.
- Nothing is persisted, so there is no across-run comparison.
- `nodes/classify.py` calls `json.loads` on raw LLM text with no fence stripping.
- Each of `classify` and `cluster` makes one blocking LLM call per item inside a
  synchronous handler: N items cost 2N sequential calls.
- `utils.py` branches on `user_type == "enterprise"`, which the schema does not permit.

The app can describe one piece of feedback. It structurally cannot describe a
customer base. Closing that gap is this project.

## Architecture

Loose root modules move into an `app/` package. Thirteen node files at the repo root
would be unmanageable and the store layer needs a home.

```
app/
├── main.py            FastAPI app + router registration
├── config.py          pydantic-settings
├── llm.py             chat model, embeddings, structured-output helpers
├── schemas.py         API contracts + LLM structured-output models
├── api/               analyze.py, themes.py, runs.py
├── graph/
│   ├── state.py       AnalysisState + reducers
│   ├── build.py       StateGraph wiring
│   └── nodes/         one module per node
└── store/             db.py, models.py, repo.py
tests/
ui/                    unchanged
```

### Graph state

```python
class AnalysisState(TypedDict):
    run_id: str
    clean: list[CleanItem]
    rejected: list[RejectedItem]
    analyzed: Annotated[list[AnalyzedItem], operator.add]   # fan-in reducer
    clusters: list[Cluster]
    themes: list[ResolvedTheme]
    trends: list[TrendSignal]
    recommendations: list[Recommendation]
    critique: Critique | None
    revision_count: int
    summary: str
```

The `operator.add` reducer on `analyzed` is load-bearing: without it, parallel `Send`
branches overwrite each other instead of accumulating.

### Flow

```
normalize → triage
              ├─(nothing actionable)──────────────→ summarize → END
              └─(Send fan-out, one per item)→ analyze_one ─┐
                                                            ↓ fan-in
        embed (one batched call) → cluster → resolve_taxonomy → name_themes
                                                            ↓
                          prioritize → detect_trends → recommend
                                                            ↓
                                                        critique
                                                   ┌────────┴────────┐
                                   (unsupported,   ↓                 ↓  (approved or
                                    revisions<2) recommend      summarize   revisions==2)
                                                                     ↓
                                                                    END
```

### Node responsibilities

| Node | LLM | Purpose |
|---|---|---|
| `normalize` | no | Trim, collapse whitespace, drop exact duplicates |
| `triage` | no | Heuristic spam/noise rejection; drives the conditional edge |
| `analyze_one` | yes | Per-item structured sentiment, emotion, intent, severity, feature area, churn risk |
| `embed` | embeddings | One batched embedding call for all surviving texts |
| `cluster` | no | Agglomerative clustering over embeddings |
| `resolve_taxonomy` | no | Match clusters to stored themes by centroid similarity |
| `name_themes` | yes | Name, describe and persist only the genuinely new clusters |
| `prioritize` | no | Impact score: frequency x severity x user-tier weight |
| `detect_trends` | no | Compare against trailing snapshots; emerging / spiking / declining |
| `recommend` | yes | Product actions for the top themes |
| `critique` | yes | Verify recommendations are supported by evidence; may loop back |
| `summarize` | yes | Executive brief |

**`redact_pii` was cut during design review.** It made the diagram look
enterprise-serious and did nothing for the job the product does. Every node must earn
its place against the ranked-list-of-what-to-fix outcome.

`critique` is retained on dual grounds: it stops `recommend` from inventing
unsupported advice, and it is the clearest demonstration of a LangGraph cycle.

### Design decisions

**Naming runs after taxonomy resolution,** reversing the order shown in the original
sketch. Matching first means LLM naming calls are spent only on clusters we have
never seen; a recurring theme keeps its established name, which is the point of a
stable taxonomy.

**Deduplication is exact-match only, never semantic.** The original sketch said
"dedupe by embedding similarity". That is wrong: if forty people report the same bug
in forty phrasings, that is forty mentions, and collapsing them would destroy the
volume signal the product exists to produce. Only genuine duplicates — the same text
submitted twice — are removed.

**Triage is heuristic, not LLM.** Length, character-class and URL-only checks.
Deterministic behaviour is testable and cannot embarrass a live demo. It still
provides a genuine conditional edge.

**`embed` is a batch node placed after fan-in,** not per item. Embedding APIs accept
arrays; one call for fifty items rather than fifty calls.

**Clustering uses agglomerative, not HDBSCAN.** `metric="cosine"`,
`linkage="average"`, `distance_threshold≈0.35`, `n_clusters=None` — no need to guess
*k*. HDBSCAN is the more fashionable answer but labels most points as noise on a
ten-item demo batch, which reads as broken. Agglomerative degrades gracefully at
demo scale.

**The critique cycle is bounded at 2 revisions.** Unbounded cycles are how a
LangGraph demo hangs in front of an audience.

### Persistence (SQLite)

Zero-config so the project runs from a fresh clone with no Docker or cloud account.

- `runs` — id, created_at, item counts, status
- `feedback_items` — run_id, text, source, user_type, analysis fields, theme_id
- `themes` — id, name, description, **centroid vector**, first_seen_run, run_count
- `theme_snapshots` — theme_id, run_id, count, avg_severity, sentiment breakdown

**Taxonomy reconciliation** is what makes trajectory possible. Each new cluster's
centroid is cosine-compared against stored theme centroids. Above ~0.82 similarity it
merges into the existing theme and updates that centroid as a running mean; below, it
becomes a new theme and gets named. This is the direct fix for themes being renamed
on every run.

**Both thresholds were corrected on first contact with real embeddings
(2026-08-11).** The originals — distance 0.35, similarity 0.82 — had only ever been
exercised against the test suite's fake embedder, whose vectors are orthogonal and
therefore score exactly 0.0 or 1.0. Any value between the two passes that suite.

Measured against `gemini-embedding-001`: same-topic pairs fall in 0.070–0.217,
different-topic pairs in 0.224–0.309. At 0.35, **every** unrelated pair in the sample
merged — a four-item batch of two signup bugs, a billing complaint and a piece of
praise collapsed into one theme called "Signup Fails", reported as a churn risk.

Now 0.22 distance / 0.78 similarity. The two are the same number from opposite sides
and must move together, or clustering and taxonomy matching disagree about what
counts as the same thing.

The lesson generalises: a constant validated only against synthetic fixtures is
untested, not tested. Prefer erring toward over-splitting — it is visible, whereas
over-merging produces confident, wrong output that nothing downstream can detect.

**Trend detection** compares this run's per-theme share against that theme's trailing
snapshots. With fewer than three prior snapshots it reports `insufficient_history`
rather than inventing a percentage.

### API

- `POST /analyze` — synchronous, returns the full result
- `POST /analyze/stream` — SSE driven by `graph.astream_events(version="v2")`,
  emitting `node_start`, `node_end`, `error`, `complete`. Consumed by the frontend
  with `fetch` + `ReadableStream`; `EventSource` cannot issue POST.
- `GET /themes`, `GET /themes/trends`, `GET /runs`, `GET /runs/{id}`

Requests are bounded at 200 items and 5000 characters per item; beyond that, 422.

### Error handling

- Per-item failures are isolated. `analyze_one` catches and returns
  `status="failed"`, so one bad item cannot kill a run.
- All LLM calls use `.with_structured_output(PydanticModel)`. No raw `json.loads`.
- A semaphore caps concurrent fan-out so a large batch does not trip rate limits.
- Embedding or LLM outage marks the run failed and emits an `error` SSE event.

### Testing

pytest + pytest-asyncio, with a **fake chat model** and a **fake embedder** that
derives deterministic vectors from text hashes. Clustering assertions stay stable and
the suite costs nothing to run.

Coverage: each node in isolation, the full graph end to end on fakes, and the API via
`TestClient`. Three hazards get dedicated tests:

1. The critique cycle terminates when critique never approves.
2. The triage short-circuit reaches END with no actionable items.
3. Trend detection stays silent on thin history.

## Phase 2 — tenancy, evidence, hardening

Built after the original spec shipped. Auth and multi-tenancy were listed below as
out of scope; that turned out to be wrong, for a specific reason.

### Workspace scoping

`Theme` had no tenant column and `repo.load_themes()` returned every row unscoped.
That is not merely a missing feature: taxonomy matching compares a new cluster's
centroid against *stored* centroids, so with two tenants in one database, company
A's cluster would merge into company B's theme and silently corrupt both
taxonomies. Nothing else could be built on top of it.

Every run, theme and feedback item now carries a `workspace_id`, and every read
that could span tenants takes one.

**Tenancy travels in the graph state, not on the `Runtime`.** The `Runtime` is
constructed once at startup and shared by every request, so it cannot carry
per-request scope. `AnalysisState.workspace_id` is read by `resolve_taxonomy`,
`name_themes` and `detect_trends`.

**Pre-tenancy databases are upgraded in place**, not rejected. `app/store/migrate.py`
adds missing columns with `ALTER TABLE ADD COLUMN` and adopts orphaned rows into a
default workspace. No Alembic: the schema is small and SQLite-only. A test builds a
genuinely old-schema database, upgrades it, and asserts the data survives.

### Evidence retrieval

The product promised a ranked list "with the evidence attached" and provided no way
to read any of it.

- `GET /themes/{id}/items` — paginated feedback behind a theme.
- `GET /runs/{id}/result` — a past run rebuilt in full. Kept separate from
  `GET /runs/{id}` so listing history stays cheap.

**Per-run trends are persisted rather than reconstructed from snapshots.** The
`emerging` verdict depends on whether a theme was new *at the time*, which no
snapshot records; reconstruction would relabel every first appearance. Themes in a
past result come from that run's snapshots, so counts and impact scores are the ones
the run actually produced rather than what the theme has accumulated since.
`ThemeSnapshot` gained `impact_score` and `is_new` to make that exact.

### Auth and rate limiting

`X-API-Key` resolves to a workspace. Only the SHA-256 is stored — the keys are
high-entropy random tokens, not user-chosen secrets, so an unsalted hash is
adequate; a password would need argon2.

Auth is required by default. `ALLOW_ANONYMOUS_ACCESS` (off, and logged loudly when
on) maps unkeyed requests to the default workspace for local use. `/health` and
`/graph` stay open for load balancers.

Rate limiting is an in-process token bucket per workspace, on the endpoints that
invoke models. Reads are unthrottled. **This is per-process**: N workers means N
times the allowance. Accepted deliberately rather than adding Redis to a
single-node deployment.

### Other fixes

- **Abandoned runs.** A crash left rows at `status="running"` forever with nothing
  to clear them. A startup reaper fails anything older than `STALE_RUN_MINUTES`.
  Chosen over a LangGraph checkpointer: resumability is not worth the complexity,
  and the ghost rows were the actual problem.
- **`_utcnow()` returned timezone-aware datetimes into naive `DateTime` columns**,
  so a freshly-created object and the same row re-read compared as different types
  and raised on any datetime comparison. Now naive UTC throughout.
- **CORS is configurable from the environment**, comma-separated so it needs no
  JSON quoting in a shell. It previously hard-defaulted to `localhost:3000`, which
  blocks any deployed frontend.

### CSV ingestion

`POST /analyze/csv` with configurable column mapping. Real feedback arrives as a
Zendesk or Intercom export; requiring hand-written JSON is the difference between
trying the product and closing the tab. Only the text column is mandatory.
Unrecognised tier or source values fall back rather than failing the upload — a
stray `Platinum` should not cost the user their whole file.

### Threshold calibration

`THEME_MERGE_THRESHOLD` had only ever run against the fake embedder's orthogonal
vectors, where every similarity is 1.0 or 0.0 — completely unexercised in the
0.6–0.9 band where real embeddings live. `scripts/calibrate_threshold.py` sweeps it
against labelled data, comparing centroid to centroid as the pipeline does, and
reports wrong merges against wrong splits.

It reports that offline mode *cannot* answer the question rather than presenting a
tie-break artifact as a recommendation.

## Phase 3 — accounts and the cluster explorer

Added to support frontend decisions made after phase 2, against contracts fixed by
the coordinator while the UI was built in parallel.

### Email/password accounts

A `User` owns exactly one workspace. Passwords use **`hashlib.scrypt`** with a
per-user random salt — standard library, no bcrypt/argon2 dependency. This is the
opposite of the API-key decision, deliberately: keys are high-entropy random tokens
where a plain SHA-256 is fine, whereas passwords are user-chosen and low-entropy and
need a slow salted KDF.

Signup writes the user, workspace and key hash in one transaction — a user without a
workspace, or a workspace without a key, are both unusable accounts.

**Login returns the workspace API key rather than a session token.** The key auth
built in phase 2 stays the single source of truth, and there is no second credential
system to keep consistent. Two consequences, documented rather than hidden:

1. There is no server-side session to revoke; the key is only as safe as client
   storage.
2. **Logging in rotates the key**, because only its hash is stored and the old one
   genuinely cannot be recovered. Signing in on a second device signs the first out.

That is acceptable for one-workspace-per-user. Multi-device use would need sessions.

Login answers identically for an unknown email and a wrong password, and burns
equivalent scrypt work on the unknown-email path, so the endpoint cannot be used to
enumerate accounts by response or by timing.

### 3D projection

Embeddings previously existed only in graph state and were discarded, so there was
nothing to plot. Each run's embeddings are now PCA-projected to three components and
stored as `x, y, z` per feedback item.

**Only the projection is stored, not the vector.** The scatter plot is its only
consumer and SQLite is not a vector store. The cost is that switching projection
method later means re-running analysis rather than re-projecting.

**PCA is fit per run**, so coordinates from different runs sit in different bases and
are not comparable — hence a per-run endpoint, and an explicit warning in the README
against sharing axes.

**The projection runs in the persistence layer, not as a graph node.** A node would
be architecturally tidier, but `/analyze/stream` publishes `NODE_NAMES` in its
`run_start` frame and the frontend renders that list; adding a node during parallel
UI work risked breaking it for a purely cosmetic gain. The projection has no bearing
on themes, trends or recommendations — it exists solely so stored items can be
plotted — so persistence is a defensible home.

Normalisation uses a single global scale factor rather than per-axis, which would
stretch the cloud and misrepresent the relative distances the plot exists to show.

Degenerate cases return the origin instead of raising: fewer than two items, fewer
than three available components (padded), and identical vectors, where zero variance
would otherwise make sklearn emit NaN through a divide-by-zero. A scatter plot is a
nice-to-have and must never be able to fail a run.

## Phase 4 — the frontend

The header above says "UI is designed and approved separately" and "Scope: Backend
only." That was true when this spec was written; the frontend has since been built
in `ui/` and this section records it, because the decisions below constrain the
backend contract just as much as anything in Phase 1–3.

### Shape

Next.js 15, App Router, every page a client component (`"use client"`). There is no
server-side rendering of API data and no BFF — `ui/lib/api.ts` calls the FastAPI
backend directly from the browser over `fetch`, using `NEXT_PUBLIC_API_URL`
(default `http://localhost:8000`). That variable is the entire integration surface
between the two halves of the repo; nothing else about the backend needs to know
the frontend exists.

Pages: a marketing landing page and `/login` / `/signup`, then `/app` (paste-in or
CSV analysis with a live SSE view of the pipeline), `/app/themes` and
`/app/themes/[id]` (taxonomy and evidence), `/app/runs` and `/app/runs/[id]` (history
and full replay), `/app/explore` (the 3D cluster explorer), and `/app/settings`
(workspace + API key). Full detail is in `ui/README.md`.

### Auth carries the same key, not a session

`lib/auth.tsx`'s `AuthProvider` holds the API key in `localStorage` and `lib/api.ts`
attaches it as `X-API-Key` on every call except `/auth/signup`, `/auth/login` and
`/health`. A 401 from anywhere calls a single registered `onUnauthorized` handler
that clears the key and drops the app to signed-out — no call site handles 401
individually. This is a direct consequence of the Phase 3 decision to return the
workspace key from login rather than a session token: the frontend has no session
of its own to manage, only this one credential.

### Streaming consumption

`/analyze/stream`'s SSE frames (`run_start`, `node_start`, `node_end`, `error`,
`complete`) are read by hand off a `fetch` `ReadableStream` in
`streamAnalyze()` (`lib/api.ts`), not `EventSource` — `EventSource` cannot issue the
POST the batch requires. `run_start`'s `nodes` list drives `PipelineMonitor`
(`components/app/pipeline-monitor.tsx`), which is why the Phase 3 decision to keep
the PCA projection out of the graph (a real node would have changed that list mid
UI-build) mattered beyond cosmetics.

### The contract is hand-maintained, and was checked

`ui/lib/api.ts`'s TypeScript interfaces are transcribed by hand from
`app/schemas.py` and the response dicts built in `app/api/*.py` — there is no
codegen tying them together. As part of finishing this branch, every read endpoint
(`/health`, `/themes`, `/themes/trends`, `/themes/{id}/items`, `/runs`,
`/runs/{id}`, `/runs/{id}/result`, `/runs/{id}/scatter`) was exercised against a
real offline-seeded database (`scripts/seed_demo.py --offline --reset`) running
with `ALLOW_ANONYMOUS_ACCESS=true`, and every field compared against its TS
interface by hand. No drift was found — nullability, field names and shapes all
matched. `/analyze` and `/analyze/stream` could not be exercised the same way (they
need real LLM keys) but their response shape is guaranteed by
`response_model=AnalyzeResponse` on the FastAPI route, which `schemas.py` shows
matches `AnalyzeResponse`/`Theme`/`Trend`/`Recommendation` in `lib/api.ts` field for
field. `GET /graph` exists and works but nothing in `ui/` calls it — it is not part
of the frontend contract.

Because this check is manual, not generated, it will drift again the next time
either side changes a response shape without updating the other. There is no
regression guard against that beyond doing this check again.

## Out of scope

Billing, and ingestion connectors beyond CSV (Zendesk, Intercom and App Store APIs).
Each is its own project.
