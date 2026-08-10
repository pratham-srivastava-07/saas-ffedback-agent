# Sentilytics — frontend

Next.js 15 (App Router) client for the Sentilytics insight engine. It talks to the
FastAPI backend in `../app` over plain `fetch` — there is no server-side rendering
of API data and no BFF layer; every page is a client component that calls the API
directly from the browser.

## Pages

| Route | What it does |
|---|---|
| `/` | Marketing landing page. Presentational only — the pricing shown here is not wired to billing. |
| `/login`, `/signup` | Email/password auth. On success the returned API key is stored client-side and used for every subsequent request. |
| `/app` | Paste feedback in, watch the pipeline run node-by-node over SSE, see the ranked themes, trends and recommendations come back. |
| `/app/ingest` | Upload a CSV export (Zendesk/Intercom-shaped) instead of pasting text. |
| `/app/themes` | The accumulated taxonomy for the workspace, ranked by total mentions, with a sparkline of share-of-run per theme. |
| `/app/themes/[id]` | The evidence behind one theme — paginated feedback items, not just a count. |
| `/app/runs` | Run history. |
| `/app/runs/[id]` | A past run replayed exactly as it was ranked at the time (themes/trends/recommendations are read back from storage, not recomputed). |
| `/app/explore` | The run's embedding space as a navigable 3D point cloud (PCA projection, one run at a time — coordinates are never comparable across runs). |
| `/app/settings` | Workspace name/ID, the current API key (reveal/copy), sign out. |

`/app/*` pages are wrapped in `AppShell` (`components/app/shell.tsx`) and expect an
authenticated or anonymous-mode session, set up in `lib/auth.tsx`.

## Talking to the backend

All API calls go through `lib/api.ts`. Two things to know:

- **`NEXT_PUBLIC_API_URL`** is the backend's base URL. It defaults to
  `http://localhost:8000` if unset (see `API_BASE` in `lib/api.ts`). Set it in
  `.env.local` for local dev, and as a build-time env var wherever the frontend is
  deployed — it's inlined at build time since it's a `NEXT_PUBLIC_*` var.
- **Every authenticated request sends an `X-API-Key` header.** The key is read from
  `localStorage` (`sentilytics.api_key`) by `request()` in `lib/api.ts` and attached
  automatically; call sites never handle it themselves. `/auth/signup`, `/auth/login`
  and `GET /health` are the only calls made without one (`anonymous: true`). A 401
  from any other call clears the stored key and drops the app back to signed-out,
  via the `onUnauthorized` hook `AuthProvider` registers.

`lib/api.ts`'s types are transcribed by hand from the FastAPI response models in
`../app/schemas.py` and the route handlers in `../app/api/`. They are not generated,
so if the backend's response shape changes, this file has to be updated by hand too.

## Running against a local backend

```bash
# from the repo root
cp .env.example .env                     # add GROQ_API_KEY / GOOGLE_API_KEY, or set
                                          # ALLOW_ANONYMOUS_ACCESS=true for read-only
                                          # local use with no keys
uvicorn app.main:app --reload            # backend on :8000
```

```bash
cd ui
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev                              # frontend on :3000
```

The backend's default CORS origins (`http://localhost:3000`,
`http://127.0.0.1:3000`) already match `npm run dev`'s default port, so no CORS
config is needed for local work. If you deploy the frontend elsewhere, add its
origin to the backend's `CORS_ORIGINS`.

`/app`, `/app/ingest` and their streaming/CSV endpoints need `GROQ_API_KEY` and
`GOOGLE_API_KEY` set on the backend — they call the model. Every other page under
`/app` reads previously-stored data and works fine with `ALLOW_ANONYMOUS_ACCESS=true`
and no LLM keys, once the database has something in it
(`python scripts/seed_demo.py --offline --reset` from the repo root seeds five
weeks of demo history for exactly this).

## Commands

```bash
npm run dev      # dev server, turbopack
npm run build    # production build (also type-checks)
npm run start    # serve the production build
npm run lint     # eslint
```

`npm run build` runs `next build`, which type-checks the whole project as part of
the build — there is no separate `tsc --noEmit` script.
