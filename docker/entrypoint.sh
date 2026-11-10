#!/bin/sh
# Container start script.
#
# Docker often creates the mounted data folder owned by root, which a normal
# user could not write to. So we start as root, give the data folder to the
# user PUID:PGID (default 1000:1000, the usual desktop user), and then run
# epub2zim as that user, never as root.
set -e

PUID="${PUID:-1000}"
PGID="${PGID:-1000}"
DATA="${EPUB2ZIM_DATA_DIR:-/data}"

if [ "$(id -u)" = "0" ]; then
  mkdir -p "$DATA"
  chown -R "$PUID:$PGID" "$DATA" 2>/dev/null || echo "note: could not change owner of $DATA"
  exec setpriv --reuid="$PUID" --regid="$PGID" --clear-groups env HOME=/tmp "$@"
fi
exec "$@"
