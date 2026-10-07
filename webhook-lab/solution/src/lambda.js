// Step 7 - the same webhook as a native AWS Lambda handler behind
// API Gateway (HTTP API, payload format 2.0). No Express, no dependencies:
// the zip only needs this folder and a package.json with "type": "module".
//
// Key difference from the Express version: Lambda FREEZES the execution
// environment as soon as the handler returns. Work scheduled "for later"
// (our in-memory queue) would not run. So here we process inline, and
// answer 500 on failure so the sender retries. In production, the usual
// pattern is API Gateway -> SQS (durable queue) -> worker Lambda.
import { verifySignature } from './signature.js';
import { getSource, parseJson } from './event.js';
import { createMemoryStore } from './idempotency.js';
import { createLogger } from './logger.js';
import { createEventHandler } from './handlers.js';
import { createMockCrm } from './crm.js';
import { createMockDialer } from './dialer.js';

export function createLambdaHandler(options = {}) {
  const {
    secret,
    source: sourceName = 'generic',
    logger = createLogger(),
    // NOTE: this Set lives only as long as one warm Lambda container.
    // Production: a DynamoDB table with a conditional put (see README step 7).
    store = createMemoryStore(),
    handleEvent = createEventHandler({ crm: createMockCrm(), dialer: createMockDialer(), logger }),
  } = options;

  if (!secret) {
    throw new Error('createLambdaHandler: a webhook secret is required');
  }
  const source = getSource(sourceName);

  return async function handler(apiEvent) {
    const method = apiEvent.requestContext?.http?.method ?? apiEvent.httpMethod;
    const path = apiEvent.rawPath ?? apiEvent.path ?? '';

    if (method === 'GET' && path.endsWith('/health')) {
      return json(200, { status: 'ok' });
    }
    if (method !== 'POST' || !path.endsWith('/webhook')) {
      return json(404, { error: 'not_found' });
    }

    // HTTP API lowercases header names; the older REST API does not.
    const headers = lowercaseKeys(apiEvent.headers ?? {});
    // API Gateway may base64-encode the body. Decode back to the exact bytes.
    const rawBody = Buffer.from(apiEvent.body ?? '', apiEvent.isBase64Encoded ? 'base64' : 'utf8');

    if (!verifySignature(secret, rawBody, headers[source.signatureHeader])) {
      logger.warn('webhook.rejected', { reason: 'invalid_signature' });
      return json(401, { error: 'invalid_signature' });
    }
    const parsed = parseJson(rawBody);
    if (!parsed.ok) return json(400, { error: 'invalid_json' });
    const event = source.toEvent(parsed.value, headers);
    if (!event) return json(400, { error: 'invalid_event' });

    logger.info('webhook.received', { eventId: event.id, type: event.type });

    if (!(await store.claim(event.id))) {
      logger.info('webhook.duplicate', { eventId: event.id, type: event.type });
      return json(200, { received: true, duplicate: true });
    }

    try {
      await handleEvent(event);
    } catch (err) {
      // Give the id back so the sender's retry is processed, then ask for a retry.
      await store.release(event.id);
      logger.error('event.failed', { eventId: event.id, type: event.type, error: err.message });
      return json(500, { error: 'processing_failed' });
    }
    return json(200, { received: true });
  };
}

// The function AWS calls. Configure the handler as "src/lambda.handler".
// Built once per container (cold start) and reused while the container is warm.
let cached;
export async function handler(apiEvent, context) {
  cached ??= createLambdaHandler({
    secret: process.env.WEBHOOK_SECRET,
    source: process.env.WEBHOOK_SOURCE ?? 'generic',
    logger: createLogger({ level: process.env.LOG_LEVEL ?? 'info' }),
  });
  return cached(apiEvent, context);
}

function json(statusCode, body) {
  return { statusCode, headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) };
}

function lowercaseKeys(obj) {
  return Object.fromEntries(Object.entries(obj).map(([k, v]) => [k.toLowerCase(), v]));
}
