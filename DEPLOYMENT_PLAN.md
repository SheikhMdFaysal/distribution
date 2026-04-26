# Deployment Plan — Cloud-First Architecture

Dr. Ray's directive (April 19 meeting): **do not require local installation.** Customers who can run the platform locally cannot become paying customers. Deploy to the cloud so demos are URL-first and the business model is preserved.

---

## 1. Recommendation: **Render** (not Railway)

| Factor | Render | Railway |
|---|---|---|
| Free tier | ✅ Yes — web services, PostgreSQL, Redis all free | ⚠️ $5 trial only, then paid |
| PostgreSQL | ✅ Free 90 days, then $7/mo | Requires plan |
| Redis | ✅ Free 25 MB tier | Requires plan |
| Cold start on free tier | ~30 sec wake-up | Faster but paid |
| Custom domain | ✅ Free | ✅ Free |
| Ease for first-time user | High | High |
| Best for student capstone | **✅ Yes** | No |

**Render is the correct choice** because: (a) truly free for our scale, (b) bundles everything (web + Postgres + Redis + static), (c) good enough performance for demos.

Fallback if Render has issues: **Fly.io** (also free tier, harder setup) or **Vercel + Supabase** (Vercel for Next.js frontend, Supabase for Postgres, Upstash for Redis).

---

## 2. Target architecture on Render

```
                    ┌─────────────────────────────┐
                    │  yourproject.onrender.com   │  ← public URL (Next.js)
                    └──────────────┬──────────────┘
                                   │ HTTPS
                                   ▼
                    ┌─────────────────────────────┐
                    │  api.yourproject.onrender.  │  ← FastAPI (web service)
                    │           com               │
                    └──────┬───────────┬──────────┘
                           │           │
                           ▼           ▼
                  ┌───────────────┐ ┌──────────────┐
                  │ Render        │ │ Render Redis │  ← job queue
                  │ PostgreSQL    │ │              │
                  └───────────────┘ └──────────────┘
                           ▲
                           │
                  ┌────────┴──────────┐
                  │ RQ Worker         │  ← background service
                  │ (Python worker)   │
                  └───────────────────┘
```

Four Render services total:
1. **Web service** — Next.js frontend
2. **Web service** — FastAPI backend
3. **Background worker** — RQ worker
4. **Managed Postgres** + **Managed Redis**

---

## 3. Step-by-step for Sonal (estimated 2–3 hours first time)

### Pre-flight checklist
- [ ] GitHub repo is clean — no hardcoded secrets (run `grep -r "sk-\|AIza" distribution/` to verify)
- [ ] `distribution/backend/Dockerfile` exists (already confirmed ✅)
- [ ] Create `distribution/frontend/Dockerfile` — template below
- [ ] Consolidate API keys in Render dashboard (not committed)

### Step 1 — Sign up
https://render.com → Sign up with GitHub → authorize access to `SheikhMdFaysal/distribution`

### Step 2 — Provision Postgres
Dashboard → New → PostgreSQL → free tier → name: `ai-security-db` → note the Internal Database URL.

### Step 3 — Provision Redis
Dashboard → New → Redis → free tier → name: `ai-security-redis` → note the Internal Redis URL.

### Step 4 — Deploy backend
Dashboard → New → Web Service → connect repo → settings:
- Root directory: `distribution/backend`
- Runtime: Docker
- Environment variables (from dashboard, NOT .env file):
  - `DATABASE_URL` = Internal Postgres URL
  - `REDIS_URL` = Internal Redis URL
  - `GOOGLE_API_KEY` = (from Google AI Studio)
  - `GROQ_API_KEY` = (from Groq)
  - `OPENROUTER_API_KEY`, `TOGETHER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` as obtained
  - `ALLOWED_ORIGINS` = `https://yourproject.onrender.com`
  - `ENVIRONMENT` = `production`
- Run alembic migration as "Pre-deploy command": `alembic upgrade head`

### Step 5 — Deploy RQ worker
Dashboard → New → Background Worker → same repo → settings:
- Root directory: `distribution/backend`
- Start command: `python start_worker.py`
- Same env vars as backend (DATABASE_URL, REDIS_URL, all API keys)

### Step 6 — Deploy frontend
Dashboard → New → Web Service → connect repo → settings:
- Root directory: `distribution/frontend`
- Runtime: Node
- Build command: `npm install && npm run build`
- Start command: `npm run start`
- Environment variables:
  - `NEXT_PUBLIC_API_URL` = backend service URL from Step 4

### Step 7 — Smoke test
- [ ] Visit frontend URL — dashboard loads
- [ ] Backend status card shows "healthy"
- [ ] Trigger 1 test run against Gemini → see job queued → worker processes → result appears

### Step 8 — Custom domain (optional, nice-to-have)
Buy `redteam-ai.com` (or similar) on Namecheap (~$10/year) → add CNAME in Render → auto-SSL.

---

## 4. Frontend Dockerfile (create this file)

Path: `distribution/frontend/Dockerfile`

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["npm", "run", "start"]
```

---

## 5. Cost summary (first 3 months)

| Item | Cost |
|---|---|
| Render web × 2 (free tier) | $0 |
| Render background worker (free tier) | $0 |
| Render Postgres (free 90 days) | $0 |
| Render Redis (free 25 MB) | $0 |
| API usage (free tiers only) | $0 |
| **Total** | **$0** |

After 90 days: Postgres becomes $7/mo. Decision point — either (a) migrate to Supabase free Postgres, or (b) budget ~$10/mo if the project continues post-capstone.

---

## 6. Timeline against May 4 deadline

| Week | Action |
|---|---|
| **Apr 20–23** | Sonal provisions Render services + pushes backend Dockerfile. Faysal collects free API keys from Plan §3. |
| **Apr 24–27** | End-to-end smoke test — 1 full test run against Gemini through cloud deployment. Capture screenshots for final presentation. |
| **Apr 28–May 2** | Polish, generate sample compliance reports, rehearse demo using the public URL. |
| **May 4** | Final presentation — demo from the public Render URL, not localhost. |

---

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Render free-tier cold start during live demo | Warm up by visiting URL 5 min before demo |
| API key leaks in GitHub | Use Render env vars, never commit keys; run `git secrets` scan |
| Free-tier rate limits hit mid-demo | Pre-record one successful run as backup video |
| Postgres free tier expires mid-semester | Back up to SQLite file as disaster fallback |
