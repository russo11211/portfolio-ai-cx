// The Express app. Read it top to bottom: it is the whole request lifecycle.
//
//   raw bytes -> verify signature -> parse JSON -> validate/normalize event
//   -> dedupe by id -> enqueue -> 200 (fast) ... worker processes later
import express from 'express';
import { verifySignature } from './signature.js';
import { getSource, parseJson } from './event.js';
import { createQueue } from './queue.js';
import { createMemoryStore } from './idempotency.js';
import { createLogger } from './logger.js';
import { createEventHandler } from './handlers.js';
import { createMockCrm } from './crm.js';
import { createMockDialer } from './dialer.js';

export function createApp(options = {}) {
  const {
    secret,
    source: sourceName = 'generic',
    logger = createLogger({ level: process.env.LOG_LEVEL ?? 'info' }),
    store = createMemoryStore(),
    crm = createMockCrm(),
    dialer = createMockDialer(),
    handleEvent = createEventHandler({ crm, dialer, logger }),
    bodyLimit = '100kb',
  } = options;

  if (!secret) {
    throw new Error('createApp: a webhook secret is required');
  }
  const source = getSource(sourceName);

  // Step 3: the worker that runs AFTER we have answered the sender.
  const queue = createQueue({
    worker: async (event) => {
      await handleEvent(event);
    },
    onError: (err, event) => {
      // Step 5: a failure in the background must never crash the process.
      logger.error('event.failed', { eventId: event.id, type: event.type, error: err.message });
    },
  });

  const app = express();
  app.disable('x-powered-by');
  app.locals.queue = queue;
  app.locals.store = store;

  // Step 5: health check for load balancers / uptime monitors.
  app.get('/health', (req, res) => {
    res.json({ status: 'ok', queueDepth: queue.depth });
  });

  // Step 1 + 2: express.raw() gives us req.body as a Buffer with the EXACT
  // bytes the sender signed. Do NOT use express.json() here: it would hand
  // us a re-built object and the original bytes would be gone.
  app.post('/webhook', express.raw({ type: '*/*', limit: bodyLimit }), async (req, res, next) => {
    try {
      const rawBody = Buffer.isBuffer(req.body) ? req.body : Buffer.alloc(0);

      // Step 2: authenticate first. An unauthenticated request gets no
      // further information (not even "your JSON is invalid").
      const signature = req.get(source.signatureHeader);
      if (!verifySignature(secret, rawBody, signature)) {
        logger.warn('webhook.rejected', { reason: 'invalid_signature' });
        return res.status(401).json({ error: 'invalid_signature' });
      }

      // Step 1: parse and validate.
      const parsed = parseJson(rawBody);
      if (!parsed.ok) {
        return res.status(400).json({ error: 'invalid_json' });
      }
      const event = source.toEvent(parsed.value, req.headers);
      if (!event) {
        return res.status(400).json({ error: 'invalid_event' });
      }

      logger.info('webhook.received', { eventId: event.id, type: event.type });

      // Step 4: idempotency. A duplicate is a success from the sender's
      // point of view (answer 2xx so it stops retrying), but we do no work.
      const isNew = await store.claim(event.id);
      if (!isNew) {
        logger.info('webhook.duplicate', { eventId: event.id, type: event.type });
        return res.status(200).json({ received: true, duplicate: true });
      }

      // Step 3: acknowledge fast, process later.
      queue.enqueue(event);
      return res.status(200).json({ received: true });
    } catch (err) {
      return next(err);
    }
  });

  // Step 5: JSON 404 for anything else.
  app.use((req, res) => {
    res.status(404).json({ error: 'not_found' });
  });

  // Step 5: central error handler (Express recognises it by the 4 arguments).
  // eslint-disable-next-line no-unused-vars
  app.use((err, req, res, next) => {
    const status = err.status ?? err.statusCode ?? 500;
    if (status >= 500) {
      logger.error('http.error', { error: err.message, path: req.path });
    } else {
      logger.warn('http.client_error', { error: err.type ?? err.message, status, path: req.path });
    }
    const error = status === 413 ? 'payload_too_large' : status >= 500 ? 'internal_error' : 'bad_request';
    res.status(status).json({ error });
  });

  return app;
}
