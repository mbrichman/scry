#!/bin/bash
# PostgreSQL Database Restore Script
# Restores a backup to the dovos_dev database on the remote dovos machine

set -e

# Configuration
REMOTE_HOST="dovos"
DB_NAME="dovos_dev"
DB_USER="dovrichman"
PG_RESTORE="/Applications/Postgres.app/Contents/Versions/latest/bin/pg_restore"
BACKUP_DIR="$HOME/dovos_backups"

# Check if backup file was provided
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lh "$BACKUP_DIR"/dovos_backup_*.backup 2>/dev/null | awk '{print "  " $9 " (" $5 ", " $6 " " $7 ")"}' || echo "  No backups found in $BACKUP_DIR"
    exit 1
fi

BACKUP_FILE="$1"

# If user provided just the filename, look in backup directory
if [ ! -f "$BACKUP_FILE" ] && [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will restore the database and may overwrite existing data!"
echo "Database: $DB_NAME on $REMOTE_HOST"
echo "Backup file: $BACKUP_FILE"
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""
echo "Starting restore of $DB_NAME on $REMOTE_HOST..."

# Copy backup file to remote machine
TEMP_BACKUP="/tmp/dovos_restore_$(basename $BACKUP_FILE)"
echo "Copying backup to remote machine..."
scp "$BACKUP_FILE" "$REMOTE_HOST:$TEMP_BACKUP"

# Restore on remote machine
echo "Restoring database..."
ssh "$REMOTE_HOST" "$PG_RESTORE -h localhost -U $DB_USER -d $DB_NAME -c $TEMP_BACKUP"

# Clean up temporary file on remote machine
ssh "$REMOTE_HOST" "rm -f $TEMP_BACKUP"

echo "✅ Restore completed successfully!"
