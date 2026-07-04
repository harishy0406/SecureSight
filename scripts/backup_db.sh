#!/usr/bin/env bash
# =============================================================================
# SecureSight — PostgreSQL Database Backup Script
# Usage: ./scripts/backup_db.sh [--db <name>] [--output <dir>] [--compress]
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ----- Defaults --------------------------------------------------------------
DB_NAME="${SECURESIGHT_DB_NAME:-securesight}"
DB_USER="${SECURESIGHT_DB_USER:-securesight}"
DB_HOST="${SECURESIGHT_DB_HOST:-localhost}"
DB_PORT="${SECURESIGHT_DB_PORT:-5432}"
OUTPUT_DIR="${PROJECT_DIR}/backups"
COMPRESS=false
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ----- Parse Arguments -------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --db) DB_NAME="$2"; shift 2 ;;
        --output) OUTPUT_DIR="$2"; shift 2 ;;
        --compress) COMPRESS=true; shift ;;
        --retention) RETENTION_DAYS="$2"; shift 2 ;;
        --help)
            echo "Usage: $0 [--db <name>] [--output <dir>] [--compress] [--retention <days>]"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

mkdir -p "$OUTPUT_DIR"

export PGPASSWORD="${SECURESIGHT_DB_PASSWORD:-securesight}"

# ----- Health Check ----------------------------------------------------------
echo ">>> Checking database connectivity..."
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q 2>/dev/null; then
    echo "ERROR: Database is not reachable at ${DB_HOST}:${DB_PORT}"
    exit 1
fi

# ----- Backup ----------------------------------------------------------------
DUMP_FILE="${OUTPUT_DIR}/${DB_NAME}_${TIMESTAMP}.dump"
echo ">>> Starting backup: ${DUMP_FILE}"

if $COMPRESS; then
    DUMP_FILE="${DUMP_FILE}.gz"
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --format=custom --verbose --no-owner --no-acl | gzip > "$DUMP_FILE"
else
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --format=custom --verbose --no-owner --no-acl -f "$DUMP_FILE"
fi

echo ">>> Backup complete: $(du -h "$DUMP_FILE" | cut -f1)"

# ----- Rotation --------------------------------------------------------------
echo ">>> Cleaning backups older than ${RETENTION_DAYS} days..."
find "$OUTPUT_DIR" -name "${DB_NAME}_*.dump*" -type f -mtime "+${RETENTION_DAYS}" -delete
find "$OUTPUT_DIR" -name "${DB_NAME}_*.dump.gz" -type f -mtime "+${RETENTION_DAYS}" -delete

echo ">>> Remaining backups:"
ls -lh "${OUTPUT_DIR}"/*.dump* 2>/dev/null || echo "(none)"

unset PGPASSWORD
echo ">>> Backup finished successfully."
