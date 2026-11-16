# hermes-docker

Requires Docker and Rust.

1. Map the API key to the host env var that holds it:

   ```sh
   cp .env.example .env   # edit the variable name if yours differs
   ```

2. Build and run:

   ```sh
   cargo build --release
   ./target/release/hermes-docker
   ```

This starts the container and opens the Hermes chat. `/exit` stops the container.

Optional alias:

```sh
alias hermes="$PWD/target/release/hermes-docker"
```
