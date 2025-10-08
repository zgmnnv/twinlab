#!/usr/bin/env bash
set -euo pipefail

# --- Use container env (Compose .env) ---
PGUSER="${PGUSER:-${POSTGRES_USER:-superset}}"
PGPASSWORD="${PGPASSWORD:-${POSTGRES_PASSWORD:-}}"
export PGPASSWORD

DBNAME="${DBNAME:-dvdrental}"
ZIP_URL="${ZIP_URL:-https://www.postgresqltutorial.com/wp-content/uploads/2019/05/dvdrental.zip}"
TMP_DIR="/tmp"
ZIP_PATH="${TMP_DIR}/dvdrental.zip"
TAR_PATH="${TMP_DIR}/dvdrental.tar"

log(){ echo -e "\033[1;32m[INFO]\033[0m $*"; }
err(){ echo -e "\033[1;31m[ERR ]\033[0m $*" >&2; }

command -v psql >/dev/null       || { err "psql missing"; exit 1; }
command -v pg_restore >/dev/null || { err "pg_restore missing"; exit 1; }
command -v createdb >/dev/null   || { err "createdb missing"; exit 1; }
command -v dropdb >/dev/null     || true

# --- Ensure dvdrental.tar exists ---
if [[ ! -f "$TAR_PATH" ]]; then
  log "Downloading dvdrental dataset..."
  if command -v curl >/dev/null; then
    curl -L -o "$ZIP_PATH" "$ZIP_URL"
  elif command -v wget >/dev/null; then
    wget -O "$ZIP_PATH" "$ZIP_URL"
  else
    err "Neither curl nor wget found. Please install one."
    exit 1
  fi

  log "Extracting dvdrental.tar from ZIP..."
  if command -v unzip >/dev/null; then
    unzip -o "$ZIP_PATH" -d "$TMP_DIR" >/dev/null
  else
    err "unzip not found. Please install it or copy dvdrental.tar manually."
    exit 1
  fi

  [[ -f "$TAR_PATH" ]] || { err "dvdrental.tar not found after unzip."; exit 1; }
fi

# --- Recreate and restore database ---
log "Resetting database '$DBNAME' (owner: $PGUSER)…"
dropdb  -U "$PGUSER" "$DBNAME" 2>/dev/null || true
createdb -U "$PGUSER" -O "$PGUSER" "$DBNAME"

log "Restoring from $TAR_PATH..."
pg_restore -U "$PGUSER" \
  --no-owner --no-privileges \
  --clean --if-exists \
  -d "$DBNAME" "$TAR_PATH"

log "✅ dvdrental restored successfully for user '$PGUSER'"
