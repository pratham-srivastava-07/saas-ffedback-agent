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
- **Embeddings** — Google `gemini-embedding-001` (3072-dim)
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

Structural hazards get dedicated tests, because each is a way this class of system
fails quietly: the critique cycle terminates when the critic never approves, the
triage short-circuit reaches the end with nothing actionable, trend detection stays
silent on thin history, two workspaces analysing identical feedback stay completely
separate, and a pre-tenancy database survives the schema upgrade with its data
intact. Another replays the whole five-week corpus to prove themes survive across
runs rather than being reinvented each time.

---

## Accounts, workspaces and auth

Everything — runs, themes, feedback, trend history — is scoped to a **workspace**.
Without that, two users of one deployment would share a taxonomy: company A's
"Billing issues" would absorb company B's and corrupt both.

### Signing up

```bash
curl -X POST localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"pm@acme.com","password":"correct-horse-battery","workspace_name":"Acme Product"}'
```

```json
{ "api_key": "sk_...", "email": "pm@acme.com",
  "workspace": { "id": "d503647d-...", "name": "Acme Product" } }
```

Signup creates the user, their workspace and its API key in one transaction.
Passwords are hashed with **`hashlib.scrypt`** and a per-user random salt — standard
library, no bcrypt or argon2 dependency. Minimum 8 characters.

`POST /auth/login` verifies the password and returns an API key; `GET /auth/me`
reports who a key belongs to.

### The deliberate trade: no sessions

Login returns the **workspace API key**, not a session token. The key auth the rest
of the API already uses stays the single source of truth, and there is no second
credential system to keep consistent. The client stores the key and sends it as
`X-API-Key` on every call.

Two consequences worth knowing:

- The key is only as safe as the client's storage. There is no server-side session
  to invalidate.
- **Logging in rotates the key.** Only its hash is stored, so the previous key
  genuinely cannot be handed back — a new one is issued and the old one stops
  working. Logging in on a second device therefore signs the first one out.

That is fine for one-workspace-per-user. Multi-device use or token revocation would
need real sessions.

### Keys without an account

For scripts and local work you can create a workspace directly, with no user
attached (`GET /auth/me` then reports `email: null`):

```bash
python scripts/create_workspace.py "Acme Product Team"
```

```
  Name:  Acme Product Team
  ID:    d503647d-7534-4a36-991f-71b298dea825
  Key:   sk_taX4GwcJpEgleVmLIwVWsuRZPAfCvgIPqn3RS6Q8L8o
```

Only the SHA-256 of the key is stored, so it is shown once and cannot be
recovered — a leaked database yields no working credentials. Send it on every
request:

```bash
curl -H "X-API-Key: sk_..." localhost:8000/themes
```

Auth is **required by default**. For local single-user work set
`ALLOW_ANONYMOUS_ACCESS=true`, which maps unkeyed requests to the default
workspace. Never do that on a deployed instance: `/analyze` spends real money on
every call.

`/analyze` and `/analyze/csv` are rate limited per workspace (default 30/min).
The bucket lives in process memory, so **N workers means N times the allowance** —
fine for a single node, and the point at which to move it to Redis.

---

## API

| Endpoint | Purpose |
|---|---|
| `POST /auth/signup` | Create a user, workspace and API key |
| `POST /auth/login` | Verify a password, return a freshly rotated API key |
| `GET /auth/me` | Who the current key belongs to |
| `POST /analyze` | Run the pipeline, return the full result |
| `POST /analyze/stream` | Same, streamed as SSE per node — consume with `fetch` + `ReadableStream` |
| `POST /analyze/csv` | Upload a CSV export directly |
| `GET /themes` | The accumulated taxonomy for this workspace |
| `GET /themes/trends` | Per-theme history for sparklines |
| `GET /themes/{id}/items` | **The evidence** — paginated feedback behind a theme |
| `GET /runs`, `GET /runs/{id}` | Run history |
| `GET /runs/{id}/result` | Rebuild a past run in full: items, themes, trends, recommendations |
| `GET /runs/{id}/scatter` | The run's embedding space as a 3D point cloud |
| `GET /graph` | The live pipeline topology as mermaid |
| `GET /health` | Unauthenticated, for load balancers |

Requests are bounded at 200 items and 5000 characters per item.

### CSV upload

Real feedback arrives as a Zendesk or Intercom export, not a hand-built JSON array.
Only a text column is required; everything else falls back to a default, so the
minimum viable upload is a one-column file.

```bash
curl -H "X-API-Key: sk_..." -F "file=@zendesk-export.csv" \
     -F "text_column=body" -F "id_column=ticket_id" \
     localhost:8000/analyze/csv
```

Unrecognised values in a tier or source column fall back rather than rejecting the
upload — a stray `Platinum` should not cost you the whole file.

---

## Frontend

Next.js 15 app in `ui/`, talking to this API over plain `fetch` — no SSR of API
data, every page is a client component. It covers everything the API exposes for
reading and analysing: paste-in or CSV analysis with a live SSE view of the
pipeline running node-by-node, the theme taxonomy with trend sparklines, the
evidence behind each theme, run history, a past run replayed exactly as it was
ranked, and a 3D explorer of a run's embedding space. `/app/settings` shows the
workspace and its API key; sign-up/login use `/auth/*` above.

Every call sends the stored key as `X-API-Key`; a 401 anywhere signs the app out.
Point it at a backend with `NEXT_PUBLIC_API_URL` (defaults to
`http://localhost:8000`):

```bash
cd ui
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

The default CORS origins above already allow `npm run dev`'s port. Most of
`/app` — themes, runs, the 3D explorer — needs no LLM keys and works against
`ALLOW_ANONYMOUS_ACCESS=true` once the database has history in it (the demo
seed above does this); only the analyze pages call the model. See `ui/README.md`
for the page-by-page rundown and `ui/lib/api.ts` for the request layer.

---

## The 3D cluster explorer

`GET /runs/{id}/scatter` returns one point per feedback item, positioned by a PCA
projection of the run's real embedding space and tagged with its theme:

```json
{ "points": [{ "item_id": "1", "theme_id": "...", "theme_name": "Signup issues",
               "x": 0.83, "y": -0.21, "z": 0.05,
               "sentiment": "negative", "severity": 5, "text": "Signup is broken" }],
  "themes": [{ "id": "...", "name": "Signup issues", "count": 3 }] }
```

Coordinates are normalised to roughly [-1, 1] with a single global scale factor,
not per-axis — per-axis would stretch the cloud and misrepresent the relative
distances the plot exists to show.

**PCA is fit per run, so coordinates are not comparable between runs.** Each run has
its own basis; two runs must never share axes. That is why the endpoint is per-run.

Only the projection is stored, not the underlying 768-dimension vector: the scatter
plot is its only consumer and SQLite is not a vector store. The cost of that choice
is that changing projection method later (t-SNE, UMAP) means re-running analysis
rather than re-projecting stored vectors.

Degenerate cases are handled rather than raising — a single item, or items whose
embeddings are identical, collapse to the origin, which is the honest picture rather
than an error.

---

## Tuning the merge threshold

Two numbers govern grouping, and they are the same number from opposite sides:
`CLUSTER_DISTANCE_THRESHOLD` (0.22) decides whether two items join one cluster, and
`THEME_MERGE_THRESHOLD` (0.78 similarity = 0.22 distance) decides whether a new
cluster *is* an existing theme. **Move them together or clustering and the taxonomy
will disagree.**

Both were measured against `gemini-embedding-001` on a labelled sample: same-topic
pairs land in 0.070–0.217, different-topic pairs in 0.224–0.309. 0.22 sits in the gap.

That gap is narrow, so re-measure against your own data. When in doubt, err low: an
over-split shows two themes that should be one, which is visible and irritating. An
over-merge files praise under a churn-risk bug, which is a lie nothing downstream can
detect.

```bash
python scripts/calibrate_threshold.py          # needs GOOGLE_API_KEY
python scripts/calibrate_threshold.py --offline   # smoke test only
```

The sweep mirrors what the pipeline actually does — centroid against centroid, not
text against text — and reports wrong merges against wrong splits at each threshold
so you can choose which way to err.

**Offline mode cannot answer this question.** The fake embedder maps topics to
orthogonal dimensions, so every similarity is exactly 1.0 or 0.0 and any threshold
scores perfectly. The script says so rather than reporting a meaningless winner.

---

## Not built

Billing, and ingestion connectors beyond CSV (Zendesk, Intercom, App Store APIs).
The pricing page in the UI is presentational.
