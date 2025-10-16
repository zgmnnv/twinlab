#!/usr/bin/env bash
set -euo pipefail

PGUSER="${PGUSER:-${POSTGRES_USER:-superset}}"
PGPASSWORD="${PGPASSWORD:-${POSTGRES_PASSWORD:-}}"
export PGPASSWORD

DBNAME="${DBNAME:-northwind}"
ZIP_URL="${ZIP_URL:-https://github.com/pthom/northwind_psql/archive/refs/heads/master.zip}"
TMP_DIR="/tmp"
ZIP_PATH="${TMP_DIR}/northwind.zip"
SQL_DIR="${TMP_DIR}/northwind_sql"
SQL_PATH="${SQL_DIR}/northwind.sql"

log(){ echo -e "\033[1;32m[INFO]\033[0m $*"; }
err(){ echo -e "\033[1;31m[ERR ]\033[0m $*" >&2; }

command -v psql >/dev/null     || { err "psql missing"; exit 1; }
command -v createdb >/dev/null || { err "createdb missing"; exit 1; }
command -v dropdb >/dev/null   || true

# --- Ensure Northwind SQL exists ---
if [[ ! -f "$SQL_PATH" ]]; then
  log "Downloading Northwind dataset..."
  mkdir -p "$SQL_DIR"

  if command -v curl >/dev/null; then
    curl -L -o "$ZIP_PATH" "$ZIP_URL"
  elif command -v wget >/dev/null; then
    wget -O "$ZIP_PATH" "$ZIP_URL"
  else
    err "Neither curl nor wget found."
    exit 1
  fi

  log "Extracting Northwind SQL..."
  if command -v unzip >/dev/null; then
    unzip -o "$ZIP_PATH" -d "$SQL_DIR" >/dev/null
  else
    err "unzip not found."
    exit 1
  fi

  FOUND_SQL="$(find "$SQL_DIR" -type f -name 'northwind.sql' | head -n 1 || true)"
  if [[ -z "$FOUND_SQL" ]]; then
    err "northwind.sql not found after extraction."
    exit 1
  fi

  mv "$FOUND_SQL" "$SQL_PATH"
fi

# --- Recreate and restore database ---
log "Resetting database '$DBNAME' (owner: $PGUSER)…"
psql -U "$PGUSER" -d postgres -v ON_ERROR_STOP=0 -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DBNAME}';" >/dev/null || true
dropdb  -U "$PGUSER" "$DBNAME" 2>/dev/null || true
createdb -U "$PGUSER" -O "$PGUSER" "$DBNAME"

log "Restoring from $SQL_PATH..."
psql -U "$PGUSER" -v ON_ERROR_STOP=1 -d "$DBNAME" -f "$SQL_PATH"

log "✅ Northwind restored successfully for user '$PGUSER'"
