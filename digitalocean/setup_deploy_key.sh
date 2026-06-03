#!/bin/bash
# One-time setup script for GitHub Actions auto-deploy.
# Run this ONCE on your droplet after the initial deployment is working.
#
# Usage:
#   ssh root@YOUR_DROPLET_IP
#   cd /root/Enterprise-AI-Security-Red-Teaming-Platform/distribution/digitalocean
#   chmod +x setup_deploy_key.sh
#   ./setup_deploy_key.sh

set -e

KEY_PATH="/root/.ssh/github_actions_deploy"

echo "==> Generating a fresh SSH key pair for GitHub Actions..."

if [ -f "$KEY_PATH" ]; then
    echo "Key already exists at $KEY_PATH"
    read -p "Overwrite? [y/N] " confirm
    if [ "$confirm" != "y" ]; then
        echo "Aborted."
        exit 0
    fi
fi

ssh-keygen -t ed25519 -C "github-actions-deploy" -f "$KEY_PATH" -N ""

echo ""
echo "==> Adding the public key to authorized_keys..."
cat "${KEY_PATH}.pub" >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

echo ""
echo "============================================================"
echo "  SETUP COMPLETE.  Copy the values below into GitHub."
echo "============================================================"
echo ""
echo "Go to your GitHub repo:"
echo "  Settings -> Secrets and variables -> Actions -> New repository secret"
echo ""
echo "Add these three secrets:"
echo ""
echo "  Name:  DROPLET_HOST"
echo "  Value: $(curl -s ifconfig.me)"
echo ""
echo "  Name:  DROPLET_USER"
echo "  Value: root"
echo ""
echo "  Name:  DROPLET_SSH_KEY"
echo "  Value: (paste the entire contents below, including BEGIN and END lines)"
echo ""
echo "------ BEGIN PRIVATE KEY (copy everything between the dashes) ------"
cat "$KEY_PATH"
echo "------ END PRIVATE KEY ------"
echo ""
echo "============================================================"
echo "  IMPORTANT: After adding the secrets, delete this output"
echo "  from your terminal history for security."
echo "============================================================"
