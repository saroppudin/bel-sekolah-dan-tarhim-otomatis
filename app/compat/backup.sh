#!/bin/bash
# app/compat/backup.sh
# Compatibility wrapper skeleton to create consistent backups used by
# the legacy scripts and the migration process. This script must be
# expanded to support encryption, retention, and verification.

set -euo pipefail

LOGFILE="/var/log/otomasi_audio_compat.log"
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') - [backup] $*" >>"$LOGFILE"; }

usage() {
  cat <<EOF
Usage: $0 create <output.tar.gz>
       $0 list <backupdir>
EOF
}

case "${1:-}" in
  create)
    OUT="$2"
    log "create backup -> $OUT"
    # Placeholder: callers should pass an explicit list of paths to include
    tar -czf "$OUT" /etc/audio-school-system || { log "tar failed"; exit 1; }
    ;;
  list)
    ls -lh "$2"
    ;;
  *)
    usage
    exit 2
    ;;
esac
