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

The 0.82 threshold is the number most likely to need tuning against real data. It is
a single named constant in `config.py`.

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

## Out of scope

Auth, multi-tenancy, billing, and ingestion connectors. Each is its own project.
The UI is designed and approved separately; this spec changes no file under `ui/`
except to document the `NEXT_PUBLIC_API_URL` contract.
