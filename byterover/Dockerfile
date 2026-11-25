# ByteRover (brv) daemon for Hermes's memory. See docker-compose.yml.
FROM node:22-slim

ARG BRV_VERSION=3.16.1

# The CLI is installed here and copied into the shared `brv-cli` volume
# (/opt/brv) on every start, so Hermes always runs the same brv version
# as this daemon.
RUN npm install --global --prefix /usr/local/lib/brv "byterover-cli@${BRV_VERSION}" \
 && npm cache clean --force \
 && groupadd --gid 10000 brv \
 && useradd --uid 10000 --gid 10000 --home-dir /opt/data/home --no-create-home brv \
 && mkdir -p /opt/brv /opt/data/home \
 && chown brv:brv /opt/brv /opt/data/home

COPY entrypoint.sh keepalive.mjs /usr/local/lib/brv-service/

ENV PATH=/opt/brv/bin:$PATH

USER brv
ENTRYPOINT ["/usr/local/lib/brv-service/entrypoint.sh"]
