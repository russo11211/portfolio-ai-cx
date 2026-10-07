// YOUR webhook receiver. Fill it in step by step (see README.md).
// Run one step's tests at a time: npm run test:step1, npm run test:step2, ...
import express from 'express';
// Import helpers as you need them, e.g.:
// import { parseJson, getSource } from './event.js';          // step 1
// import { verifySignature } from './signature.js';           // step 2
// import { createQueue } from './queue.js';                   // step 3
// import { createMemoryStore } from './idempotency.js';       // step 4
// import { createLogger } from './logger.js';                 // step 5
// import { createEventHandler } from './handlers.js';         // step 8
// import { createMockCrm } from './crm.js';                   // step 8
// import { createMockDialer } from './dialer.js';             // step 8

/**
 * Options the tests pass in (read them from `options` as each step needs them):
 *   secret       string   shared HMAC secret (required)                    step 2
 *   handleEvent  async fn called with { id, type, data } for each event  step 3
 *   store        { claim(id), release(id) } idempotency store             step 4
 *   logger       { debug, info, warn, error }                             step 5
 *   source       'generic' | 'github'                                     step 6
 *   crm, dialer  mocks used by the default handleEvent                    step 8
 *
 * Tip: use defaults only for things you have already built, e.g.
 *   const { store = createMemoryStore() } = options;   // only after step 4!
 */
export function createApp(options = {}) { // eslint-disable-line no-unused-vars
  const app = express();

  // TODO(step 3): create the queue and expose it as app.locals.queue
  //               (the tests call app.locals.queue.onIdle()).

  // TODO(step 5): GET /health -> 200 { status: 'ok', queueDepth }

  // TODO(step 1): POST /webhook
  //   - use express.raw({ type: '*/*', limit: '100kb' }) so req.body is a Buffer
  //   - parse it with parseJson(); invalid -> 400 { error: 'invalid_json' }
  //   - normalize with getSource('generic').toEvent(); null -> 400 { error: 'invalid_event' }
  //   - answer 200 { received: true }
  // TODO(step 2): BEFORE parsing, verify the signature header -> 401 { error: 'invalid_signature' }
  // TODO(step 3): enqueue the event instead of processing it in the request
  // TODO(step 4): store.claim(event.id); a duplicate -> 200 { received: true, duplicate: true }
  // TODO(step 5): log 'webhook.received' / 'webhook.rejected' / 'webhook.duplicate'
  // TODO(step 6): use getSource(options.source) so the header and toEvent change per sender

  // TODO(step 5): JSON 404 handler, then an error handler (err, req, res, next)
  //               that answers 413 { error: 'payload_too_large' } for big bodies.

  return app;
}
