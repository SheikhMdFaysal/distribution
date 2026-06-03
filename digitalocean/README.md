# DigitalOcean Deployment

Complete migration kit from Render to DigitalOcean.

## Start Here

Read these in order:

1. **`BACKUP_RENDER_FIRST.md`** — URGENT. Back up your Render database before the 14-day deletion window closes.
2. **`DIGITALOCEAN_MIGRATION.md`** — Full step-by-step migration guide. Pick Path A (Droplet, $6/mo) or Path B (App Platform, $40/mo).
3. **`AUTODEPLOY_SETUP.md`** — Set up auto-deploy on git push (only after Step 2 is working). Makes the droplet behave exactly like Render.

## Files in This Folder

| File | Purpose |
|------|---------|
| `BACKUP_RENDER_FIRST.md` | Urgent: backup Render data |
| `DIGITALOCEAN_MIGRATION.md` | Main migration guide |
| `AUTODEPLOY_SETUP.md` | GitHub Actions auto-deploy guide |
| `docker-compose.yml` | Droplet deployment (Path A) |
| `Caddyfile` | HTTPS reverse proxy for droplet |
| `app-platform.yaml` | App Platform spec (Path B) |
| `.env.example` | Environment variables template |
| `deploy.sh` | One-shot deploy script for droplet |
| `backup_postgres.sh` | Automated daily database backup |
| `setup_deploy_key.sh` | One-time setup for GitHub Actions auto-deploy |

The GitHub Actions workflow itself lives at:
`distribution/.github/workflows/deploy-digitalocean.yml`

## Recommended Path

**Path A (Droplet + Docker Compose) at $6/month.** It is 6x cheaper than App Platform, includes 1 TB bandwidth, and works identically once set up. Free for the first 60 days thanks to DigitalOcean's $200 new-user credit.
