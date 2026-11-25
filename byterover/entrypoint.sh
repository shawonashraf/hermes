#!/bin/sh
# Runs the brv daemon in the foreground, keeps it from idling out, and
# points it at the oMLX model. This container joins Hermes's network and
# PID namespaces, so Hermes's brv CLI finds the daemon on 127.0.0.1.
set -eu

SERVICE_DIR=/usr/local/lib/brv-service
PKG=/opt/brv/lib/node_modules/byterover-cli

# Give Hermes this image's CLI (the `brv-cli` volume; /opt/data/.brv-cli there).
find /opt/brv -mindepth 1 -maxdepth 1 -exec rm -rf {} +
cp -a /usr/local/lib/brv/. /opt/brv/

rm -f /run/brv-ready/*

# The CLI must not replace itself (/opt/brv is rebuilt from the image).
# Written before any brv command runs: each one may start a background
# `brv update --autoupdate`, which reads this setting once, at its start.
node -e '
  const fs = require("node:fs");
  const dir = process.env.HOME + "/.local/share/brv";
  const file = dir + "/settings.json";
  let s = {};
  try { s = JSON.parse(fs.readFileSync(file, "utf8")); } catch {}
  s.version ??= "2";
  s.values = { ...s.values, "update.checkForUpdates": false };
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(file, JSON.stringify(s, null, 2));
'

# Same env the brv launcher (bin/run.js) gives a daemon it spawns itself.
BRV_ENV=production node --env-file="$PKG/.env.production" \
  "$PKG/dist/server/infra/daemon/brv-server.js" &
daemon=$!
trap 'kill -TERM "$daemon" 2>/dev/null; wait "$daemon"; exit 0' TERM INT

node "$SERVICE_DIR/keepalive.mjs" /run/brv-ready/connected &

i=0
until [ -f /run/brv-ready/connected ]; do
  i=$((i + 1))
  if [ "$i" -gt 120 ] || ! kill -0 "$daemon" 2>/dev/null; then
    echo "byterover: daemon did not come up" >&2
    exit 1
  fi
  sleep 0.5
done

brv providers connect openai-compatible \
  --base-url "$LLM_BASE_URL" \
  --api-key "$OMLX_API_KEY" \
  --model "$LLM_MODEL_NAME"

touch /run/brv-ready/configured
echo "byterover: ready" >&2

wait "$daemon"
echo "byterover: daemon exited" >&2
exit 1
