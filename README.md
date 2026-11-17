# hermes-docker

Requires Docker and Rust.

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
`/exit` stops both containers.

- `hermes_wd/`: Hermes's working directory; files it creates land here.
- `hindsight_data/`: Hindsight's memory database.
- Memory browser: http://localhost:9999 (while running).

Optional alias:

```sh
alias hermes="$PWD/target/release/hermes-docker"
```
