# hermes-docker

Requires Docker, Rust, and an OpenAI-compatible model server (oMLX) on
`localhost:2026` serving the model named in `.env`.

1. Create `.env` and set the oMLX key mapping, model name and Exa API key:

   ```sh
   cp .env.example .env
   ```

2. Build and run:

   ```sh
   cargo build --release
   ./target/release/hermes-docker
   ```

This starts the Hermes and ByteRover containers, then opens the Hermes chat.
`/exit` stops both. The first start pulls the Hermes image and builds the
ByteRover image, and takes a few minutes. After changing `byterover/`, run
`docker compose build`.

- `hermes_wd/`: Hermes's working directory; files it creates land here.
- `byterover_data/`: Hermes's long-term memory (ByteRover, local only).
  `tree/` holds the context tree as Markdown; `data/` and `config/` hold the
  daemon's state, provider setup and settings. ByteRover uses the same model
  server and model as Hermes.

Optional alias:

```sh
alias hermes="$PWD/target/release/hermes-docker"
```
