# DigitalOcean Migration Guide

Step-by-step migration from Render to DigitalOcean. Written for someone who is not a DevOps engineer.

## What Changes and What Stays the Same

**Stays the same:** Your application code, Docker setup, GitHub repo, database schema, all functionality.

**Changes:** Where the app runs (DigitalOcean instead of Render), the deployment hosting URL, and the database hostname.

## Two Deployment Options

You have two paths. Pick one based on your priorities.

| Aspect | Droplet + Docker Compose | App Platform |
|--------|--------------------------|--------------|
| Monthly cost (after free credit) | $6 to $12 | $40 to $60 |
| Setup complexity | Medium (need SSH) | Easy (web UI) |
| Free for first 60 days | Yes ($200 credit covers it) | Yes ($200 credit covers it) |
| Auto-deploy on git push | Manual (run deploy.sh) | Yes |
| HTTPS auto | Yes (via Caddy) | Yes (built-in) |
| Database backups | Manual (use backup_postgres.sh) | Automated daily |
| Best for | Cost-conscious startups, students | Teams that want zero ops |

**Recommendation:** Droplet + Compose unless you genuinely have $40/month to burn. The savings ($400+/year) are real.

---

## URGENT: Step 0 — Backup Render Data

Before anything else, follow `BACKUP_RENDER_FIRST.md`. You have 14 days before Render deletes your database. This is non-recoverable if you miss it.

---

## Path A: Droplet + Docker Compose ($6/month)

### Step 1: Create DigitalOcean Account

1. Go to https://www.digitalocean.com
2. Sign up using a referral link if you can find one (gives you $200 free credit). Or sign up directly and you get $200 credit for 60 days.
3. Verify your email and add a payment method (required, not charged immediately).

### Step 2: Create a Droplet

1. Click "Create" → "Droplets"
2. Choose Image: **Ubuntu 24.04 LTS x64**
3. Choose Size: **Basic** → **Regular** → **$6/mo (1 GB RAM, 25 GB SSD)**
4. Choose Datacenter: **NYC1** or whatever is closest to your users
5. Authentication: **SSH Key** (recommended) or **Password**
   - If SSH Key, follow the prompt to add your public key
   - If Password, choose a strong one and save it
6. Hostname: `ai-security-platform`
7. Click "Create Droplet"

After ~30 seconds, you will see the droplet's IP address. Copy it.

### Step 3: SSH Into the Droplet

Open PowerShell on Windows:

```powershell
ssh root@YOUR_DROPLET_IP
```

(Replace `YOUR_DROPLET_IP` with the IP from Step 2. If you used a password, you will be prompted.)

### Step 4: Install Docker

Once SSH'd in, run these commands one by one:

```bash
# Update package lists
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose plugin (already included in modern Docker)
docker compose version

# Install git
apt install -y git

# Confirm everything works
docker --version
docker compose version
git --version
```

### Step 5: Clone Your Repo

```bash
# Make sure your repo is private but you can clone it. You will need either:
# - A deploy key (recommended), or
# - GitHub Personal Access Token

# Quick option: use Personal Access Token
git clone https://YOUR_GITHUB_USERNAME:YOUR_TOKEN@github.com/SheikhMdFaysal/Enterprise-AI-Security-Red-Teaming-Platform.git
cd Enterprise-AI-Security-Red-Teaming-Platform/distribution/digitalocean
```

### Step 6: Configure Environment

```bash
# Copy the template
cp .env.example .env

# Edit it with your real values
nano .env
```

Fill in:

- `POSTGRES_PASSWORD`: generate with `openssl rand -hex 16` (paste the output)
- `SECRET_KEY`: generate with `openssl rand -hex 32` (paste the output)
- All API keys (GROQ, GOOGLE, OPENROUTER, HF, NVIDIA)
- `ALLOWED_ORIGINS`: `http://YOUR_DROPLET_IP` if no domain, or `https://yourdomain.com` if you have one
- `PUBLIC_API_URL`: same logic

Save and exit nano: `Ctrl+O`, `Enter`, `Ctrl+X`.

### Step 7: Update Caddyfile

If you have NO domain (using IP address only):

```bash
nano Caddyfile
```

Replace the entire contents with:

```
:80 {
    handle /api/* {
        reverse_proxy backend:8000
    }
    handle {
        reverse_proxy frontend:3000
    }
}
```

If you have a domain, edit Caddyfile and replace `YOUR_DOMAIN.com` with your real domain in both blocks. Also point your domain's DNS A records to the droplet IP:

- `yourdomain.com` → A record → YOUR_DROPLET_IP
- `api.yourdomain.com` → A record → YOUR_DROPLET_IP

### Step 8: Copy Render Backup (Optional)

If you backed up your Render database in Step 0:

```bash
# From your Windows machine, in a NEW PowerShell window:
scp render_backup_2026-06-02.sql root@YOUR_DROPLET_IP:/root/Enterprise-AI-Security-Red-Teaming-Platform/distribution/digitalocean/render_backup.sql
```

### Step 9: Deploy

Back in the SSH session on the droplet:

```bash
chmod +x deploy.sh backup_postgres.sh
./deploy.sh
```

Wait 2 to 3 minutes for everything to build and start. You will see container status at the end.

### Step 10: Verify

Open in your browser:

- `http://YOUR_DROPLET_IP` (or `https://yourdomain.com` if you set up a domain)
- `http://YOUR_DROPLET_IP/api/v1/health` should return `{"status": "ok"}`

### Step 11: Set Up Automated Backups

```bash
# Set the backup script to run daily at 2 AM
crontab -e
```

Add this line:

```
0 2 * * * cd /root/Enterprise-AI-Security-Red-Teaming-Platform/distribution/digitalocean && ./backup_postgres.sh >> /var/log/backup.log 2>&1
```

Save and exit.

### Step 12: Tell Dr. Ray, Sonal, Baquer the New URL

The application is now live at your new DigitalOcean URL. Update any documentation, README, or LinkedIn posts that pointed at the old Render URL.

---

## Path B: App Platform ($40/month)

Only do this if you really want the easier UI and you are okay paying more.

### Step 1: Install doctl (DigitalOcean CLI)

On Windows PowerShell:

```powershell
# Using Scoop (https://scoop.sh)
scoop install doctl

# Or download the binary directly from https://github.com/digitalocean/doctl/releases
```

### Step 2: Authenticate

```powershell
doctl auth init
# Paste your DigitalOcean API token from https://cloud.digitalocean.com/account/api/tokens
```

### Step 3: Create the App

```powershell
cd "C:\Users\sober\Documents\Faysal\Enterprise AI Security Red Teaming Platform\distribution"
doctl apps create --spec digitalocean/app-platform.yaml
```

### Step 4: Set Secrets

In the DigitalOcean web UI, go to your new app, then Settings → Components → Backend → Environment Variables. Add real values for all the SECRET-typed variables (API keys, SECRET_KEY).

### Step 5: Wait for Build

App Platform will build and deploy automatically. First deploy takes 5 to 10 minutes.

### Step 6: Restore Database

In the App Platform UI:

1. Go to Database → Connection Details → "Connect from this computer"
2. Copy the connection string
3. From your local Windows machine:

```powershell
psql "POSTGRES_CONNECTION_STRING" < render_backup_2026-06-02.sql
```

### Step 7: Done

App Platform auto-deploys on git push to main. Update DNS if you want a custom domain.

---

## After Migration: Cleanup

1. In your Render dashboard, delete the old services and database (so you do not get billed)
2. Update `render.yaml` in the repo to add a comment saying it is deprecated, or move it to an `archive/` folder
3. Update README.md to point at the new DigitalOcean deployment
4. Rotate all your API keys (Google, Groq, OpenRouter, HF, NVIDIA) since they were in the old environment

## Cost Tracking

| Item | Droplet Path | App Platform Path |
|------|--------------|---------------------|
| Compute | $6/mo droplet | $5/mo backend + $5/mo frontend |
| Database | Included (self-hosted) | $15/mo managed |
| Storage | 25 GB SSD included | 1 GB SSD included |
| Backups | Free (cron + droplet disk) | Included |
| Bandwidth | 1 TB included | Pay-per-use |
| **Total** | **$6/mo** | **$25 to $40/mo** |

First 60 days are free either way thanks to the $200 credit.

## If You Get Stuck

Common issues:

**SSH connection refused:** The droplet IP is wrong, or your firewall is blocking. Check droplet IP in DigitalOcean dashboard.

**Docker build fails:** Run `docker compose logs backend` or `docker compose logs frontend` to see what failed.

**Database connection error:** Check `.env` POSTGRES_PASSWORD matches what is set. Try `docker compose restart backend`.

**HTTPS not working:** Caddy needs valid DNS pointing to the droplet IP. Wait a few minutes after DNS update, then `docker compose restart caddy`.

**Out of memory on $6 droplet:** Upgrade to $12 droplet (2 GB RAM). Build steps are memory-hungry but the running services fit in 1 GB.
