# hermes-docker

Hermes Agent with ByteRover memory, fully containerised. Models are served
through LiteLLM, so any mix of local servers (oMLX, vLLM, Ollama, ...) and
cloud providers (OpenAI, OpenRouter, Anthropic, ...) works.

Requires Docker and Rust.

## First start

1. Create `.env` and set the Exa API key. `LLM_MODEL_NAME` is set in
   step 4.

   ```sh
   cp .env.example .env
   ```

2. Start the services without opening a chat (no model is set up yet):

   ```sh
   docker compose up -d --wait
   ```

   The first start pulls the images and builds the ByteRover image, and
   takes a few minutes.

3. Add a model in the LiteLLM dashboard (see below).

4. Set `LLM_MODEL_NAME` in `.env` to that model's public name, then build
   and run:

   ```sh
   cargo build --release
   ./target/release/hermes-docker
   ```

`hermes-docker` starts all services, opens the Hermes chat, and stops the
services on `/exit`. After changing `byterover/`, run
`docker compose build`.

Optional alias:

```sh
alias hermes="$PWD/target/release/hermes-docker"
```

## Models and the LiteLLM dashboard

Providers, base URLs, model names and API keys are set in the LiteLLM
dashboard, not in `.env`.

1. With the services running, open <http://127.0.0.1:4000/ui>. It listens
   on this machine only.
2. Log in as `admin`. The password is LiteLLM's master key, generated on
   first start:

   ```sh
   cat data/litellm/keys/master.key
   ```

3. Under **Models**, add a model: pick the provider, enter the model id,
   the API key and, for local or OpenAI-compatible servers, the API base.
   A server on this Mac is `http://host.docker.internal:<port>/v1`.
   The public model name you give it is what Hermes asks for.
4. To switch Hermes to another model, set `LLM_MODEL_NAME` in `.env` and
   restart (`/exit`, then start again).

Hermes and ByteRover get the master key automatically. Models added in the
dashboard are saved in LiteLLM's database. `data/litellm/config.yaml`
takes static entries too, but those are read-only in the dashboard.

## Services

- `litellm`: model proxy and dashboard, with its database `litellm-db`
  (Postgres).
- `hermes`: the agent. ByteRover memory runs alongside it in `byterover`.
- `core-sync`, `litellm-db-sync`: write the host snapshots in `data/`.
- `hermes-restore`: one-shot; fills an empty Hermes volume from
  `data/core/`.

## Data

Everything under `data/` is gitignored. Hermes's home and LiteLLM's
database run in Docker volumes (neither can run on a Docker Desktop bind
mount), and the host keeps what is needed to restore them:

- `data/core/`: Hermes's sessions and messages (`state.db`), memories,
  `SOUL.md`, config, cron jobs, skills and plans. Written every 60 s and on
  stop.
- `data/litellm/`: `db.sql`, a dump of LiteLLM's database (models,
  provider keys, settings), written every 60 s and on stop;
  `keys/master.key`, which also encrypts the stored provider keys, so keep
  it with `db.sql`; and `config.yaml`.
- `data/byterover/`: Hermes's long-term memory (ByteRover, local only).
  `tree/` holds the context tree as Markdown; `data/` and `config/` hold the
  daemon's state, provider setup and settings.
- `hermes_wd/`: Hermes's working directory; files it creates land here.

## Moving to another machine

Stop the services (`/exit` or `docker compose stop`) so the last snapshots
are written, then copy the repo with `data/`, `hermes_wd/` and `.env`. On
the new machine, the first start restores Hermes and LiteLLM from `data/`
into fresh volumes.
