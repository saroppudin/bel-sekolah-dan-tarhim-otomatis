#!/bin/bash
# app/compat/system.sh
# Lightweight systemctl / rfkill / service wrapper used by the compatibility
# layer. All calls are logged and executed with a timeout. This is a
# minimal skeleton to be expanded and hardened during migration.

set -euo pipefail

LOGFILE="/var/log/otomasi_audio_compat.log"
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') - [system] $*" >>"$LOGFILE"; }

case "${1:-}" in
  restart)
    SERVICE="$2"
    log "restart $SERVICE"
    systemctl restart "$SERVICE"
    ;;
  status)
    systemctl status "$2" --no-pager
    ;;
  mask)
    systemctl mask "$2"
    ;;
  unmask)
    systemctl unmask "$2"
    ;;
  rfkill-unblock)
    rfkill unblock "$2"
    ;;
  *)
    echo "Usage: $0 {restart|status|mask|unmask|rfkill-unblock} ..."
    exit 2
    ;;
esac
