#!/bin/bash
# Automated daily backup of the DigitalOcean postgres database.
# Set this up via cron to run daily.
#
# Add to crontab:  crontab -e
# Then add line:   0 2 * * * /path/to/backup_postgres.sh
# (runs daily at 2 AM)

set -e

BACKUP_DIR="/root/backups"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
RETENTION_DAYS=14

mkdir -p "$BACKUP_DIR"

# Source environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Dump database
docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-ai_security}" "${POSTGRES_DB:-ai_security}" \
    > "$BACKUP_DIR/postgres_$DATE.sql"

# Compress
gzip "$BACKUP_DIR/postgres_$DATE.sql"

echo "Backup created: $BACKUP_DIR/postgres_$DATE.sql.gz"

# Delete backups older than RETENTION_DAYS
find "$BACKUP_DIR" -name "postgres_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Old backups cleaned up (older than $RETENTION_DAYS days)."
