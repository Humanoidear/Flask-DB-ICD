#!/usr/bin/env bash
# Create the three Proxmox LXC containers and install Docker in each.
# Run as root on the Proxmox host, from the proxmox/ directory.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=config.env
source "$SCRIPT_DIR/config.env"

log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mwarn:\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "run this script as root"
command -v pct >/dev/null || die "pct not found — this must run on a Proxmox host"

if ! pveam list local 2>/dev/null | grep -q "$(basename "$TEMPLATE")"; then
  warn "template '$TEMPLATE' not found locally."
  warn "download it first, e.g.:"
  warn "  pveam update"
  warn "  pveam download local $(basename "$TEMPLATE")"
fi

create_ct() {
  local id=$1 host=$2 ip=$3 cores=$4 mem=$5
  if pct status "$id" >/dev/null 2>&1; then
    log "CT $id ($host) already exists"
    pct status "$id" | grep -q running || { log "starting CT $id"; pct start "$id"; }
    return
  fi
  log "creating CT $id ($host) at $ip"
  pct create "$id" "$TEMPLATE" \
    --hostname "$host" \
    --cores "$cores" --memory "$mem" --swap 512 \
    --rootfs "${STORAGE}:8" \
    --net0 "name=eth0,bridge=${BRIDGE},ip=${ip}/${CIDR},gw=${GATEWAY}" \
    --features "nesting=1,keyctl=1" \
    --unprivileged 1 \
    --onboot 1 \
    --password "$CT_PASSWORD" \
    --start 1
}

install_docker() {
  local id=$1
  log "waiting for CT $id to come online..."
  for _ in $(seq 1 30); do
    if pct exec "$id" -- ping -c1 -W1 "$GATEWAY" >/dev/null 2>&1; then break; fi
    sleep 2
  done
  log "installing Docker in CT $id (this takes a minute)"
  pct exec "$id" -- bash -lc "apt-get update -qq && apt-get install -y -qq ca-certificates curl"
  pct exec "$id" -- bash -lc "curl -fsSL https://get.docker.com | sh"
}

for spec in \
  "$DB_ID $DB_HOST $DB_IP $DB_CORES $DB_MEM" \
  "$APP_ID $APP_HOST $APP_IP $APP_CORES $APP_MEM" \
  "$WEB_ID $WEB_HOST $WEB_IP $WEB_CORES $WEB_MEM"; do
  # shellcheck disable=SC2086
  create_ct $spec
done

for id in "$DB_ID" "$APP_ID" "$WEB_ID"; do
  install_docker "$id"
done

log "done. run ./deploy.sh next."
