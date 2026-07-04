#!/usr/bin/env bash
# =============================================================================
# SecureSight — Health Check Script
# Usage: ./scripts/health_check.sh [--all] [--api] [--db] [--redis]
# =============================================================================

set -euo pipefail

BASE_URL="${SECURESIGHT_API_URL:-http://localhost:8000}"
DB_HOST="${SECURESIGHT_DB_HOST:-localhost}"
DB_PORT="${SECURESIGHT_DB_PORT:-5432}"
DB_USER="${SECURESIGHT_DB_USER:-securesight}"
DB_NAME="${SECURESIGHT_DB_NAME:-securesight}"
REDIS_HOST="${SECURESIGHT_REDIS_HOST:-localhost}"
REDIS_PORT="${SECURESIGHT_REDIS_PORT:-6379}"

CHECK_API=false
CHECK_DB=false
CHECK_REDIS=false

# ----- Argument Parsing ------------------------------------------------------
if [[ $# -eq 0 ]]; then
    CHECK_API=true
    CHECK_DB=true
    CHECK_REDIS=true
else
    for arg in "$@"; do
        case "$arg" in
            --all) CHECK_API=true; CHECK_DB=true; CHECK_REDIS=true ;;
            --api) CHECK_API=true ;;
            --db) CHECK_DB=true ;;
            --redis) CHECK_REDIS=true ;;
            --help)
                echo "Usage: $0 [--all] [--api] [--db] [--redis]"
                exit 0 ;;
            *) echo "Unknown option: $arg"; exit 1 ;;
        esac
    done
fi

PASS=0
FAIL=0

check() {
    local name="$1" status="$2" detail="$3"
    if [[ "$status" -eq 0 ]]; then
        echo "  [PASS] ${name}: ${detail}"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] ${name}: ${detail}"
        FAIL=$((FAIL + 1))
    fi
}

# ----- API Check -------------------------------------------------------------
if $CHECK_API; then
    echo ">>> Checking API health..."
    API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${BASE_URL}/api/v1/health" 2>/dev/null || echo "000")
    if [[ "$API_STATUS" == "200" ]]; then
        RESPONSE=$(curl -s --max-time 5 "${BASE_URL}/api/v1/health" 2>/dev/null || echo '{"status":"unreachable"}')
        DETAIL=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))" 2>/dev/null || echo "HTTP ${API_STATUS}")
        check "API" 0 "$DETAIL"
    else
        check "API" 1 "HTTP ${API_STATUS}"
    fi
fi

# ----- Database Check --------------------------------------------------------
if $CHECK_DB; then
    echo ">>> Checking database connectivity..."
    export PGPASSWORD="${SECURESIGHT_DB_PASSWORD:-securesight}"
    if command -v pg_isready &>/dev/null; then
        pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q 2>/dev/null && \
            check "PostgreSQL" 0 "running on ${DB_HOST}:${DB_PORT}" || \
            check "PostgreSQL" 1 "not reachable on ${DB_HOST}:${DB_PORT}"
    else
        check "PostgreSQL" 1 "pg_isready not found"
    fi
    unset PGPASSWORD
fi

# ----- Redis Check -----------------------------------------------------------
if $CHECK_REDIS; then
    echo ">>> Checking Redis connectivity..."
    if command -v redis-cli &>/dev/null; then
        REDIS_PONG=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null || echo "FAIL")
        if [[ "$REDIS_PONG" == "PONG" ]]; then
            check "Redis" 0 "running on ${REDIS_HOST}:${REDIS_PORT}"
        else
            check "Redis" 1 "not responding on ${REDIS_HOST}:${REDIS_PORT}"
        fi
    else
        check "Redis" 1 "redis-cli not found"
    fi
fi

# ----- Summary ---------------------------------------------------------------
echo ""
echo "=== Health Check Results ==="
echo "  PASS: ${PASS}"
echo "  FAIL: ${FAIL}"
if [[ "$FAIL" -gt 0 ]]; then
    echo "  Status: UNHEALTHY"
    exit 1
else
    echo "  Status: HEALTHY"
    exit 0
fi
