# URGENT: Backup Render Database Before Migration

You have 14 days from the Render expiration email before your data is deleted permanently. Do this step first, before anything else.

## Option 1: Backup via Render Dashboard (Easiest)

1. Log in to https://dashboard.render.com
2. Click on your database `ai-security-db`
3. Look for "Backups" tab or "Restore" section
4. If a recent backup is listed, click "Download"
5. Save the `.sql` or `.dump` file somewhere safe (e.g., this folder)

If Render does not show backups on free tier (likely the case), use Option 2.

## Option 2: Manual Export with pg_dump (5 minutes)

You need the External Database URL from Render. Find it here:

1. Log in to https://dashboard.render.com
2. Click your `ai-security-db` database
3. Scroll to "Connections" section
4. Copy the value next to "External Database URL"
   (looks like: `postgresql://user:password@somehost.oregon-postgres.render.com/ai_security`)

Then open PowerShell on your Windows machine and run:

```powershell
# Install PostgreSQL client tools if you do not have them
# Download from: https://www.postgresql.org/download/windows/
# Or use chocolatey: choco install postgresql

# Set the connection string (paste yours below)
$env:RENDER_DB_URL = "postgresql://user:password@somehost.oregon-postgres.render.com/ai_security"

# Run the backup (saves to current folder as backup.sql)
pg_dump $env:RENDER_DB_URL --no-owner --no-acl --format=plain --file="render_backup_$(Get-Date -Format yyyy-MM-dd).sql"
```

You should get a file named `render_backup_2026-06-02.sql` (or similar) in the current folder.

## Option 3: Quick Test Whether Backup Worked

Open the .sql file in Notepad. You should see SQL statements like:

```sql
CREATE TABLE security_tests (...);
INSERT INTO security_tests VALUES (...);
```

If you see those, the backup is good. Keep this file safe.

## What to Do With the Backup

Once you have the .sql file:

1. Copy it to two places (USB drive, cloud storage) for safety
2. Continue with the migration to DigitalOcean
3. After the new database is set up on DigitalOcean, you will restore from this file

## If You Cannot Do This Yourself

The platform has been mostly test data. If you cannot run pg_dump and the data is not critical, you can skip the backup and start fresh on DigitalOcean. The new database will be empty but the application will work the same way.
