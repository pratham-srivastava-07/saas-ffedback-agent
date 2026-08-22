# Deployment

## Current state

**Nothing is deployed.** There is no frontend hosting configured anywhere in this
repo, no `vercel.json`, no `netlify.toml`, no `render.yaml`. The old backend at
`saas-feedback-agent.onrender.com` no longer responds.

So if a deployed URL is showing an old UI, it is not being fed by this branch. It
is either a stale build from before the rebuild, or a host pointed at a different
commit.

---

## The order that matters

**Deploy the backend first.** The frontend is useless without it: every page
except the landing page reads from the API, and a Vercel build with no reachable
backend gives you a login screen that cannot log anyone in.

---

## 1. Backend

**Fastest path: the Render Blueprint.** `render.yaml` is in the repo root. In
Render choose New, then Blueprint, and point it at this repository. It builds the
Dockerfile, mounts the disk the database needs, sets the health check, and
prompts for the two API keys. Nothing is committed.

Any other container host works too, since the `Dockerfile` is standard.

**Start command,** if a host asks for one rather than reading the Dockerfile:
`uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Note the module path. It is `app.main:app`, not `main:app`. The entry point moved
into the package during the rebuild, and an old host config will fail on boot.
The container binds `$PORT` when the host sets it, falling back to 8000.

**Required environment**

```
GROQ_API_KEY=...
GOOGLE_API_KEY=...
EMBEDDING_MODEL=models/gemini-embedding-001
CORS_ORIGINS=https://your-frontend-domain.vercel.app
```

**Do not set `ALLOW_ANONYMOUS_ACCESS`.** It defaults to false and must stay that
way. It exists for local demo convenience: on a public instance it lets anyone
run analyses against your API keys, and every request costs you money.

### The SQLite problem, read this before choosing a host

The database is SQLite on local disk. On a free container tier that disk is
**ephemeral**, so it is wiped on every restart and every redeploy.

For this product that is not a minor annoyance. Themes and their snapshots are
what make trend detection possible. Wipe them and every theme reports
`insufficient_history` again, permanently, because the history never accumulates
past one run. The single capability that separates this from a stateless demo
stops working.

Three options, in order of effort:

1. **Persistent disk.** Render offers one on paid instances. Mount it and set
   `DATABASE_URL=sqlite+aiosqlite:////data/sentilytics.db`. Smallest change.
2. **Accept the reset.** Fine for a demo you reseed by hand. Not fine for anyone
   who signs up, since their account disappears too.
3. **Move to Postgres.** The store layer is SQLAlchemy async throughout, so this
   is a driver and URL change rather than a rewrite. The right answer if real
   users are coming.

---

## 2. Frontend

Vercel, since this is Next.js.

**Root Directory must be set to `ui`.** The Next app is not at the repo root, and
this is a project setting in the Vercel dashboard, not something a file in the
repo can express. A build that fails immediately with "no Next.js version
detected" is this setting.

**Environment**

```
NEXT_PUBLIC_API_URL=https://your-backend-host.onrender.com
```

Build command and output directory are Vercel's defaults. Nothing to override.

```bash
npm i -g vercel
cd ui
vercel          # first run links the project and asks for the root directory
vercel --prod
```

`vercel login` is interactive, so this has to be run by a human with the account.

---

## 3. After both are up

1. `GET https://your-backend/health` returns `{"status":"ok"}`.
2. Open the frontend, sign up, and confirm you land in an empty workspace rather
   than an error. A 401 loop here means `NEXT_PUBLIC_API_URL` is wrong or CORS
   does not list the frontend's exact origin, scheme included.
3. Seed demo data into that workspace so the product is not empty:

   ```bash
   python scripts/seed_demo.py --workspace <id from Settings>
   ```

   Run it against the deployed database, not your local one. Without `--offline`
   it uses real models and costs a few cents.

---

## What is not solved here

- **No CI deploy.** Pushing to `main` does not ship anything. Vercel will do this
  automatically once the project is linked; the backend host needs its own hook.
- **Rate limiting is per process.** Two backend instances mean two independent
  allowances. Fine at one instance, wrong the moment it scales.
- **No custom domain, no TLS beyond what the hosts provide by default.**
