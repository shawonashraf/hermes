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

This starts Hermes and its Hindsight memory server, then opens the Hermes chat.
`/exit` stops both containers. The first start takes a few minutes: it pulls
the images (about 4 GB) and installs the Hindsight plugin into Hermes.

- `hermes_wd/`: Hermes's working directory; files it creates land here.
- `hindsight_data/`: Hindsight's memory database.
- Memory browser: http://localhost:9999 (while running).

Optional alias:

```sh
alias hermes="$PWD/target/release/hermes-docker"
```
