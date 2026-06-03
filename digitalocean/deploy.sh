#!/bin/bash
# One-shot deployment script for DigitalOcean Droplet.
# Run this AFTER you have SSH'd into your droplet and cloned the repo.
#
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh

set -e

echo "==> Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "Docker not installed. Run: curl -fsSL https://get.docker.com | sh"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "Docker Compose not installed."; exit 1; }

if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Copy .env.example to .env and fill in real values."
    exit 1
fi

echo "==> Pulling latest code..."
git pull origin main

echo "==> Building containers..."
docker compose build

echo "==> Starting services..."
docker compose up -d

echo "==> Waiting for postgres to be ready..."
sleep 10

echo "==> Running database migrations..."
docker compose exec backend python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine); print('Tables created')"

echo "==> Restoring backup if render_backup.sql exists..."
if [ -f render_backup.sql ]; then
    echo "Found render_backup.sql, restoring..."
    docker compose exec -T postgres psql -U "${POSTGRES_USER:-ai_security}" -d "${POSTGRES_DB:-ai_security}" < render_backup.sql
    echo "Backup restored."
else
    echo "No render_backup.sql found, skipping restore (starting with empty database)."
fi

echo "==> Checking service health..."
sleep 5
docker compose ps

echo ""
echo "==> Deployment complete!"
echo "Frontend: http://$(curl -s ifconfig.me)"
echo "Backend:  http://$(curl -s ifconfig.me):8000/api/v1/health"
echo ""
echo "If you set up a domain in Caddyfile, HTTPS will activate within 60 seconds."
