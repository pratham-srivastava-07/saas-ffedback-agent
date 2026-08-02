# 📊 Sentilytics

**Turns a customer feedback firehose into a ranked list of what to fix this week, with the evidence attached.**

---

## The problem

Feedback arrives continuously, as unstructured text, from everywhere at once — support
tickets, NPS responses, app store reviews, sales calls, Slack. Nobody can read all of
it, so roadmap decisions get made from anecdote instead of aggregate. The loudest
customer in last week's call gets a fix; the issue quietly mentioned by forty people
doesn't, because nobody counted.

Per-item sentiment analysis doesn't solve this. *"68% negative"* is a chart, not a
decision. The unit a product manager can act on is a **theme with volume, trajectory,
and blast radius**:

> **OAuth signup fails for enterprise accounts** — 34 mentions, 3× since Tuesday's
> release, 9 of them paid.

That sentence gets a ticket filed before lunch. Producing it is what this does.

---

## See it working in 30 seconds

Trend detection needs history, so a fresh database has nothing to say. This
replays five weeks of feedback for a fictional product through the real
pipeline — no API key, no network:

```bash
pip install -r requirements-dev.txt
python scripts/seed_demo.py --offline --reset
```

```
  Week 1                             15 analysed, 2 rejected, 6 themes
  Week 2                             15 analysed, 1 rejected, 6 themes
  Week 3                             14 analysed, 0 rejected, 6 themes
  Week 4                             14 analysed, 0 rejected, 7 themes
  Week 5 (signup regression ships)   16 analysed, 0 rejected, 5 themes

========================================================================
FINAL RUN — themes ranked by impact
========================================================================

^^ Signup issues  [impact 66.43, 7 mentions, severity 4.43/5]
     spiking: 5.0x its 4-run average.

-- Export issues  [impact 27.0, 2 mentions, severity 3.0/5]
     steady: In line with its 4-run average.

** Mobile issues  [impact 21.67, 3 mentions, severity 4.33/5]
     emerging: First time this theme has appeared.

-- Dashboard issues  [impact 18.0, 3 mentions, severity 3.0/5]
     steady: In line with its 4-run average.

vv Billing issues  [impact 6.0, 1 mentions, severity 3.0/5]
     declining: 0.2x its 4-run average.
```

Nothing is inserted into the tables directly — the clustering, taxonomy
matching and trend maths all run for real, which is why the numbers move the
way the corpus's storyline says they should.

`--offline` swaps in the deterministic providers the test suite uses, so the
theme *names* and the written summary are placeholders. Drop the flag and set
your keys to get real ones; the counts, rankings and trends are identical
either way, since none of them come from the model.

---

## How it works

A LangGraph pipeline with conditional routing, map-reduce fan-out, and a bounded
self-correction cycle.

```mermaid
flowchart TD
    START([start]) --> normalize
    normalize --> triage
    triage -->|nothing actionable| summarize
    triage -->|Send: one branch per item| analyze_one
    analyze_one --> embed
    embed --> cluster
    cluster --> resolve_taxonomy
    resolve_taxonomy --> name_themes
    name_themes --> prioritize
    prioritize --> detect_trends
    detect_trends --> recommend
    recommend --> critique
    critique -->|unsupported, revisions < 2| recommend
    critique -->|approved or bounded out| summarize
    summarize --> END([end])
```

| Node | Does |
|---|---|
| `normalize` | Trim, collapse whitespace, drop exact duplicates |
| `triage` | Heuristic noise rejection; drives the conditional edge |
| `analyze_one` | Sentiment, emotion, intent, severity, feature area, churn risk — one structured call per item, fanned out concurrently |
| `embed` | One batched embedding call for the whole run |
| `cluster` | Agglomerative clustering over embeddings — the actual grouping |
| `resolve_taxonomy` | Match clusters to stored themes by centroid similarity |
| `name_themes` | Name only the genuinely new clusters, and persist them |
| `prioritize` | Impact = weighted reach × severity × churn multiplier |
| `detect_trends` | Compare against trailing runs: emerging / spiking / declining |
| `recommend` | Product actions grounded in the themes |
| `critique` | Audits those actions against the evidence; loops back if unsupported |
| `summarize` | The Monday-morning brief |

### Design notes

- **Clustering is agglomerative, not HDBSCAN.** HDBSCAN is the fancier answer and
  better on large corpora, but it labels most points as noise on a ten-item batch,
  which reads as broken. Agglomerative with a cosine threshold needs no `k` and
  degrades gracefully at demo scale.
- **Deduplication is exact-match only, never semantic.** Forty people reporting the
  same bug in forty phrasings is forty mentions. Collapsing them would destroy the
  volume signal the whole product rests on.
- **Themes persist across runs.** Each cluster centroid is compared against stored
  theme centroids; above the merge threshold it *is* that theme and keeps its name.
  Without this there is nothing stable to compare against, and "is this getting
  worse?" is unanswerable.
- **Trends compare share of run, not raw count.** Otherwise uploading a bigger file
  next week reports every theme as spiking. Below three prior runs it reports
  `insufficient_history` rather than inventing a percentage.
- **The critique cycle is bounded at 2 revisions.** Unbounded cycles are how a
  LangGraph demo hangs in front of an audience.

---

## Stack

- **Backend** — Python, FastAPI, LangGraph
- **Chat model** — Llama 3.3 70B via Groq (structured output throughout)
- **Embeddings** — Google `text-embedding-004`
- **Clustering** — scikit-learn
- **Storage** — SQLite via async SQLAlchemy
- **Frontend** — Next.js 15, Tailwind, shadcn/ui

---

## Running it

```bash
git clone https://github.com/pratham-srivastava-07/saas-ffedback-agent.git
cd saas-ffedback-agent

python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows

pip install -r requirements.txt

cp .env.example .env            # add GROQ_API_KEY and GOOGLE_API_KEY

uvicorn app.main:app --reload
```

The database is created on first start. No Docker, no cloud account.

Or containerised, mounting a volume so the taxonomy survives restarts:

```bash
docker build -t sentilytics .
docker run -p 8000:8000 --env-file .env -v sentilytics-data:/data sentilytics
```

Frontend:

```bash
cd ui
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

### Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The suite runs entirely against a fake chat model and a fake embedder that derives
deterministic vectors from text — no API key, no network, no cost, and stable
clustering assertions. CI runs the same command plus a full demo seed, so it needs
no secrets.

Three structural hazards get dedicated tests, because each is a way this class of
system fails quietly: the critique cycle terminates when the critic never approves,
the triage short-circuit reaches the end with nothing actionable, and trend
detection stays silent on thin history. A fourth replays the whole five-week corpus
to prove themes survive across runs rather than being reinvented each time.

---

## API

| Endpoint | Purpose |
|---|---|
| `POST /analyze` | Run the pipeline, return the full result |
| `POST /analyze/stream` | Same, streamed as SSE per node — consume with `fetch` + `ReadableStream` |
| `GET /themes` | The accumulated taxonomy across all runs |
| `GET /themes/trends` | Per-theme history for sparklines |
| `GET /runs`, `GET /runs/{id}` | Run history |
| `GET /graph` | The live pipeline topology as mermaid |

Requests are bounded at 200 items and 5000 characters per item.

---

## Not built

Auth, multi-tenancy, billing, and ingestion connectors (Zendesk, Intercom, App Store).
Each is its own project. The pricing page in the UI is presentational.
