// Entry point: `npm run start:solution` (or `npm start` for your starter).
import { createApp } from './app.js';
import { createLogger } from './logger.js';

const secret = process.env.WEBHOOK_SECRET;
if (!secret) {
  console.error('WEBHOOK_SECRET is not set. Example: export WEBHOOK_SECRET=dev-secret');
  process.exit(1);
}

const port = Number(process.env.PORT ?? 3000);
const logger = createLogger({ level: process.env.LOG_LEVEL ?? 'info' });
const app = createApp({ secret, source: process.env.WEBHOOK_SOURCE ?? 'generic', logger });

const server = app.listen(port, () => {
  logger.info('server.started', { port, source: process.env.WEBHOOK_SOURCE ?? 'generic' });
});

// Graceful shutdown: stop accepting connections, then let the queue drain.
async function shutdown(signal) {
  logger.info('server.stopping', { signal });
  server.close();
  await app.locals.queue.onIdle();
  logger.info('server.stopped');
  process.exit(0);
}
process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));
