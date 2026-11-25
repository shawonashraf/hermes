// Holds one client connection open so the brv daemon never reaches its
// built-in 30-minute no-clients shutdown. Writes READY_FILE (argv[2]) once
// connected. If the daemon dies, the entrypoint exits and Docker restarts
// the container.
import { connectToTransport } from '/opt/brv/lib/node_modules/byterover-cli/node_modules/@campfirein/brv-transport-client/dist/index.js';

const READY_FILE = process.argv[2];
const deadline = Date.now() + 60_000;

let client;
for (;;) {
  try {
    ({ client } = await connectToTransport(process.cwd(), { clientType: 'cli' }));
    break;
  } catch (error) {
    if (Date.now() > deadline) {
      console.error(`keepalive: cannot connect to the brv daemon: ${error.message}`);
      process.exit(1);
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}

console.error('keepalive: connected to the brv daemon');
if (READY_FILE) {
  const { writeFileSync } = await import('node:fs');
  writeFileSync(READY_FILE, '');
}

// Keep the event loop alive; the socket alone does that, this is a backstop.
setInterval(() => {}, 1 << 30);
