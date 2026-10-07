// Entry point for YOUR server: `npm start`.
// Uses console.log so it works from step 1, before you write the logger in step 5.
// (solution/src/server.js shows the version with the structured logger.)
import { createApp } from './app.js';

const secret = process.env.WEBHOOK_SECRET;
if (!secret) {
  console.error('WEBHOOK_SECRET is not set. Example: export WEBHOOK_SECRET=dev-secret');
  process.exit(1);
}

const port = Number(process.env.PORT ?? 3000);
const source = process.env.WEBHOOK_SOURCE ?? 'generic';
const app = createApp({ secret, source });

const server = app.listen(port, () => {
  console.log(`webhook-lab (starter) listening on http://localhost:${port} - source: ${source}`);
});

// Graceful shutdown: stop accepting connections, let the queue (step 3) drain.
async function shutdown(signal) {
  console.log(`${signal} received, shutting down`);
  server.close();
  await app.locals.queue?.onIdle?.();
  process.exit(0);
}
process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));
