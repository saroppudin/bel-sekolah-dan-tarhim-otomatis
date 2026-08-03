#!/bin/bash
# app/compat/asound.sh
# Manage /etc/asound.conf creation and safe backups. Provide a small
# API for switching between bluetooth and line_out that mirrors existing
# atur_output_audio.sh behavior, but as a single entrypoint usable by
# the backend compatibility layer.

set -euo pipefail

ASOUND_CONF="/etc/asound.conf"
LOGFILE="/var/log/otomasi_audio_compat.log"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') - [asound] $*" >>"$LOGFILE"; }

backup() {
  if [ -f "$ASOUND_CONF" ]; then
    cp -f "$ASOUND_CONF" "${ASOUND_CONF}.bak.$(date +%s)"
  fi
}

write_bluetooth() {
  MAC="$1"
  backup
  cat >"$ASOUND_CONF" <<EOF
pcm.!default {
  type plug
  slave.pcm "bt_speaker_aktif"
}
pcm.bt_speaker_aktif {
  type bluealsa
  device "$MAC"
  profile "a2dp"
}
ctl.!default { type bluealsa }
EOF
  log "wrote bluetooth asound.conf for $MAC"
}

write_lineout() {
  CARD="$1"
  backup
  cat >"$ASOUND_CONF" <<EOF
pcm.!default {
  type plug
  slave.pcm "line_out_aktif"
}
pcm.line_out_aktif {
  type dmix
  ipc_key 1024
  ipc_perm 0600
  slave { pcm "hw:${CARD},0" rate 48000 }
}
ctl.!default { type hw card ${CARD} }
EOF
  log "wrote lineout asound.conf for ${CARD}"
}

case "${1:-}" in
  bluetooth)
    write_bluetooth "$2"
    ;;
  lineout)
    write_lineout "$2"
    ;;
  status)
    if [ -f "$ASOUND_CONF" ]; then
      cat "$ASOUND_CONF"
    else
      echo "(no asound.conf)"
    fi
    ;;
  *)
    echo "Usage: $0 {bluetooth <mac>|lineout <card>|status}"
    exit 2
    ;;
esac
