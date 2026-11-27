#!/bin/sh
# Dumps LiteLLM's database to /backup/db.sql (data/litellm) every
# INTERVAL seconds and once more on SIGTERM. Replaces the file only when
# the dump changed, and atomically.
set -u
umask 077
INTERVAL="${DB_SYNC_INTERVAL:-60}"
stopping=0
trap 'stopping=1' TERM INT

dump() {
  if pg_dump --no-owner --no-privileges -f /backup/.db.sql.tmp; then
    if cmp -s /backup/.db.sql.tmp /backup/db.sql; then
      rm -f /backup/.db.sql.tmp
    else
      mv /backup/.db.sql.tmp /backup/db.sql
    fi
  else
    rm -f /backup/.db.sql.tmp
    echo "litellm-db-sync: dump failed" >&2
  fi
}

echo "litellm-db-sync: dumping every ${INTERVAL}s" >&2
while :; do
  dump
  if [ "$stopping" = 1 ]; then
    echo "litellm-db-sync: final dump written" >&2
    exit 0
  fi
  i=0
  while [ "$stopping" = 0 ] && [ "$i" -lt "$INTERVAL" ]; do
    sleep 1 & wait $!
    i=$((i + 1))
  done
done
