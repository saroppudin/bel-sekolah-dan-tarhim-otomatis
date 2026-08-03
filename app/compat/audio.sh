#!/bin/bash
# app/compat/audio.sh
# Compatibility wrapper skeleton for audio probing and simple operations.
# Uses ffprobe/ffmpeg if available. This script should be called by the
# backend compatibility adapter and must validate inputs before calling
# system tools.

set -euo pipefail

LOGFILE="/var/log/otomasi_audio_compat.log"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') - [audio] $*" >>"$LOGFILE"; }

usage() {
  cat <<EOF
Usage: $0 probe <file>
       $0 waveform <file> <out.png>
EOF
}

case "${1:-}" in
  probe)
    FILE="$2"
    log "probe $FILE"
    if ! command -v ffprobe >/dev/null 2>&1; then
      echo "ffprobe not found" >&2
      exit 1
    fi
    ffprobe -v error -show_entries format=duration,size,bit_rate -of json "$FILE"
    ;;
  waveform)
    FILE="$2"; OUT="$3"
    log "waveform $FILE -> $OUT"
    if ! command -v ffmpeg >/dev/null 2>&1; then
      echo "ffmpeg not found" >&2
      exit 1
    fi
    # Simple waveform generation placeholder
    ffmpeg -y -i "$FILE" -filter_complex "aformat=channel_layouts=mono,showwavespic=s=600x120" -frames:v 1 "$OUT"
    ;;
  *)
    usage
    exit 2
    ;;
esac
