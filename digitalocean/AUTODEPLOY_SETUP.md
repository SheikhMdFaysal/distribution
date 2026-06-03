# GitHub Actions Auto-Deploy Setup

This makes your droplet behave exactly like Render: every push to `main` triggers an automatic deployment within about 2 minutes.

## How It Works

1. You push code to GitHub.
2. GitHub Actions starts a workflow.
3. The workflow SSHes into your droplet.
4. It pulls the latest code, rebuilds containers, and restarts services.
5. It runs a health check to confirm everything is up.

Total time: 1 to 3 minutes per deploy.

## Prerequisites

Before setting this up, you must already have:

- A working DigitalOcean droplet running the platform (followed Path A in `DIGITALOCEAN_MIGRATION.md`)
- The droplet's IP address
- Your GitHub repo (private is fine)

## One-Time Setup (10 minutes)

### Step 1: Generate the Deploy Key on the Droplet

SSH into your droplet:

```bash
ssh root@YOUR_DROPLET_IP
cd /root/Enterprise-AI-Security-Red-Teaming-Platform/distribution/digitalocean
chmod +x setup_deploy_key.sh
./setup_deploy_key.sh
```

The script will print three values you need to copy:

- `DROPLET_HOST` (your droplet IP)
- `DROPLET_USER` (will be `root`)
- `DROPLET_SSH_KEY` (a long private key block)

Keep this terminal window open. You will copy from it in the next step.

### Step 2: Add Secrets to GitHub

In a browser, go to your GitHub repo:

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

Add three secrets one at a time, using the exact values from Step 1:

**Secret 1:**
- Name: `DROPLET_HOST`
- Value: (the IP address printed by the script)

**Secret 2:**
- Name: `DROPLET_USER`
- Value: `root`

**Secret 3:**
- Name: `DROPLET_SSH_KEY`
- Value: (the entire block between BEGIN and END lines, including those lines)

Click `Add secret` after each one.

### Step 3: Clear Terminal History (Security)

Back in the SSH session on the droplet:

```bash
history -c
clear
exit
```

This removes the private key from your shell history.

### Step 4: Test the Workflow

Make a tiny change to any non-doc file (or just trigger it manually):

**Option A: Trigger manually**

1. Go to your GitHub repo
2. Click `Actions` tab
3. Click `Deploy to DigitalOcean` in the left sidebar
4. Click `Run workflow` → `Run workflow`

**Option B: Push a commit**

```powershell
# Make any small change
cd "C:\Users\sober\Documents\Faysal\Enterprise AI Security Red Teaming Platform"
echo "# Trigger deploy" >> distribution\README.md
git add distribution\README.md
git commit -m "Test auto-deploy to DigitalOcean"
git push origin main
```

### Step 5: Watch the Deployment

1. Go to your GitHub repo → `Actions` tab
2. Click the running workflow
3. Click `deploy` to see live logs

You should see:

- Checkout repository
- Set up SSH agent
- Verify SSH connection
- Deploy on droplet (this is where containers rebuild)
- Verify backend health

Total time: 90 to 180 seconds for the first deploy, faster after that (Docker layer cache).

## Daily Workflow After Setup

Once auto-deploy is working, your daily workflow is identical to Render:

1. Make code changes locally
2. `git push origin main`
3. Wait 2 minutes
4. Visit your site, changes are live

You can also see deploy status in the GitHub Actions tab, including past deployments and their results.

## Troubleshooting

### "Permission denied (publickey)" in SSH step

The `DROPLET_SSH_KEY` secret is wrong or incomplete. Re-run `setup_deploy_key.sh` and copy the entire private key block, including the `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----` lines.

### "Host key verification failed"

The droplet IP changed or DNS is misconfigured. Update the `DROPLET_HOST` secret to match the current IP.

### Backend health check fails but deploy succeeded

Usually means the backend is slow to start. Check directly:

```bash
ssh root@YOUR_DROPLET_IP
cd /root/Enterprise-AI-Security-Red-Teaming-Platform/distribution/digitalocean
docker compose logs --tail=100 backend
```

### Deploy succeeds but old code is still showing

Browser cache. Hard refresh with `Ctrl+Shift+R` or open in private/incognito.

### How to disable auto-deploy temporarily

In GitHub: `Settings` → `Actions` → `General` → `Disable Actions` or just disable the specific workflow under the Actions tab.

## Security Notes

- The deploy key only works from GitHub Actions (it is stored as an encrypted secret).
- The key has full SSH access to your droplet. Treat it like a password.
- If the key is ever exposed, run `setup_deploy_key.sh` again to rotate it, then update the GitHub secret.
- Consider creating a dedicated `deploy` user instead of `root` for a production setup. For now, root works and is simpler.

## What Got Created

| File | What It Does |
|------|---------------|
| `.github/workflows/deploy-digitalocean.yml` | The GitHub Actions workflow (lives in your repo) |
| `setup_deploy_key.sh` | One-time setup script to generate the SSH key on the droplet |
| `AUTODEPLOY_SETUP.md` | This guide |

Once set up, you only ever interact with `git push`. Everything else is automated.
