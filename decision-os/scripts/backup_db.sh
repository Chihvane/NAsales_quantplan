#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${1:-decision_os_prod}"
BACKUP_DIR="${2:-./backups}"

mkdir -p "$BACKUP_DIR"
pg_dump "$DB_NAME" > "$BACKUP_DIR/${DB_NAME}_$(date +%Y%m%d_%H%M%S).sql"
