# Migration: DigitalOcean → Render + Vercel + Neon (all free, $0/month)

Why this migration: the DigitalOcean GitHub Student Pack credits expired July 31,
2026, and standard billing kicked in ($15.78 charged September 1, and it will
recur monthly). OpenAI Build Week judging ended August 5, so it's safe to move
now with zero risk to the submission.

**New architecture (all free tier, no expiration traps):**

| Piece | Old (DigitalOcean) | New | Cost |
|-------|---------------------|-----|------|
| Backend (FastAPI) | App Platform web service | Render Web Service | $0 |
| Frontend (Next.js) | App Platform web service | Vercel | $0 |
| Database (Postgres) | App Platform managed DB | Neon | $0 |
| Redis | Not used anyway | Removed entirely | $0 |

**Important note about free tiers:** Render's free web services "sleep" after
15 minutes of no traffic and take about 30-60 seconds to wake up on the next
request. Vercel's frontend does not have this problem. This means: the first
time someone opens your site after a period of inactivity, the backend calls
might feel slow for one request, then it's fast again. This is a normal,
well-known tradeoff of free hosting and does not affect your Devpost
submission (already judged) or your code quality.

---

## STEP 1: Back up your DigitalOcean database (do this first, before anything else)

### 1a. Get your DigitalOcean database connection string

1. Go to https://cloud.digitalocean.com/apps → `ai-security-platform`
2. Click the `ai-security-db` database component
3. Find **Connection Details** → copy the **Connection String** (starts with `postgresql://`)

### 1b. Run the backup

Open PowerShell:

```powershell
cd "C:\Users\sober\Documents\Faysal\Enterprise AI Security Red Teaming Platform\distribution"
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" "PASTE_YOUR_DO_CONNECTION_STRING_HERE?sslmode=require" --no-owner --no-acl --format=plain --file="do_backup_$(Get-Date -Format yyyy-MM-dd).sql"
```

### 1c. Verify it worked

```powershell
ls do_backup_*.sql
```

If the file is more than a few KB, the backup succeeded. Keep this file safe —
you'll restore from it into Neon in Step 3.

**If this fails or you don't want to bother:** the data in this database is
test runs and scenario definitions, not anything irreplaceable. The seed
script (`seed_attack_scenarios`) automatically recreates the attack scenarios
on first boot regardless. Skipping the backup means losing your test run
history, not losing the platform's functionality.

---

## STEP 2: Create a free Postgres database on Neon

1. Go to https://neon.tech and sign up (GitHub login is fastest)
2. Click **Create a project**
3. Name it `ai-security-db`
4. Choose a region close to you (US East is fine)
5. Once created, you'll see a **Connection String** on the dashboard — copy it.
   It looks like:
   ```
   postgresql://user:password@ep-something.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
6. **Save this connection string somewhere safe** — you'll need it twice (once
   to restore your backup, once to give to Render).

### Restore your backup into Neon (skip if you skipped Step 1)

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" "PASTE_YOUR_NEON_CONNECTION_STRING_HERE" -f do_backup_2026-09-XX.sql
```

Replace the filename with whatever your backup file was actually named.

---

## STEP 3: Deploy the backend to Render

1. Go to https://render.com and sign up / log in (GitHub login is fastest)
2. Click **New** → **Blueprint**
3. Connect your GitHub account if not already connected, select
   `SheikhMdFaysal/distribution`
4. Render will detect `render.yaml` in the repo automatically and show you
   the `ai-security-backend` service it's about to create
5. Click **Apply**
6. Wait for the first build (5-10 minutes)

### Set the environment variables Render couldn't auto-fill

1. Once the service exists, go to it → **Environment** tab
2. Add each of these (click **Add Environment Variable** for each):

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Your Neon connection string from Step 2 |
| `GOOGLE_API_KEY` | Your Google AI key |
| `GROQ_API_KEY` | Your Groq key |
| `OPENROUTER_API_KEY` | Your OpenRouter key |
| `HF_TOKEN` | Your HuggingFace token |
| `NVIDIA_API_KEY` | Your NVIDIA key |
| `OPENAI_API_KEY` | Your OpenAI key (if you added the $5 credit earlier) |

3. Click **Save Changes** — this triggers an automatic redeploy
4. Once redeployed, copy your backend's URL from the top of the Render page.
   It looks like: `https://ai-security-backend-xxxx.onrender.com`

### Test the backend

Open in your browser:
```
https://ai-security-backend-xxxx.onrender.com/api/v1/health
```
You should see `{"status":"healthy",...}`. The first request after a cold
start can take 30-60 seconds — that's expected on the free tier.

---

## STEP 4: Deploy the frontend to Vercel

1. Go to https://vercel.com and sign up / log in (GitHub login is fastest)
2. Click **Add New** → **Project**
3. Import `SheikhMdFaysal/distribution`
4. **Important:** set the **Root Directory** to `frontend` (click Edit next to
   Root Directory in the import screen)
5. Vercel auto-detects Next.js — you don't need to change build settings
6. Before clicking Deploy, expand **Environment Variables** and add:

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_API_URL` | Your Render backend URL from Step 3 (e.g. `https://ai-security-backend-xxxx.onrender.com`) |

7. Click **Deploy**
8. Wait 2-3 minutes. Vercel gives you a URL like `https://distribution-xxxx.vercel.app`

### Connect the two services (CORS)

1. Go back to Render → your backend service → **Environment**
2. Add or edit `ALLOWED_ORIGINS` with this **exact JSON array format**
   (not comma-separated — the backend expects real JSON):
   ```
   ["https://distribution-xxxx.vercel.app"]
   ```
   Replace with your actual Vercel URL.
3. Save — this redeploys the backend once more.

---

## STEP 5: Test everything end to end

1. Open your new Vercel URL
2. Confirm the status dot goes green (may take 30-60s on first load — cold start)
3. Run a real security test (pick Groq, it's the most reliable)
4. Confirm results appear
5. Click **Generate Executive Summary**, confirm it works
6. Check the footer shows the right version number

If anything fails, the troubleshooting instincts from this whole project
still apply: check Render's **Logs** tab (equivalent of DigitalOcean's Runtime
Logs) for the real error before guessing.

---

## STEP 6: Update every place that mentions the old DigitalOcean URL

The old URL `https://ai-security-platform-jlp76.ondigitalocean.app` appears in:

- [ ] Your LinkedIn post/profile featured link
- [ ] Your Devpost submission ("Try it out" links) — **only relevant if you still want it live post-judging; judging already happened, so this is optional but good practice**
- [ ] The footer's GitHub link is unaffected (that always pointed at GitHub, not the live URL)
- [ ] Any resume, portfolio, or EB2-NIW draft materials that cite the live URL

Update these to the new Vercel URL once you've confirmed everything works.

---

## STEP 7: Only now — delete the DigitalOcean app to stop billing

**Do this only after Steps 3-5 are confirmed working.** Do not delete DigitalOcean
until the new setup is proven, in case you need to roll back.

1. Go to https://cloud.digitalocean.com/apps → `ai-security-platform`
2. Settings → scroll to the bottom → **Destroy App**
3. Type the app name to confirm
4. This deletes the web services AND the database. Your backup from Step 1
   protects you regardless.
5. Go to **Billing** → confirm no other DigitalOcean resources are still
   running (droplets, spaces, etc.) that could keep charging you.

You will not be charged again after this, since App Platform bills for what's
currently running, not in advance.

---

## Cost comparison, for the record

| | Old (DigitalOcean, post-credit) | New (Render + Vercel + Neon) |
|---|---|---|
| Monthly cost | ~$15.78 (confirmed) and climbing with usage | $0 |
| Cold starts | None | Backend only, ~30-60s after 15 min idle |
| Data ownership | Same | Same (you control the Neon database directly) |
| Custom domain later | Paid tier upgrade | Both Render and Vercel support this on free tiers already |
