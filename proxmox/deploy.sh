#!/usr/bin/env bash
# Copy the project into the three CTs and start each Docker Compose stack.
# Run as root on the Proxmox host after ./create-cts.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
# shellcheck source=config.env
source "$SCRIPT_DIR/config.env"

log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "run this script as root"
command -v pct >/dev/null || die "pct not found — this must run on a Proxmox host"
for id in "$DB_ID" "$APP_ID" "$WEB_ID"; do
  pct status "$id" >/dev/null 2>&1 || die "CT $id does not exist; run ./create-cts.sh first"
done

push_repo() {
  local id=$1
  log "copying project into CT $id:/opt/datanotes"
  tar czf - \
    --exclude='./.git' \
    --exclude='./proxmox' \
    --exclude='node_modules' \
    --exclude='.venv' \
    --exclude='dist' \
    --exclude='.env' \
    --exclude='*.db' \
    -C "$ROOT" . \
    | pct exec "$id" -- bash -lc \
        "rm -rf /opt/datanotes && mkdir -p /opt/datanotes && tar xzf - -C /opt/datanotes"
}

# --- 1. database ---------------------------------------------------------
push_repo "$DB_ID"
pct exec "$DB_ID" -- bash -lc "cd /opt/datanotes/database && cat > .env <<'EOF'
POSTGRES_DB=${DB_NAME}
POSTGRES_USER=${DB_USER}
POSTGRES_PASSWORD=${DB_PASSWORD}
EOF
docker compose up -d"

log "waiting for the database to accept connections..."
for _ in $(seq 1 30); do
  if pct exec "$DB_ID" -- docker exec datanotes-db \
      pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
    log "database ready"
    break
  fi
  sleep 3
done

# --- 2. app (Flask + React) ---------------------------------------------
push_repo "$APP_ID"
pct exec "$APP_ID" -- bash -lc "cd /opt/datanotes/backend && cat > .env <<'EOF'
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_IP}:5432/${DB_NAME}
EOF
docker compose up -d --build"

# --- 3. web (landing) ----------------------------------------------------
push_repo "$WEB_ID"
pct exec "$WEB_ID" -- bash -lc "cd /opt/datanotes/landing && cat > config.js <<EOF
window.DATANOTES_APP_URL = \"http://${APP_IP}\"
EOF
docker compose up -d"

log "deployment complete:"
log "  landing page : http://${WEB_IP}"
log "  notes app    : http://${APP_IP}"
log "  database     : ${DB_IP}:5432"
