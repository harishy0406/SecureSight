#!/usr/bin/env bash
# =============================================================================
# SecureSight — PostgreSQL Database Restore Script
# Usage: ./scripts/restore_db.sh <backup_file> [--db <name>] [--force]
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ----- Defaults --------------------------------------------------------------
DB_NAME="${SECURESIGHT_DB_NAME:-securesight}"
DB_USER="${SECURESIGHT_DB_USER:-securesight}"
DB_HOST="${SECURESIGHT_DB_HOST:-localhost}"
DB_PORT="${SECURESIGHT_DB_PORT:-5432}"
FORCE=false

# ----- Parse Arguments -------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --db) DB_NAME="$2"; shift 2 ;;
        --force) FORCE=true; shift ;;
        --help)
            echo "Usage: $0 <backup_file> [--db <name>] [--force]"
            exit 0 ;;
        -*)
            echo "Unknown option: $1"
            exit 1 ;;
        *)
            BACKUP_FILE="$1"
            shift ;;
    esac
done

if [[ -z "${BACKUP_FILE:-}" ]]; then
    echo "ERROR: No backup file specified."
    echo "Usage: $0 <backup_file> [--db <name>] [--force]"
    exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

export PGPASSWORD="${SECURESIGHT_DB_PASSWORD:-securesight}"

# ----- Confirmation ----------------------------------------------------------
if ! $FORCE; then
    echo "WARNING: This will DESTROY the current database '${DB_NAME}' and restore from:"
    echo "  ${BACKUP_FILE} ($(du -h "$BACKUP_FILE" | cut -f1))"
    read -rp "Are you sure? [y/N] " CONFIRM
    if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
        echo "Restore cancelled."
        unset PGPASSWORD
        exit 0
    fi
fi

# ----- Terminate Existing Connections ----------------------------------------
echo ">>> Terminating existing connections to '${DB_NAME}'..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "
    SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = '${DB_NAME}'
      AND pid <> pg_backend_pid();
" 2>/dev/null || true

# ----- Drop and Recreate -----------------------------------------------------
echo ">>> Dropping and recreating database '${DB_NAME}'..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS \"${DB_NAME}\";" 2>/dev/null
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE \"${DB_NAME}\";"

# ----- Restore ---------------------------------------------------------------
echo ">>> Restoring from ${BACKUP_FILE}..."
RESTORE_START=$(date +%s)

if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
        -d "$DB_NAME" --verbose --no-owner --no-acl
else
    pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --verbose --no-owner --no-acl -f "$BACKUP_FILE"
fi

RESTORE_END=$(date +%s)
echo ">>> Restore complete (took $((RESTORE_END - RESTORE_START)) seconds)."

unset PGPASSWORD
echo ">>> Database restore finished successfully."
