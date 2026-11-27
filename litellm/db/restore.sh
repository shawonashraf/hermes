#!/bin/sh
# Postgres runs this once, on an empty data volume (first start on a new
# machine): load the last dump that litellm-db-sync wrote to data/litellm.
set -eu
if [ -s /backup/db.sql ]; then
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -q -f /backup/db.sql
  echo "litellm-db: restored from data/litellm/db.sql"
else
  echo "litellm-db: no dump in data/litellm; starting empty"
fi
