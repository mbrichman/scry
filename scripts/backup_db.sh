#!/bin/bash
# PostgreSQL Database Backup Script
# Backs up the dovos_dev database from the remote dovos machine

set -e

# Configuration
REMOTE_HOST="dovos"
DB_NAME="dovos_dev"
DB_USER="dovrichman"
PG_DUMP="/Applications/Postgres.app/Contents/Versions/latest/bin/pg_dump"
BACKUP_DIR="$HOME/dovos_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/dovos_backup_$TIMESTAMP.backup"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Starting backup of $DB_NAME from $REMOTE_HOST..."
echo "Backup file: $BACKUP_FILE"

# Run pg_dump on remote machine and save locally
ssh "$REMOTE_HOST" "$PG_DUMP -h localhost -U $DB_USER -d $DB_NAME -F c" > "$BACKUP_FILE"

# Check if backup was successful
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Backup completed successfully!"
    echo "   File: $BACKUP_FILE"
    echo "   Size: $BACKUP_SIZE"
    
    # Keep only the last 7 backups
    echo "Cleaning up old backups (keeping last 7)..."
    ls -t "$BACKUP_DIR"/dovos_backup_*.backup | tail -n +8 | xargs -r rm -f
    
    echo "Remaining backups:"
    ls -lh "$BACKUP_DIR"/dovos_backup_*.backup | awk '{print "  " $9 " (" $5 ")"}'
else
    echo "❌ Backup failed!"
    exit 1
fi
