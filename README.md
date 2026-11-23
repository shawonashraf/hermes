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

This starts the Hermes container, then opens the Hermes chat. `/exit` stops
the container. The first start pulls the image and takes a few minutes.

- `hermes_wd/`: Hermes's working directory; files it creates land here.

Optional alias:

```sh
alias hermes="$PWD/target/release/hermes-docker"
```
