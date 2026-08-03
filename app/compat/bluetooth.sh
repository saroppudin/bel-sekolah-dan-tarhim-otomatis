#!/bin/bash
# app/compat/bluetooth.sh
# Compatibility wrapper skeleton for Bluetooth operations.
# Purpose: provide a stable CLI used by the backend compatibility layer
# to perform bluetooth actions. This file is intentionally minimal —
# implementation will call the underlying system commands with strict
# input validation, timeouts, and structured logging.

set -euo pipefail

LOGFILE="/var/log/otomasi_audio_compat.log"

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - [bluetooth] $*" >>"$LOGFILE"
}

usage() {
  cat <<EOF
Usage: $0 {scan|pair|trust|connect|disconnect|info|list}
EOF
}

case "${1:-}" in
  scan)
    log "scan requested"
    timeout 10 bluetoothctl --timeout 10 scan on || true
    ;;
  pair)
    MAC="${2:-}"
    log "pair requested: $MAC"
    bluetoothctl agent NoInputNoOutput >/dev/null 2>&1 || true
    bluetoothctl default-agent >/dev/null 2>&1 || true
    bluetoothctl pair "$MAC"
    ;;
  trust)
    MAC="${2:-}"
    log "trust requested: $MAC"
    bluetoothctl trust "$MAC"
    ;;
  connect)
    MAC="${2:-}"
    log "connect requested: $MAC"
    bluetoothctl connect "$MAC"
    ;;
  disconnect)
    MAC="${2:-}"
    log "disconnect requested: $MAC"
    bluetoothctl disconnect "$MAC"
    ;;
  info)
    MAC="${2:-}"
    bluetoothctl info "$MAC"
    ;;
  list)
    bluetoothctl devices
    ;;
  *)
    usage
    exit 2
    ;;
esac
