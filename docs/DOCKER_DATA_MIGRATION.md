# Docker Data Migration Guide

This guide covers migrating existing PostgreSQL data from your host machine to the containerized PostgreSQL instance.

## Overview

You have two migration approaches:

1. **Fresh Start** - Start with empty database and re-import source conversations
2. **Data Migration** - Export existing data and import into Docker PostgreSQL

## Prerequisites

- Host PostgreSQL with existing Dovos data
- Docker and docker-compose installed
- Sufficient disk space for backup files

## Option 1: Fresh Start (Recommended for Development)

If you can easily re-import your source conversation files, this is the simplest approach.

### Steps

```bash
# 1. Start containerized stack
docker compose up -d

# 2. Run migrations
docker compose exec dovos-rag alembic upgrade head

# 3. Re-import your source conversations
# Copy source files to data/source/ if not already there
# Then use your import scripts or UI to re-import conversations
```

**Pros:**
- Clean, fresh database
- No migration complexity
- Guaranteed schema consistency

**Cons:**
- Need to re-import all conversations
- Loses any manual database changes

## Option 2: Full Data Migration

If you need to preserve all existing data exactly as-is, follow this complete migration process.

### Step 1: Backup Host PostgreSQL

```bash
# Create backup directory
mkdir -p ./backups

# Get your host database credentials
# Check your .env file or use these common defaults:
HOST_USER="your_postgres_user"
HOST_DB="dovos"

# Option A: SQL format backup (text, easy to inspect)
pg_dump -U $HOST_USER -d $HOST_DB > ./backups/host_backup_$(date +%Y%m%d_%H%M%S).sql

# Option B: Custom format backup (compressed, faster)
pg_dump -U $HOST_USER -d $HOST_DB -Fc > ./backups/host_backup_$(date +%Y%m%d_%H%M%S).dump

# Verify backup was created
ls -lh ./backups/
```

### Step 2: Start Docker PostgreSQL

```bash
# Make sure .env is configured with PostgreSQL credentials
# POSTGRES_USER=dovos
# POSTGRES_PASSWORD=your_password
# POSTGRES_DB=dovos

# Start only the PostgreSQL container first
docker compose up -d postgres

# Wait for PostgreSQL to be ready
docker compose exec postgres pg_isready -U dovos

# Verify pgvector extension was created
docker compose exec postgres psql -U dovos -d dovos -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### Step 3: Import Data into Docker PostgreSQL

#### Method A: Using SQL Backup

```bash
# Import SQL file directly
docker compose exec -T postgres psql -U dovos -d dovos < ./backups/host_backup.sql

# Check for errors in the output
# Some warnings about existing extensions are normal
```

#### Method B: Using Custom Format Backup

```bash
# Copy backup file into container
docker cp ./backups/host_backup.dump dovos-postgres:/tmp/

# Restore from backup
docker compose exec postgres pg_restore -U dovos -d dovos -c -v /tmp/host_backup.dump

# Clean up
docker compose exec postgres rm /tmp/host_backup.dump
```

### Step 4: Verify Migration

```bash
# Check table counts
docker compose exec postgres psql -U dovos -d dovos -c "
  SELECT 
    schemaname,
    tablename,
    n_tup_ins - n_tup_del as row_count
  FROM pg_stat_user_tables
  ORDER BY row_count DESC;
"

# Verify conversations exist
docker compose exec postgres psql -U dovos -d dovos -c "
  SELECT COUNT(*) as conversation_count FROM conversations;
"

# Verify messages exist
docker compose exec postgres psql -U dovos -d dovos -c "
  SELECT COUNT(*) as message_count FROM messages;
"

# Verify embeddings exist (if you use pgvector)
docker compose exec postgres psql -U dovos -d dovos -c "
  SELECT COUNT(*) as embeddings_count FROM message_embeddings;
"

# Check Alembic migration version
docker compose exec postgres psql -U dovos -d dovos -c "
  SELECT version_num FROM alembic_version;
"
```

### Step 5: Start Application

```bash
# Start the full stack
docker compose up -d

# Watch logs to ensure clean startup
docker compose logs -f dovos-rag

# Run any pending migrations (if needed)
docker compose exec dovos-rag alembic upgrade head

# Test the application
curl http://localhost:5001/api/stats
```

### Step 6: Validate Application

```bash
# Test search functionality
curl -X POST http://localhost:5001/api/rag/query \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "test search query",
    "context_window": 3
  }'

# Check web UI
open http://localhost:5001
```

## Troubleshooting

### Migration Errors

**"ERROR: extension 'vector' already exists"**
- This is normal - the init script creates it, then restore tries to create it again
- Safe to ignore

**"ERROR: role 'your_old_user' does not exist"**
- Your backup references the old PostgreSQL user
- Fix: Edit the SQL backup file and replace old username with `dovos`
- Or: Create the old user in Docker PostgreSQL:
  ```bash
  docker compose exec postgres psql -U dovos -d dovos -c "CREATE USER your_old_user;"
  ```

**"ERROR: database 'dovos' already exists"**
- The database is auto-created by docker-compose
- Use `-c` or `--clean` flag with pg_restore to drop existing objects first

### Version Mismatches

**Schema version conflicts:**
```bash
# Check current migration version
docker compose exec postgres psql -U dovos -d dovos -c "SELECT version_num FROM alembic_version;"

# Downgrade to specific version if needed
docker compose exec dovos-rag alembic downgrade <version>

# Upgrade to latest
docker compose exec dovos-rag alembic upgrade head
```

### Performance Issues

**Large database import is slow:**
- Use custom format (`-Fc`) which is compressed
- Disable triggers during restore: `pg_restore --disable-triggers`
- Import with multiple jobs: `pg_restore -j 4` (uses 4 parallel jobs)

**Connection timeouts:**
- Increase startup timeout in docker-compose.yml:
  ```yaml
  healthcheck:
    start_period: 60s  # Increase if needed
  ```

## Rollback Plan

If migration fails, you can easily return to host PostgreSQL:

```bash
# Stop Docker containers
docker compose down

# Update .env to use host PostgreSQL
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/dovos

# Start application normally (without Docker)
python app.py
```

Your host PostgreSQL data remains untouched during migration.

## Post-Migration Cleanup

After successful migration and validation:

```bash
# Optional: Remove backup files to save space
# (Keep at least one backup for safety!)
rm -i ./backups/host_backup_*.sql
rm -i ./backups/host_backup_*.dump

# Optional: Stop host PostgreSQL service if no longer needed
brew services stop postgresql@16  # or your version
```

## Best Practices

1. **Always backup before migration** - The migration process is non-destructive to host data, but backups are essential
2. **Test in development first** - Try migration with a copy of production data before migrating production
3. **Verify data integrity** - Check row counts and sample queries before decommissioning host PostgreSQL
4. **Keep multiple backups** - Keep backups from different time periods
5. **Document custom changes** - If you have custom PostgreSQL settings, document them for the Docker setup

## Regular Backups

After migration, set up regular backups:

```bash
# Create backup script
cat > backup-dovos.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker compose exec -T postgres pg_dump -U dovos -d dovos -Fc > "$BACKUP_DIR/dovos_$TIMESTAMP.dump"
# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "dovos_*.dump" -mtime +7 -delete
echo "Backup completed: $BACKUP_DIR/dovos_$TIMESTAMP.dump"
EOF

chmod +x backup-dovos.sh

# Run manually or add to cron
# Daily at 2 AM: 0 2 * * * /path/to/backup-dovos.sh
```

## Support

If you encounter issues:

1. Check Docker logs: `docker compose logs postgres`
2. Check application logs: `docker compose logs dovos-rag`
3. Verify network connectivity: `docker compose exec dovos-rag ping postgres`
4. Test database connection: `docker compose exec dovos-rag python -c "from db.database import test_connection; print(test_connection())"`
